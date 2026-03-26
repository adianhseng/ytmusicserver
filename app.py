import os
import traceback
import requests
from flask import Flask, request, jsonify, Response
from cachetools import TTLCache
import yt_dlp

app = Flask(__name__)

url_cache = TTLCache(maxsize=1000, ttl=7200)
SECRET_KEY = os.environ.get("APP_SECRET_KEY", "LumiaWP81-An")

cookie_data = os.environ.get('COOKIE_DATA')
if cookie_data:
    with open('cookies.txt', 'w', encoding='utf-8') as f:
        f.write(cookie_data)

@app.route('/')
def home():
    return "🚀 API Railway (Bản Giải Phóng YT-DLP) đang hoạt động!"

@app.route('/api/play')
def play_audio():
    client_key = request.args.get("key")
    if client_key != SECRET_KEY:
        return jsonify({"error": "Unauthorized!"}), 403

    video_id = request.args.get('v')
    if not video_id:
        return "Lỗi: Thiếu ID bài hát", 400

    audio_url = url_cache.get(video_id)

    if not audio_url:
        youtube_url = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = {
            # CHỈ ĐỊNH ĐƠN GIẢN: Ưu tiên m4a, nếu không có lấy audio xịn nhất, cuối cùng lấy bừa file tốt nhất
            'format': '140/bestaudio[ext=m4a]/bestaudio/best',
            
            # TUYỆT ĐỐI XÓA EXTRACTOR_ARGS VÀ MANIFEST: 
            # Thả rông cho yt-dlp tự dùng bộ não của nó để luồn lách qua anti-bot của YouTube
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True
        }
        
        if os.path.exists('cookies.txt'):
            ydl_opts['cookiefile'] = 'cookies.txt'

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(youtube_url, download=False)
                audio_url = info_dict.get('url')
                if not audio_url:
                    return "Không tìm thấy định dạng âm thanh.", 500
                url_cache[video_id] = audio_url
        except Exception as e:
            traceback.print_exc()
            return f"🚨 Lỗi yt-dlp: {str(e)}", 500

    try:
        req_headers = {}
        if "Range" in request.headers:
            req_headers["Range"] = request.headers["Range"]
            
        r = requests.get(audio_url, headers=req_headers, stream=True)
        
        if r.status_code in [403, 401]:
            if video_id in url_cache:
                del url_cache[video_id]
            return "🚨 Bị khóa IP bởi Vevo. Đã xóa cache!", 403

        def generate():
            for chunk in r.iter_content(chunk_size=65536):
                if chunk:
                    yield chunk

        resp = Response(generate(), status=r.status_code)
        
        excluded_headers = ['content-encoding', 'transfer-encoding', 'connection']
        for k, v in r.headers.items():
            if k.lower() not in excluded_headers:
                resp.headers[k] = v
                
        if 'Content-Length' in r.headers:
            resp.headers['Content-Length'] = r.headers['Content-Length']
            
        resp.direct_passthrough = True
        return resp

    except Exception as e:
        traceback.print_exc()
        return f"🚨 Lỗi Stream: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
