import os
import json

def info(msg, queue=None):
    if queue is not None:
        queue.put(msg + "\n")
    else:
        print(msg)

def median(data):
    if not data:
        raise ValueError("空のリストです")
    data_sorted = sorted(data)
    n = len(data_sorted)
    mid = n // 2
    if n % 2 == 0:
        return (data_sorted[mid - 1] + data_sorted[mid]) / 2
    else:
        return data_sorted[mid]

def analyse_scene_calculate(
    config_path, psnr_file_path, psnr_ratio_file_path, scene_change_frame_file, scene_threshold_file, file_count_file,
    queue=None, lang="en"
):
    # thinning_ratioを読み取り (JSON形式)
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        # JSONから "thin" キーを取得し、float型（浮動小数点数）に変換（デフォルト1.05）
        thinning_ratio = float(config_data.get("thin", "1.05"))
    except Exception:
        # 万が一の読み込みエラーに備えたデフォルト値
        thinning_ratio = 1.05

    # PSNR値と比率を読み込む
    with open(psnr_file_path, "r") as f:
        psnr_values = [float(line.strip()) for line in f if line.strip()]
    with open(psnr_ratio_file_path, "r") as f:
        psnr_ratios = [float(line.strip()) for line in f if line.strip()]

    with open(scene_change_frame_file, "r") as f:
        scene_frames = [int(line.strip()) for line in f if line.strip()]

    # 総フレーム数をfile_count_fileから取得
    with open(file_count_file, "r") as f:
        total_frames = int(f.read().strip())

    # 最初のシーンを含めるため先頭に0を追加
    scene_frames = [0] + scene_frames

    # 最後の区間も計算するため、末尾に総フレーム数を追加！
    scene_frames.append(total_frames)

    scene_threshold_dict = {}

    # シーンごとの処理開始メッセージ
    if lang == "ja":
        info("シーンごとのしきい値を計算しています・・・。", queue)
    elif lang == "en":
        info("Calculating per-scene thresholds...", queue)

    # 各シーンごとに処理
    for i in range(len(scene_frames) - 1):
        start = scene_frames[i]
        end = scene_frames[i + 1] - 2  # PSNRインデックスに合わせて -2

        if end < start:
            continue

        scene_psnr = psnr_values[start:end + 1]
        scene_ratio = psnr_ratios[start:end + 1]

        # PSNRレシオが 0.9～1.1 の範囲外のみ使用
        filtered_psnr = [
            val for val, ratio in zip(scene_psnr, scene_ratio)
            if ratio < 0.9 or ratio > 1.1
        ]

        if not filtered_psnr:
            continue

        med = median(filtered_psnr)
        threshold = med * thinning_ratio  # しきい値 = 中央値 × 間引き係数

        # ここで区切りフレーム番号として「scene_frames[i + 1]」を使う
        scene_change_frame = scene_frames[i + 1]
        scene_threshold_dict[scene_change_frame] = round(threshold, 6)
        
    # 結果を書き出す
    with open(scene_threshold_file, "w", encoding="utf-8") as f:
        for frame, threshold in scene_threshold_dict.items():
            f.write(f"{frame} {threshold}\n")
    
    if lang == "ja":
        info("シーンごとのしきい値計算が完了しました。", queue)
    elif lang == "en":
        info("Per-scene threshold calculation finished.", queue)

