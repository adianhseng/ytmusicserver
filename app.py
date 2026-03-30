import os
import traceback
from flask import Flask, request, jsonify, send_file
from cachetools import TTLCache
import yt_dlp

app = Flask(__name__)

# TỐI ƯU 1: CACHE CHỐNG TRÀN RAM
url_cache = TTLCache(maxsize=1000, ttl=7200)

# TỐI ƯU 2: KHÓA BẢO MẬT
SECRET_KEY = os.environ.get("APP_SECRET_KEY", "LumiaWP81-An")

# TẠO THƯ MỤC LƯU NHẠC TẠM THỜI TRÊN SERVER 
DOWNLOAD_DIR = "/tmp/ytmusic"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# NẠP COOKIE CHỐNG GIỚI HẠN ĐỘ TUỔI
cookie_data = os.environ.get('COOKIE_DATA')
if cookie_data:
    with open('cookies.txt', 'w', encoding='utf-8') as f:
        f.write(cookie_data)

@app.route('/')
def home():
    return "🚀 API Railway (Bản Tối Thượng: Nghe & Tải đều dùng Server Cache) đang hoạt động!"

# ==================================================
# ĐỘNG CƠ CỐT LÕI: TẢI FILE VỀ Ổ CỨNG SERVER
# ==================================================
def get_cached_file(video_id):
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.m4a")
    
    # Nếu file đã được tải trước đó thì lấy dùng luôn (load tức thì)
    if not os.path.exists(file_path):
        youtube_url = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = {
            'format': '140/bestaudio[ext=m4a]/bestaudio/best',
            'extractor_args': {'youtube': {'client': ['android', 'ios', 'tv', 'web']}},
            'outtmpl': file_path, # Ra lệnh lưu file vào ổ cứng Server
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True
        }
        if os.path.exists('cookies.txt'):
            ydl_opts['cookiefile'] = 'cookies.txt'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
            
    return file_path

# ==================================================
# CỔNG 1: NGHE NHẠC (Phát file tĩnh từ Server)
# ==================================================
@app.route('/api/play')
def play_audio():
    client_key = request.args.get("key")
    if client_key != SECRET_KEY:
        return jsonify({"error": "Unauthorized!"}), 403

    video_id = request.args.get('v')
    if not video_id: return "Lỗi ID bài hát", 400

    try:
        file_path = get_cached_file(video_id)
        # Bắn thẳng file nguyên khối. send_file tự động xử lý tua nhạc cực mượt.
        return send_file(file_path, mimetype="audio/mp4")
    except Exception as e:
        traceback.print_exc()
        return f"🚨 Lỗi Play: {str(e)}", 500

# ==================================================
# CỔNG 2: TẢI OFFLINE (Bơm max tốc độ về máy)
# ==================================================
@app.route('/api/download')
def download_audio():
    client_key = request.args.get("key")
    if client_key != SECRET_KEY:
        return jsonify({"error": "Unauthorized!"}), 403

    video_id = request.args.get('v')
    if not video_id: return "Lỗi ID bài hát", 400

    try:
        file_path = get_cached_file(video_id)
        # as_attachment=True sẽ ép trình duyệt/app phải tải file xuống thay vì phát
        return send_file(file_path, mimetype="audio/mp4", as_attachment=True, download_name=f"{video_id}.m4a")
    except Exception as e:
        traceback.print_exc()
        return f"🚨 Lỗi Download: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
