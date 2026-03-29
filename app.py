import os
import traceback
import requests
from flask import Flask, request, redirect, jsonify, Response
from cachetools import TTLCache
import yt_dlp

app = Flask(__name__)

url_cache = TTLCache(maxsize=1000, ttl=7200)
SECRET_KEY = os.environ.get("APP_SECRET_KEY", "LumiaWP81-An")

# NẠP COOKIE CHỐNG GIỚI HẠN ĐỘ TUỔI
cookie_data = os.environ.get('COOKIE_DATA')
if cookie_data:
    with open('cookies.txt', 'w', encoding='utf-8') as f:
        f.write(cookie_data)

@app.route('/')
def home():
    return "🚀 API Railway (Bản Kép Nồi Đồng Cối Đá - Mặt Nạ 4 Lớp) đang hoạt động!"

def get_audio_url(video_id):
    if video_id in url_cache:
        return url_cache[video_id]

    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        'format': '140/bestaudio[ext=m4a]/18/best[ext=mp4]',
        
        # CHỐT GIỮ MẶT NẠ 4 LỚP: Đảm bảo khả năng vượt rào mạnh mẽ nhất
        'extractor_args': {'youtube': {'client': ['android', 'ios', 'tv', 'web']}},
        
        'youtube_include_dash_manifest': False,
        'youtube_include_hls_manifest': False,
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
            if audio_url:
                url_cache[video_id] = audio_url
            return audio_url
    except Exception as e:
        raise e

# ==================================================
# CỔNG 1: NGHE NHẠC (Chuyển hướng trực tiếp để Lumia tự xử lý)
# ==================================================
@app.route('/api/play')
def play_audio():
    client_key = request.args.get("key")
    if client_key != SECRET_KEY:
        return jsonify({"error": "Unauthorized!"}), 403

    video_id = request.args.get('v')
    if not video_id:
        return "Lỗi: Thiếu ID bài hát", 400

    try:
        audio_url = get_audio_url(video_id)
        if not audio_url:
            return "Không tìm thấy định dạng âm thanh.", 500
            
        return redirect(audio_url)
    except Exception as e:
        traceback.print_exc()
        return f"🚨 Lỗi: {str(e)}", 500

# ==================================================
# CỔNG 2: TẢI OFFLINE (Sử dụng Proxy bơm dữ liệu lớn)
# ==================================================
@app.route('/api/download')
def download_audio():
    client_key = request.args.get("key")
    if client_key != SECRET_KEY:
        return jsonify({"error": "Unauthorized!"}), 403

    video_id = request.args.get('v')
    if not video_id:
        return "Lỗi: Thiếu ID bài hát", 400

    try:
        audio_url = get_audio_url(video_id)
        if not audio_url:
            return "Không tìm thấy định dạng âm thanh.", 500

        r = requests.get(audio_url, stream=True)
        if r.status_code in [403, 401]:
            if video_id in url_cache: del url_cache[video_id]
            return "Bị khóa IP", 403

        # Ép bơm dữ liệu cục to 1MB để tải siêu nhanh
        resp = Response(r.iter_content(chunk_size=1048576), status=r.status_code)
        
        for k, v in r.headers.items():
            if k.lower() not in ['content-encoding', 'transfer-encoding', 'connection']:
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
