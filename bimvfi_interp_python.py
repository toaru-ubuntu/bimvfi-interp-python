import faulthandler
faulthandler.enable()

import tkinter as tk
from tkinter import messagebox, ttk
import threading
import os
import platform
import shutil
import time
import json
from queue import Queue, Empty
from threading import Event
from python_script.definition import all_definition
from python_script.config_gui import open_settings_window
from python_script.ffmpeg_download import download_ffmpeg_windows
from python_script.setting_information import setting_information
from python_script.convert_to_image import convert_video_to_images
from python_script.calculate_psnr import calculate_psnr
from python_script.psnr_ratio import calculate_psnr_ratio
from python_script.scene_change_detection import value_definitions
from python_script.analyse_scene import analyse_scene_calculate
from python_script.frame_thinning import frame_thinning
from python_script.calculate_gaps import calculate_gaps
from python_script.frame_interp_1 import interpolate_frames
from python_script.frame_interp_2 import interpolate_final_frames
from python_script.noise_reduction import noise_reduction
from python_script.convert_to_yuvj420p import convert_to_yuvj420p
from python_script.encode_and_merge import encode_video
from python_script.messages import MESSAGES

def read_lang_from_config(config_path):
    lang = "en"  # デフォルト
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            # 辞書から "lang" キーを取得（無ければ "en" を返す）
            lang = config_data.get("lang", "en")
        except json.JSONDecodeError:
            # 万が一古いテキスト形式が残っていた場合などのエラー回避
            pass
    return lang

def main():
    # --- 言語設定の読み込み ---
    config_path = "config"
    lang = read_lang_from_config(config_path)

    def getmsg(key):
        return MESSAGES[lang][key]

    progress_queue = Queue()
    stop_event = Event()

    is_os = platform.system().lower()
    is_windows = is_os == "windows"

    temp_folder = "temp"
    ffmpeg_dest_dir = "ffmpeg_bin"
    material_folder = "material"
    jpg_folder = os.path.join(temp_folder, "jpg")
    output_jpg = os.path.join(temp_folder, "output_jpg")
    final_jpg = os.path.join(temp_folder, "final_jpg")
    filename_path = os.path.join(temp_folder, "filename.txt")
    file_count_path = os.path.join(temp_folder, "file_count.txt")
    psnr_file_path = os.path.join(temp_folder, "psnr_values.txt")
    psnr_ratio_file_path = os.path.join(temp_folder, "psnr_ratio.txt")
    scene_change_frame_file = os.path.join(temp_folder, "scene_change_frame.txt")
    file_count_file = os.path.join(temp_folder, "file_count.txt")
    scene_threshold_file = os.path.join(temp_folder, "scene_threshold.txt")
    gap_file = os.path.join(temp_folder, "gaps.txt")
    ffmpeg_path = os.path.join("ffmpeg_bin", "ffmpeg.exe") if is_windows else "ffmpeg"
    ffprobe_path = os.path.join("ffmpeg_bin", "ffprobe.exe") if is_windows else "ffprobe"

    root = tk.Tk()
    root.title(getmsg("app_title"))
    root.geometry("750x750")

    # UIラベル・ボタン
    label = tk.Label(root, text=getmsg("select_action"))
    label.pack(pady=10)

    run_button = tk.Button(root, text=getmsg("start"), command=lambda: run_main_py_async())
    run_button.pack(pady=5)

    stop_button = tk.Button(root, text=getmsg("stop"), command=lambda: stop_event.set())
    stop_button.pack(pady=5)

    settings_button = tk.Button(
        root, text=getmsg("settings"),
        command=lambda: open_settings_window(config_path, is_os, parent=root)
    )
    settings_button.pack(pady=5)

    main_frame = tk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    log_frame = tk.Frame(main_frame)
    log_frame.pack(fill=tk.BOTH, expand=True)

    scrollbar = tk.Scrollbar(log_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    log_text = tk.Text(log_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set, height=25)
    log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    log_text.tag_config("error", foreground="red")
    scrollbar.config(command=log_text.yview)

    progress_var = tk.DoubleVar()
    progress_text_var = tk.StringVar()
    progress_frame = tk.Frame(main_frame)
    progress_frame.pack(fill=tk.X, pady=10)
    progress_bar = ttk.Progressbar(progress_frame, variable=progress_var, maximum=100, length=350)
    progress_bar.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=False)
    progress_label = tk.Label(progress_frame, textvariable=progress_text_var, fg="green", anchor="w",
                             font=("Meiryo", 12, "bold"), width=32)
    progress_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def poll_progress_queue():
        try:
            while True:
                line = progress_queue.get_nowait()
                if line.startswith("[PROGRESS]"):
                    import re
                    clean_line = line.replace("[PROGRESS]", "").strip()
                    match = re.search(r"(\d+)\s*/\s*(\d+)(?:\s*\(avg:\s*([\d.]+)\s*fps\))?", clean_line)
                    if match:
                        current = int(match.group(1))
                        total = int(match.group(2))
                        percent = (current / total) * 100 if total > 0 else 0
                        progress_var.set(percent)
                        fps = match.group(3)
                        if fps:
                            progress_text_var.set(f"{getmsg('progress')}: {current} / {total}   ({float(fps):.2f} fps)")
                        else:
                            progress_text_var.set(f"{getmsg('progress')}: {current} / {total}")
                    else:
                        progress_text_var.set(clean_line)
                elif line.startswith("[ERROR]"):
                    log_text.insert(tk.END, line, "error")
                else:
                    log_text.insert(tk.END, line)
                log_text.see(tk.END)
        except Empty:
            pass
        root.after(100, poll_progress_queue)

    def initial_check():
        if not os.path.exists(config_path):
            progress_queue.put(f"[ERROR] Config file not found.\nPlease open 'Change settings' and click 'Save settings' at least once.\n")
            progress_queue.put(f"[ERROR] configファイルが見つかりません。\n'Change settings'から、一度'save settings'をクリックして下さい。\n")
        if not os.path.exists(material_folder):
            progress_queue.put(f"[ERROR] Material folder not found.\n")
            progress_queue.put(f"Creating material folder.\n")
            progress_queue.put(f"[ERROR] materialフォルダが見つかりません\n")
            progress_queue.put(f"materialフォルダを作成します。\n")
            os.makedirs(material_folder, exist_ok=True)

    def run_main_py_async():
        stop_event.clear()
        log_text.delete("1.0", tk.END)
        
        def worker():
            result = all_definition(temp_folder, config_path, material_folder, progress_queue, lang)
            if result == "no_file" or stop_event.is_set(): return

            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                python_path = config_data.get("python_path", "python")
            except Exception as e:
                progress_queue.put(f"[ERROR] {getmsg('config_read_error')}: {e}\n")
                return

            setting_information(config_path, progress_queue, lang)
            if stop_event.is_set(): return

            start_time = time.time()
            download_ffmpeg_windows(ffmpeg_dest_dir, progress_queue, lang)
            if stop_event.is_set(): return

            convert_video_to_images(ffmpeg_path, ffprobe_path, temp_folder, jpg_folder, material_folder, filename_path, progress_queue, lang)
            if stop_event.is_set(): return

            calculate_psnr(jpg_folder, file_count_path, ffmpeg_path, psnr_file_path,
               queue=progress_queue, stop_event=stop_event, lang=lang)
            if stop_event.is_set(): return

            calculate_psnr_ratio(psnr_file_path, psnr_ratio_file_path, progress_queue, lang)
            if stop_event.is_set(): return

            value_definitions(config_path, psnr_file_path, file_count_file, scene_change_frame_file, progress_queue, lang)
            if stop_event.is_set(): return

            analyse_scene_calculate(config_path, psnr_file_path, psnr_ratio_file_path, scene_change_frame_file, scene_threshold_file, file_count_file, progress_queue, lang)
            if stop_event.is_set(): return

            frame_thinning(psnr_file_path, psnr_ratio_file_path, scene_threshold_file, jpg_folder, output_jpg, progress_queue, lang)
            if stop_event.is_set(): return

            calculate_gaps(jpg_folder, gap_file, progress_queue, lang)
            if stop_event.is_set(): return

            interpolate_frames(config_path, jpg_folder, output_jpg, gap_file, scene_change_frame_file, file_count_path, progress_queue, lang)
            if stop_event.is_set(): return

            interpolate_final_frames(config_path, jpg_folder, output_jpg, final_jpg, progress_queue, lang)
            if stop_event.is_set(): return

            noise_reduction(config_path, scene_change_frame_file, final_jpg, progress_queue)
            if stop_event.is_set(): return

            convert_to_yuvj420p(ffmpeg_path, final_jpg, output_jpg, progress_queue, lang)
            if stop_event.is_set(): return

            encode_video(temp="temp", config_path="config", queue=progress_queue, lang=lang)
            if stop_event.is_set(): return
            elapsed_time = time.time() - start_time
            msg = f"{getmsg('elapsed_time')}: {elapsed_time:.2f} {getmsg('seconds')}\n"
            progress_queue.put(msg)

        threading.Thread(target=worker, daemon=True).start()

    root.after(100, poll_progress_queue)
    root.after(100, initial_check)
    root.mainloop()

if __name__ == "__main__":
    main()

