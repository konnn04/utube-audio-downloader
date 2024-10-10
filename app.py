from app import app
from flask import Flask, request, jsonify
import yt_dlp
import os
import ffmpeg
import json
import random

@app.route('/')
def hello_world():
    return 'Hello, World!'

STATIC_DIR = 'app/static'
MP3_DIR = os.path.join(STATIC_DIR, 'mp3')
THUMBNAIL_DIR = os.path.join(STATIC_DIR, 'thumbnail')
INFO_DIR = os.path.join(STATIC_DIR, 'info')

os.makedirs(MP3_DIR, exist_ok=True)
os.makedirs(THUMBNAIL_DIR, exist_ok=True)
os.makedirs(INFO_DIR, exist_ok=True)

@app.route('/audio', methods=['GET'])
def download_audio():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'URL is required'}), 400

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(MP3_DIR, '%(id)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'writethumbnail': True,
        'writeinfojson': True,
        'noplaylist': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        video_id = info_dict.get('id')
        mp3_path = os.path.join(MP3_DIR, f'{video_id}.mp3')
        info_path = os.path.join(INFO_DIR, f'{video_id}.json')
        if os.path.exists(mp3_path) and os.path.exists(info_path):
            with open(info_path, 'r') as f:
                metadata = json.load(f)
            return jsonify(metadata)

        ydl.download([url])

        # Move thumbnail to respective directory
        thumbnail_path = os.path.join(MP3_DIR, f'{video_id}.jpg')
        if os.path.exists(thumbnail_path):
            os.rename(thumbnail_path, os.path.join(THUMBNAIL_DIR, f'{video_id}.jpg'))
    
        metadata = {
            'id': video_id,
            'thumbnail': f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg',
            'title': info_dict.get('title'),
            'duration': info_dict.get('duration'),
            'uploader': info_dict.get('uploader'),
            'mp3_url': f'/static/mp3/{video_id}.mp3'
        }
        with open(os.path.join(INFO_DIR, f'{video_id}.json'), 'w') as f:
            json.dump(metadata, f)

    return jsonify(metadata)

@app.route('/list', methods=['GET'])
def list_audio():
    q = request.args.get('q')
    if q:
        q = int(q)
    else:
        q = 10

    files = os.listdir(INFO_DIR)
    i_files = [f for f in files if f.endswith('.json')]
    audio_list = []

    for file in i_files:
        with open(os.path.join(INFO_DIR, file), 'r') as f:
            metadata = json.load(f)
            audio_list.append(metadata)

    if len(audio_list) > q:
        audio_list = random.sample(audio_list, q)
    return jsonify(audio_list)

@app.route('/search', methods=['GET'])
def search_videos():

    query = request.args.get('q')
    if not query:
        return jsonify({'error': 'Query is required'}), 400

    ydl_opts = {
        'default_search': 'ytsearch10',  # Search for up to 15 results
        'quiet': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        search_results = ydl.extract_info(query, download=False)['entries']

    results = []
    for item in search_results:
        result = {
            'id_video': item['id'],
            'title': item['title'],
            'uploader': item['uploader'],
            'thumbnail': item['thumbnail'],
            'duration': item['duration']
        }
        results.append(result)

    return jsonify(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)