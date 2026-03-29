import os
import traceback
import requests
from flask import Flask, request, redirect, jsonify, Response
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
    return "🚀 API Railway (Bản Kép Hoàn Hảo - Đã Khóa Chặn M3U8) đang hoạt động!"

def get_audio_url(video_id):
    if video_id in url_cache:
        return url_cache[video_id]

    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
    
    ydl_opts = {
        # BÍ KÍP CHỐT HẠ: Ép yt-dlp chỉ lấy link media nguyên khối (http/https), tuyệt đối không lấy file chữ m3u8
        'format': 'bestaudio[ext=m4a][protocol^=http]/140/18/best[ext=mp4][protocol^=http]/best[protocol^=http]',
        
        'extractor_args': {'youtube': {'client': ['android', 'ios', 'tv', 'web']}},
        
        # Bật DASH để lấy được file M4A bị giấu của NCS, nhưng TẮT HLS để chặn m3u8
        'youtube_include_dash_manifest': True,
        'youtube_include_hls_manifest': False,
        
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True
    }
    
    if os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(youtube_url, download=False)
        audio_url = info_dict.get('url')
        if audio_url:
            url_cache[video_id] = audio_url
        return audio_url

# ==================================================
# CỔNG 1: NGHE NHẠC (Redirect lấy thẳng file m4a/mp4 xịn)
# ==================================================
@app.route('/api/play')
def play_audio():
    if request.args.get("key") != SECRET_KEY:
        return jsonify({"error": "Unauthorized!"}), 403
    
    video_id = request.args.get('v')
    if not video_id: return "Lỗi ID", 400

    try:
        url = get_audio_url(video_id)
        if not url: return "Lỗi không tìm thấy link", 500
        return redirect(url)
    except Exception as e:
        traceback.print_exc()
        return f"🚨 Lỗi yt-dlp: {str(e)}", 500

# ==================================================
# CỔNG 2: TẢI OFFLINE (Bơm Proxy 1MB tốc độ cao)
# ==================================================
@app.route('/api/download')
def download_audio():
    if request.args.get("key") != SECRET_KEY:
        return jsonify({"error": "Unauthorized!"}), 403

    video_id = request.args.get('v')
    if not video_id: return "Lỗi ID", 400

    try:
        audio_url = get_audio_url(video_id)
        if not audio_url: return "Lỗi không tìm thấy link", 500

        r = requests.get(audio_url, stream=True)
        if r.status_code in [403, 401]:
            if video_id in url_cache: del url_cache[video_id]
            return "Bị khóa IP", 403

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
        return f"Lỗi Stream: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
