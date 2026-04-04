import os
import shutil
import threading
import time
import json
import platform
import sys

# 「このファイルがある場所」から計算して、bim_vfiフォルダの絶対的な住所（パス）を作る
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
bim_vfi_dir = os.path.join(project_root, 'bim_vfi')

# Pythonに「ここも探し物リストに追加して！」と頼む
sys.path.append(bim_vfi_dir)


# 【追加】VIP専用のBiM-VFIラッパーを読み込む
try:
    from vip_bimvfi import VIP_Interpolator
except ImportError as e:
    print(f"インポート中にエラーが発生しました: {e}")
    import traceback
    traceback.print_exc()

def info(msg, queue=None):
    if queue is not None:
        queue.put(msg + "\n")
    else:
        print(msg)

def progress_bar(output_jpg, total_files, queue=None, lang="en"):
    if lang == "ja":
        info("重複フレームを削除した分を補間中・・・。", queue)
    elif lang == "en":
        info("Interpolating for removed duplicate frames...", queue)
    initial_files = len([f for f in os.listdir(output_jpg) if f.endswith('.jpg')])
    start_time = time.time()
    interval = 0.5
    while True:
        current_files = len([f for f in os.listdir(output_jpg) if f.endswith('.jpg')])
        processed_files = current_files - initial_files
        elapsed_time = time.time() - start_time
        fps = processed_files / elapsed_time if elapsed_time > 0 else 0
        info(f"[PROGRESS] {current_files}/{total_files} (avg: {fps:.2f} fps)", queue)
        if current_files >= total_files:
            break
        time.sleep(interval)
    if lang == "ja":
        info("重複フレームを削除した分の補間が終わりました。", queue)
    elif lang == "en":
        info("Interpolation for removed duplicate frames finished.", queue)
    info(f"[PROGRESS] {current_files}/{total_files} (avg: {fps:.2f} fps)", queue)

def interpolate_frames(
    config_path,
    jpg_folder,
    output_jpg,
    gap_file,
    scene_change_frame_file,
    file_count_path,
    queue=None,
    lang="en"
):
    os.makedirs(output_jpg, exist_ok=True)

    input_files = sorted([f for f in os.listdir(jpg_folder) if f.endswith('.jpg')])

    with open(gap_file, 'r', encoding='utf-8') as f:
        gap_values = [int(line.strip()) for line in f]

    with open(scene_change_frame_file, 'r', encoding='utf-8') as f:
        scene_change_frames = [f"{int(frame.strip()):08d}.jpg" for frame in f]

    with open(file_count_path, 'r', encoding='utf-8') as f:
        total_files = int(f.readline().strip())

    output_file_number = 1
    file_count = len(input_files)
    tasks = []

    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
    gpu_id = int(config_data.get('gpu', 0))
    
    # 【追加】BiM-VFIのエンジンを初期化
    interpolator = VIP_Interpolator(
        cfg_path='bim_vfi/bim_vfi.yaml',
        weight_path='bim_vfi/pretrained/bim_vfi.pth',
        gpu_id=gpu_id
    )

    for i in range(file_count - 1):
        file1 = os.path.join(jpg_folder, input_files[i])
        file2 = os.path.join(jpg_folder, input_files[i + 1])
        gap = gap_values[i]
        scene_change_detected = input_files[i + 1] in scene_change_frames

        if os.path.isfile(file1):
            padded_number = f"{output_file_number:08d}"
            shutil.copy(file1, f"{output_jpg}/{padded_number}.jpg")
            output_file_number += 1

        if os.path.isfile(file1) and os.path.isfile(file2):
            if scene_change_detected:
                for _ in range(1, gap + 1):
                    padded_number = f"{output_file_number:08d}"
                    shutil.copy(file1, f"{output_jpg}/{padded_number}.jpg")
                    output_file_number += 1
            else:
                for b in range(1, gap + 1):
                    result = 1 / (gap + 1) * b
                    padded_number = f"{output_file_number:08d}"
                    # タスクとしてリストに積んでおく
                    tasks.append((result, file1, file2, padded_number))
                    output_file_number += 1

    # プログレスバーのスレッドを起動
    progress_thread = threading.Thread(target=progress_bar, args=(output_jpg, total_files, queue, lang))
    progress_thread.start()

    # 【変更】マルチプロセス(Pool)を廃止し、キャッシュを活かした直列処理へ
    for task in tasks:
        result, file1, file2, padded_number = task
        output_path = f"{output_jpg}/{padded_number}.jpg"
        
        # BiM-VFIエンジンに直接リクエストを投げる！
        interpolator.interpolate_single_frame(
            file1=file1,
            file2=file2,
            output_path=output_path,
            timestep=result
        )

    # 最後のファイルをコピー
    file_last = os.path.join(jpg_folder, input_files[-1])
    if os.path.isfile(file_last):
        padded_number = f"{output_file_number:08d}"
        shutil.copy(file_last, f"{output_jpg}/{padded_number}.jpg")

    progress_thread.join()
