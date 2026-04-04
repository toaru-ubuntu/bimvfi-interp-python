import os
import shutil
import subprocess
from multiprocessing import Pool
import threading
import time
import platform

def info(msg, queue=None):
    if queue is not None:
        queue.put(msg + "\n")
    else:
        print(msg)

def convert_image(args):
    ffmpeg_path, final_jpg, output_jpg, filename, lang = args
    input_path = os.path.join(final_jpg, filename)
    output_path = os.path.join(output_jpg, filename)
    cmd = [
        ffmpeg_path, "-nostdin",
        "-i", input_path,
        "-pix_fmt", "yuvj420p",
        "-q:v", "5",
        output_path
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except Exception as e:
        if lang == "ja":
            info(f"[ERROR] 変換失敗: {filename} - {e}")
        elif lang == "en":
            info(f"[ERROR] Conversion failed: {filename} - {e}")

def monitor_progress(output_jpg, total_files, queue=None, lang="en"):
    if lang == "ja":
        info("yuvj420p形式に変換しています・・・。", queue)
    elif lang == "en":
        info("Converting to yuvj420p format...", queue)
    start_time = time.time()
    while True:
        try:
            current = len([f for f in os.listdir(output_jpg) if f.lower().endswith(".jpg")])
        except FileNotFoundError:
            current = 0
        elapsed = time.time() - start_time
        fps = current / elapsed if elapsed > 0 else 0
        info(f"[PROGRESS] {current}/{total_files} (avg: {fps:.2f} fps)", queue)
        if current >= total_files:
            break
        time.sleep(0.5)

def convert_to_yuvj420p(
    ffmpeg_path,
    final_jpg,
    output_jpg,
    queue=None,
    lang="en"
):

    # 出力先フォルダがなければ作成（中身があったら消して空で作り直すのが安全）
    if os.path.exists(output_jpg):
        shutil.rmtree(output_jpg)
    os.makedirs(output_jpg, exist_ok=True)
    
    # ファイル一覧
    jpg_files = sorted([
        f for f in os.listdir(final_jpg)
        if f.lower().endswith(".jpg")
    ])
    total_files = len(jpg_files)

    # 進捗監視スレッド
    progress_thread = threading.Thread(target=monitor_progress, args=(output_jpg, total_files, queue, lang))
    progress_thread.start()

    # 並列変換
    tasks = [
        (ffmpeg_path, final_jpg, output_jpg, filename, lang)
        for filename in jpg_files
    ]
    with Pool() as pool:
        pool.map(convert_image, tasks)

    progress_thread.join()

    # フォルダをリネーム
    if os.path.exists(final_jpg):
        shutil.rmtree(final_jpg)
    shutil.move(output_jpg, final_jpg)
    if lang == "ja":
        info("yuvj420p形式に変換が完了しました。", queue)
    elif lang == "en":
        info("Conversion to yuvj420p format completed.", queue)

