import os
import traceback
from flask import Flask, request, jsonify, send_file
import yt_dlp

app = Flask(__name__)

# KHÓA BẢO MẬT
SECRET_KEY = os.environ.get("APP_SECRET_KEY", "LumiaWP81-An")

# THƯ MỤC Ổ CỨNG ẢO ĐỂ SERVER TẢI NHẠC VỀ TRƯỚC
DOWNLOAD_DIR = "/tmp/ytmusic"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

@app.route('/')
def home():
    return "🚀 API Railway (Bản Tối Thượng: Nghe & Tải đều dùng Server Cache - Dựa trên app 7) đang hoạt động!"

# ==================================================
# ĐỘNG CƠ CỐT LÕI: TẢI FILE VỀ Ổ CỨNG SERVER (Bằng mạng Gigabit)
# ==================================================
def get_cached_file(video_id):
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.m4a")
    
    # Nếu Server chưa có bài này, ép Server tải về ổ cứng cực nhanh bằng yt-dlp
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
        # Chỉ dùng cookie nếu file txt đã được tạo sẵn
        if os.path.exists('cookies.txt'):
            ydl_opts['cookiefile'] = 'cookies.txt'

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([youtube_url])
        except Exception as e:
            raise e
            
    return file_path

# ==================================================
# CỔNG 1: NGHE NHẠC (Phát trực tiếp từ ổ cứng Server)
# ==================================================
@app.route('/api/play')
def play_audio():
    client_key = request.args.get("key")
    if client_key != SECRET_KEY:
        return jsonify({"error": "Unauthorized! Đi chỗ khác chơi!"}), 403

    video_id = request.args.get('v')
    if not video_id: return "Lỗi ID bài hát", 400

    try:
        # Tải file về máy chủ trước (nếu chưa có)
        file_path = get_cached_file(video_id)
        
        # Bắn thẳng file nguyên khối về Lumia. send_file hỗ trợ tua nhạc (seek) cực mượt.
        return send_file(file_path, mimetype="audio/mp4")
    except Exception as e:
        traceback.print_exc()
        return f"🚨 Lỗi Play: {str(e)}", 500

# ==================================================
# CỔNG 2: TẢI OFFLINE (Bắn file cho Lumia lưu với tốc độ tối đa)
# ==================================================
@app.route('/api/download')
def download_audio():
    client_key = request.args.get("key")
    if client_key != SECRET_KEY:
        return jsonify({"error": "Unauthorized! Đi chỗ khác chơi!"}), 403

    video_id = request.args.get('v')
    if not video_id: return "Lỗi ID bài hát", 400

    try:
        # Tải file về máy chủ trước (nếu chưa có)
        file_path = get_cached_file(video_id)
        
        # as_attachment=True sẽ ép trình duyệt/app phải tải file xuống máy thay vì phát tiếng
        return send_file(file_path, mimetype="audio/mp4", as_attachment=True, download_name=f"{video_id}.m4a")
    except Exception as e:
        traceback.print_exc()
        return f"🚨 Lỗi Download: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
