import os
import time
import shutil
import platform
import json
import sys
from threading import Thread

# --- パス解決の魔法 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
bim_vfi_dir = os.path.join(project_root, 'bim_vfi')

if bim_vfi_dir not in sys.path:
    sys.path.append(bim_vfi_dir)

try:
    from vip_bimvfi import VIP_Interpolator
except ImportError as e:
    print(f"BiM-VFIの読み込みに失敗しました: {e}")

def info(msg, queue=None):
    """進捗やエラーをqueue経由で送信。なければprint。"""
    if queue is not None:
        queue.put(msg + "\n")
    else:
        print(msg)

def interpolate_final_frames(
    config_path,
    jpg_folder,
    output_jpg,
    final_jpg,
    queue=None,
    lang="en"
):
    # 設定を読み込む (JSON形式)
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        
        magnification = int(config_data.get("scale", "2"))
        gpu_id = int(config_data.get("gpu", 0))
    except Exception:
        magnification = 2
        gpu_id = 0

    if magnification == 1:
        if os.path.exists(jpg_folder):
            shutil.rmtree(jpg_folder)
        shutil.move(output_jpg, final_jpg)
        if lang == "ja":
            info("最終フレーム補間なし。", queue)
        elif lang == "en":
            info("No final frame interpolation.", queue)
        return

    if lang == "ja":
        info("最終フレーム補完をしています・・・。", queue)
    elif lang == "en":
        info("Performing final frame interpolation...", queue)
        
    os.makedirs(final_jpg, exist_ok=True)
    if os.path.exists(jpg_folder):
        shutil.rmtree(jpg_folder)
    shutil.move(output_jpg, jpg_folder)

    # 進捗計算用のファイル数
    file_count = len([entry.name for entry in os.scandir(jpg_folder) if entry.is_file()])
    file_count2 = file_count * magnification
    interval = 0.5

    stop_thread = {"flag": False}
    shared_data = {"fps": 0.0}

    def count_files():
        previous_count = 0
        start_time = time.time()
        while not stop_thread["flag"]:
            file_count3 = len(os.listdir(final_jpg))
            current_time = time.time()
            elapsed_time = current_time - start_time
            frame_diff = file_count3 - previous_count
            fps = frame_diff / elapsed_time if elapsed_time > 0 else 0
            shared_data["fps"] = fps
            info(f"[PROGRESS] {file_count3}/{file_count2} (avg: {fps:.2f} fps)", queue)
            previous_count = file_count3
            start_time = current_time
            time.sleep(interval)

    # プログレスバー監視スレッドの開始
    counter_thread = Thread(target=count_files, daemon=True)
    counter_thread.start()

    # --- 🚀 ここからが BiM-VFIの処理 ---
    try:
        info("BiM-VFIエンジンで最終補間を開始します...", queue)
        interpolator = VIP_Interpolator(
            cfg_path=os.path.join(bim_vfi_dir, 'bim_vfi.yaml'),
            weight_path=os.path.join(bim_vfi_dir, 'pretrained/bim_vfi.pth'),
            gpu_id=gpu_id
        )
        
        # subprocessの代わりに、直接 process_folder メソッドを呼び出す！
        interpolator.process_folder(
            input_dir=jpg_folder,
            output_dir=final_jpg,
            ratio=magnification
        )
    except Exception as e:
        if lang == "ja":
            info(f"[ERROR] BiM-VFIエラー: {e}", queue)
        elif lang == "en":
            info(f"[ERROR] BiM-VFI error: {e}", queue)

    # 終了処理
    stop_thread["flag"] = True
    counter_thread.join()

    final_count = len([entry.name for entry in os.scandir(final_jpg) if entry.is_file()])
    fps = shared_data["fps"]
    if lang == "ja":
        info("最終フレーム補完が完了しました。", queue)
    elif lang == "en":
        info("Final frame interpolation completed.", queue)
    info(f"[PROGRESS] {final_count}/{file_count2} (avg: {fps:.2f} fps)", queue)

    if os.path.exists(jpg_folder):
        shutil.rmtree(jpg_folder)
