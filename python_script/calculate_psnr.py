import os
import subprocess
import re
import time
from multiprocessing import Pool

def info(msg, queue=None):
    """キューがあればqueue.put、なければprintする共通メッセージ関数"""
    if queue is not None:
        queue.put(msg + "\n")
    else:
        print(msg)

def compute_psnr(args):
    ffmpeg_path, index, img1, img2 = args
    cmd = [ffmpeg_path, "-nostdin", "-i", img1, "-i", img2, "-lavfi", "psnr", "-f", "null", "-"]
    try:
        result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True, check=True)
        match = re.search(r"average:(inf|[0-9.]+)", result.stderr)
        psnr_value = match.group(1) if match else "50.000000"
        if psnr_value == "inf":
            psnr_value = "50.000000"
    except subprocess.CalledProcessError as e:
        psnr_value = "50.000000"
    return index, psnr_value

def calculate_psnr(
    jpg_folder, file_count_path, ffmpeg_path,
    psnr_file_path, queue=None, stop_event=None, lang="en"
):
    with open(file_count_path, "r", encoding="utf-8") as f:
        file_count = int(f.readline().strip())
    file_list = sorted([entry.name for entry in os.scandir(jpg_folder) if entry.is_file()])
    full_paths = [os.path.join(jpg_folder, f) for f in file_list]
    tasks = [(ffmpeg_path, i, full_paths[i], full_paths[i+1]) for i in range(file_count - 1)]
    psnr_values = [None] * (file_count - 1)

    if lang == "ja":
        info("psnr値を計算中・・・。", queue)
    elif lang == "en":
        info("Calculating PSNR values...", queue)

    start_time = time.time()
    last_progress_time = [start_time]  # リストにしてnonlocal扱い

    def on_result(result):
        index, value = result
        psnr_values[index] = value
        completed = sum(1 for x in psnr_values if x is not None)
        elapsed = time.time() - start_time
        avg_fps = completed / elapsed if elapsed > 0 else 0
        now = time.time()
        # 0.5秒ごとにのみ進捗送信
        if now - last_progress_time[0] >= 0.5 or completed == (file_count - 1):
            if lang == "ja":
                progress_msg = f"[PROGRESS] {completed}/{file_count - 1} (avg: {avg_fps:.2f} fps)"
            elif lang == "en":
                progress_msg = f"[PROGRESS] {completed}/{file_count - 1} (avg: {avg_fps:.2f} fps)"
            if queue:
                queue.put(progress_msg)
            last_progress_time[0] = now

    with Pool() as pool:
        for result in pool.imap_unordered(compute_psnr, tasks):
            if stop_event is not None and stop_event.is_set():
                if queue:
                    if lang == "ja":
                        queue.put("[INFO] psnr計算が中断されました。\n")
                    elif lang == "en":
                        queue.put("[INFO] PSNR calculation was stopped.\n")
                return
            on_result(result)

    with open(psnr_file_path, "w", encoding="utf-8") as f:
        for val in psnr_values:
            f.write((val if val is not None else "50.000000") + "\n")
    if lang == "ja":
        info("psnr値の計算終了！", queue)
    elif lang == "en":
        info("PSNR value calculation finished!", queue)
    info(f"[PROGRESS] {file_count - 1}/{file_count - 1}", queue)

