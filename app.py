import os
import traceback
import requests
# ĐÃ BỔ SUNG THÊM 'send_file' ĐỂ GỬI FILE TỪ SERVER VỀ ĐIỆN THOẠI
from flask import Flask, request, redirect, jsonify, Response, send_file
from cachetools import TTLCache
import yt_dlp

app = Flask(__name__)

# TỐI ƯU 1: CACHE CHỐNG TRÀN RAM
url_cache = TTLCache(maxsize=1000, ttl=7200)

# TỐI ƯU 2: KHÓA BẢO MẬT
SECRET_KEY = os.environ.get("APP_SECRET_KEY", "LumiaWP81-An")

# TẠO THƯ MỤC LƯU NHẠC TẠM THỜI TRÊN SERVER ĐỂ ÉP TỐC ĐỘ TẢI
DOWNLOAD_DIR = "/tmp/ytmusic"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# NẠP LẠI COOKIE (Do file 11 bị thiếu, nạp lại để chống lỗi giới hạn độ tuổi)
cookie_data = os.environ.get('COOKIE_DATA')
if cookie_data:
    with open('cookies.txt', 'w', encoding='utf-8') as f:
        f.write(cookie_data)

@app.route('/')
def home():
    return "🚀 API Railway (Nghe Proxy - Tải Server Cache - Dựa trên app 11) đang hoạt động!"

# ==================================================
# HÀM LẤY LINK TỪ YT-DLP (Giữ nguyên cấu hình app 11 của bạn)
# ==================================================
def get_audio_url(video_id):
    if video_id in url_cache:
        return url_cache[video_id]

    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        'format': '140/bestaudio[ext=m4a]/bestaudio/best',
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
# BỘ ĐỘNG CƠ PROXY STREAMING 64KB (Chỉ dành để Nghe nhạc)
# ==================================================
def proxy_stream(audio_url, video_id):
    try:
        req_headers = {}
        # Hỗ trợ truyền Range cực kỳ quan trọng để WP8.1 có thể tua nhạc (seek)
        if "Range" in request.headers:
            req_headers["Range"] = request.headers["Range"]
            
        r = requests.get(audio_url, headers=req_headers, stream=True)
        if r.status_code in [403, 401]:
            if video_id in url_cache: del url_cache[video_id]
            return "Bị khóa IP", 403

        # Dùng ống bơm 64KB chảy liên tục
        def generate():
            for chunk in r.iter_content(chunk_size=65536):
                if chunk:
                    yield chunk

        resp = Response(generate(), status=r.status_code)
        
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

# ==================================================
# CỔNG 1: NGHE NHẠC (Giữ nguyên proxy_stream của app 11)
# ==================================================
@app.route('/api/play')
def play_audio():
    client_key = request.args.get("key")
    if client_key != SECRET_KEY:
        return jsonify({"error": "Unauthorized! Đi chỗ khác chơi!"}), 403

    video_id = request.args.get('v')
    if not video_id: return "Lỗi: Thiếu ID bài hát", 400

    try:
        audio_url = get_audio_url(video_id)
        if not audio_url: return "Không tìm thấy định dạng âm thanh.", 500
        # Gọi động cơ Proxy
        return proxy_stream(audio_url, video_id)
    except Exception as e:
        traceback.print_exc()
        return f"🚨 Lỗi: {str(e)}", 500

# ==================================================
# CỔNG 2: TẢI OFFLINE (Đã thay bằng cơ chế Tải Server Cache)
# ==================================================
@app.route('/api/download')
def download_audio():
    client_key = request.args.get("key")
    if client_key != SECRET_KEY:
        return jsonify({"error": "Unauthorized! Đi chỗ khác chơi!"}), 403

    video_id = request.args.get('v')
    if not video_id: return "Lỗi: Thiếu ID bài hát", 400

    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.m4a")

    # 1. Nếu Server chưa tải bài này, dùng yt-dlp kéo về ổ cứng của Railway cực nhanh
    if not os.path.exists(file_path):
        youtube_url = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = {
            'format': '140/bestaudio[ext=m4a]/bestaudio/best',
            'extractor_args': {'youtube': {'client': ['android', 'ios', 'tv', 'web']}},
            'outtmpl': file_path,  # Ra lệnh lưu file vào ổ cứng Server
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True
        }
        if os.path.exists('cookies.txt'):
            ydl_opts['cookiefile'] = 'cookies.txt'

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([youtube_url])
        except Exception as e:
            traceback.print_exc()
            return f"🚨 Lỗi tải Server: {str(e)}", 500

    # 2. Gửi nguyên khối file từ ổ cứng Server về Lumia (Mở khóa toàn bộ băng thông)
    try:
        return send_file(file_path, mimetype="audio/mp4")
    except Exception as e:
        traceback.print_exc()
        return f"🚨 Lỗi gửi file: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
