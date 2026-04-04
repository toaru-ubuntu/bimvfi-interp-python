import os
import subprocess
import threading
import time
from fractions import Fraction

def info(msg, queue=None):
    """キューがあればqueue.put、なければprintする共通メッセージ関数"""
    if queue is not None:
        queue.put(msg + "\n")
    else:
        print(msg)

def file_and_directory_check(material_folder, filename_path, jpg_folder, queue=None, lang="en"):
    os.makedirs(jpg_folder, exist_ok=True)
    file_list = [entry.name for entry in os.scandir(material_folder) if entry.is_file()]
    if not file_list:
        if lang == "ja":
            info("[ERROR] material フォルダにファイルがありません。", queue)
        elif lang == "en":
            info("[ERROR] No files found in the material folder.", queue)
        return None
    filename = file_list[0]
    with open(filename_path, "w", encoding="utf-8") as f:
        f.write(str(filename) + "\n")
    return filename

def get_video_info(ffprobe_path, video_path, temp_folder, queue=None, lang="en"):
    """動画の長さ（秒）とフレームレートを取得"""
    duration_cmd = [
        ffprobe_path, "-i", video_path, "-show_entries",
        "format=duration", "-v", "quiet", "-of", "csv=p=0"
    ]
    duration_result = subprocess.run(duration_cmd, capture_output=True, text=True, encoding="utf-8")
    duration = float(duration_result.stdout.strip())  # 秒単位

    frate_cmd = [
        ffprobe_path, "-i", video_path, "-show_entries",
        "stream=avg_frame_rate", "-v", "quiet", "-of", "csv=p=0"
    ]
    frate_result = subprocess.run(frate_cmd, capture_output=True, text=True, encoding="utf-8")
    frate = frate_result.stdout.strip()
    frate_path = os.path.join(temp_folder, "frate.txt")
    with open(frate_path, "w", encoding="utf-8") as f:
        f.write(frate + "\n")
    with open(frate_path, "r", encoding="utf-8") as f:
        frate = f.readline().strip()
    Frate = round(float(Fraction(frate)), 3)
    with open(frate_path, "w", encoding="utf-8") as f:
        f.write(str(Frate) + "\n")
    return duration, Frate

def run_ffmpeg(ffmpeg_path, video_path, Frate, jpg_folder):
    cmd = [
        ffmpeg_path, "-i", video_path,
        "-pix_fmt", "yuvj420p",
        "-q:v", "5",
        "-r", str(Frate),
        os.path.join(jpg_folder, "%08d.jpg")
    ]
    ffmpeg_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ffmpeg_process.wait()

def monitor_progress(jpg_folder, total_frames, thread1, queue=None, lang="en"):
    if lang == "ja":
        info("画像ファイルに変換中・・・。", queue)
    elif lang == "en":
        info("Converting to image files...", queue)
    prev_file_count = -1
    start_time = time.time()
    while thread1.is_alive():
        file_count = len([entry.name for entry in os.scandir(jpg_folder) if entry.is_file()])
        if int(file_count) != prev_file_count:
            elapsed = time.time() - start_time
            fps = file_count / elapsed if elapsed > 0 else 0
            if lang == "ja":
                info(f"[PROGRESS] {file_count} / {total_frames} (avg: {fps:.2f} fps)", queue)
            elif lang == "en":
                info(f"[PROGRESS] {file_count} / {total_frames} (avg: {fps:.2f} fps)", queue)
            prev_file_count = int(file_count)
        time.sleep(0.5)

def convert_video_to_images(
    ffmpeg_path, ffprobe_path, temp_folder, jpg_folder,
    material_folder, filename_path, queue=None, lang="en"
):
    filename = file_and_directory_check(material_folder, filename_path, jpg_folder, queue, lang)
    if filename is None:
        return
    video_path = os.path.join(material_folder, filename)
    if lang == "ja":
        info(f"ファイル名: {filename}", queue)
    elif lang == "en":
        info(f"File name: {filename}", queue)
    duration, Frate = get_video_info(ffprobe_path, video_path, temp_folder, queue, lang)
    total_frames = int(round(duration * Frate, 0))

    thread1 = threading.Thread(target=run_ffmpeg, args=(ffmpeg_path, video_path, Frate, jpg_folder))
    thread2 = threading.Thread(target=monitor_progress, args=(jpg_folder, total_frames, thread1, queue, lang))

    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()

    time.sleep(0.5)
    file_count = len([entry.name for entry in os.scandir(jpg_folder) if entry.is_file()])
    
    #if file_count != total_frames:
        #if lang == "ja":
            #info(f"[ERROR] 期待されたフレーム数 {total_frames} に対して、生成された画像数は {file_count} でした。", queue)
        #elif lang == "en":
            #info(f"[ERROR] Number of generated images ({file_count}) did not match the expected frame count ({total_frames}).", queue)
        #raise RuntimeError("Frame conversion failed.")

    file_count_path = os.path.join(temp_folder, "file_count.txt")
    with open(file_count_path, "w", encoding="utf-8") as f:
        f.write(str(file_count) + "\n")
    if lang == "ja":
        info("変換終了！", queue)
    elif lang == "en":
        info("Conversion finished!", queue)
    info(f"[PROGRESS] {file_count} / {total_frames}", queue)

