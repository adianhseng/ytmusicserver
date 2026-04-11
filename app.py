import os
import re
import traceback
import time
from flask import Flask, request, jsonify, send_file
import yt_dlp

app = Flask(__name__)

# KHÓA BẢO MẬT
SECRET_KEY = os.environ.get("APP_SECRET_KEY", "LumiaWP81-An")

# THƯ MỤC Ổ CỨNG ẢO
DOWNLOAD_DIR = "/tmp/ytmusic"
MAX_CACHE_FILES = 50 # Giới hạn lưu tối đa 50 bài hát (Khoảng 150MB) để không bao giờ bị nổ ổ cứng

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

def cleanup_cache():
    """ROBOT DỌN RÁC: Xóa các file cũ nhất nếu vượt quá giới hạn MAX_CACHE_FILES"""
    try:
        files = [os.path.join(DOWNLOAD_DIR, f) for f in os.listdir(DOWNLOAD_DIR) if f.endswith('.m4a')]
        if len(files) > MAX_CACHE_FILES:
            # Sắp xếp file theo thời gian (cũ nhất đứng trước)
            files.sort(key=os.path.getmtime)
            # Xóa bớt các file cũ cho đến khi đạt mức an toàn
            files_to_delete = files[:-MAX_CACHE_FILES]
            for f in files_to_delete:
                os.remove(f)
    except Exception:
        pass # Lơ đi nếu có lỗi để không làm gián đoạn việc phát nhạc

def is_valid_video_id(video_id):
    """KHIÊN BẢO MẬT: Đảm bảo ID chỉ có 11 ký tự chuẩn của YouTube, chặn hacker truyền mã độc"""
    return bool(re.match(r'^[a-zA-Z0-9_-]{11}$', video_id))

@app.route('/')
def home():
    return "🚀 API Railway (Bản Public Tối Thượng: Có Auto-Clean & Security) đang hoạt động!"

# ==================================================
# ĐỘNG CƠ CỐT LÕI
# ==================================================
def get_cached_file(video_id):
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.m4a")
    
    if not os.path.exists(file_path):
        # Dọn rác trước khi tải bài mới về
        cleanup_cache() 
        
        youtube_url = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = {
            'format': '140', # Chỉ để 140 là đủ cho Lumia, tránh tải nhầm file mp4 nặng
            'extractor_args': {'youtube': {'client': ['android', 'ios', 'tv', 'web']}},
            'outtmpl': file_path,
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
            raise e
            
    return file_path

# ==================================================
# CỔNG 1: NGHE NHẠC
# ==================================================
@app.route('/api/play')
def play_audio():
    if request.args.get("key") != SECRET_KEY:
        return jsonify({"error": "Unauthorized! Đi chỗ khác chơi!"}), 403

    video_id = request.args.get('v')
    
    # Bật khiên bảo vệ
    if not video_id or not is_valid_video_id(video_id): 
        return "Lỗi: ID bài hát không hợp lệ hoặc chứa mã độc", 400

    try:
        file_path = get_cached_file(video_id)
        return send_file(file_path, mimetype="audio/mp4")
    except Exception as e:
        traceback.print_exc()
        return f"🚨 Lỗi Play: {str(e)}", 500

# ==================================================
# CỔNG 2: TẢI OFFLINE
# ==================================================
@app.route('/api/download')
def download_audio():
    if request.args.get("key") != SECRET_KEY:
        return jsonify({"error": "Unauthorized! Đi chỗ khác chơi!"}), 403

    video_id = request.args.get('v')
    
    # Bật khiên bảo vệ
    if not video_id or not is_valid_video_id(video_id): 
        return "Lỗi: ID bài hát không hợp lệ hoặc chứa mã độc", 400

    try:
        file_path = get_cached_file(video_id)
        return send_file(file_path, mimetype="audio/mp4", as_attachment=True, download_name=f"{video_id}.m4a")
    except Exception as e:
        traceback.print_exc()
        return f"🚨 Lỗi Download: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
