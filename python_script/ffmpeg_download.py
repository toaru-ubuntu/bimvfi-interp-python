import os
import zipfile
import urllib.request
import platform
import shutil

def info(msg, queue=None):
    """キューがあればqueue.put、なければprintする共通メッセージ関数"""
    if queue is not None:
        queue.put(msg + "\n")
    else:
        print(msg)

def download_ffmpeg_windows(ffmpeg_dest_dir="ffmpeg_bin", queue=None, lang="en"):
    ffmpeg_exe = os.path.join(ffmpeg_dest_dir, "ffmpeg.exe")
    ffprobe_exe = os.path.join(ffmpeg_dest_dir, "ffprobe.exe")

    # すでに ffmpeg.exe と ffprobe.exe が両方あるか確認
    if os.path.exists(ffmpeg_exe) and os.path.exists(ffprobe_exe):
        if lang == "ja":
            info("既に ffmpeg および ffprobe が存在しています。\nダウンロードはスキップされました。", queue)
        elif lang == "en":
            info("ffmpeg and ffprobe already exist.\nDownload skipped.", queue)
        return

    system = platform.system().lower()
    if system == "linux":
        if lang == "ja":
            info("Linuxではffmpegの自動ダウンロードは行いません。", queue)
        elif lang == "en":
            info("Automatic download of ffmpeg is not supported on Linux.", queue)
        return

    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    zip_path = os.path.join(ffmpeg_dest_dir, "ffmpeg.zip")

    os.makedirs(ffmpeg_dest_dir, exist_ok=True)
    if lang == "ja":
        info("ffmpeg をダウンロードしています...", queue)
    elif lang == "en":
        info("Downloading ffmpeg...", queue)
    try:
        urllib.request.urlretrieve(url, zip_path)
    except Exception as e:
        if lang == "ja":
            info(f"[ERROR] ffmpeg のダウンロード中にエラーが発生しました。: {e}", queue)
        elif lang == "en":
            info(f"[ERROR] An error occurred while downloading ffmpeg: {e}", queue)
        return

    if lang == "ja":
        info("展開中...", queue)
    elif lang == "en":
        info("Extracting...", queue)
        
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(ffmpeg_dest_dir)

    # ffmpeg.exe の場所を探して移動
    ffmpeg_found, ffprobe_found = False, False
    for root, dirs, files in os.walk(ffmpeg_dest_dir):
        if "ffmpeg.exe" in files:
            shutil.move(os.path.join(root, "ffmpeg.exe"), ffmpeg_exe)
            ffmpeg_found = True
        if "ffprobe.exe" in files:
            shutil.move(os.path.join(root, "ffprobe.exe"), ffprobe_exe)
            ffprobe_found = True

    os.remove(zip_path)

    if ffmpeg_found and ffprobe_found:
        if lang == "ja":
            info("ffmpeg のセットアップが完了しました。", queue)
        elif lang == "en":    
            info("ffmpeg setup is complete.", queue)
    else:
        if lang == "ja":
            info("[ERROR] ffmpeg または ffprobe のセットアップに失敗しました。: {e}", queue)
        elif lang == "en":    
            info("[ERROR] Failed to set up ffmpeg or ffprobe: {e}", queue)

