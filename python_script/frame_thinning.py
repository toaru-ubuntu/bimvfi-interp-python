import os
import shutil
import time

def info(msg, queue=None):
    """キューがあればqueue.put、なければprintする共通メッセージ関数"""
    if queue is not None:
        queue.put(msg + "\n")
    else:
        print(msg)

def frame_thinning(psnr_file_path, psnr_ratio_file_path, scene_threshold_file, jpg_folder, output_jpg, queue=None, lang="en"):
    if lang == "ja":
        info("重複フレームを探しています・・・。", queue)
    elif lang == "en":
        info("Searching for duplicate frames...", queue)
    
    # フレームリストと最終ファイル名
    file_list = sorted(os.listdir(jpg_folder))
    file_count = len(file_list)
    last_file = file_list[-1]

    # PSNR値と比率を読み込み
    with open(psnr_file_path, 'r', encoding='utf-8') as f:
        psnr_values = [float(line.strip()) for line in f if line.strip()]
    with open(psnr_ratio_file_path, 'r', encoding='utf-8') as f:
        psnr_ratios = [float(line.strip()) for line in f if line.strip()]

    # シーンごとのしきい値を読み込み
    scene_threshold_dict = {}
    with open(scene_threshold_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                frame, threshold = line.strip().split()
                scene_threshold_dict[int(frame)] = float(threshold)

    # シーンごとの開始・終了インデックスを構成
    scene_frames = [0] + sorted(scene_threshold_dict.keys())
    frame_thinning = []
    last_time = time.time()

    # シーンごとに処理
    for i in range(len(scene_frames) - 1):
        start = scene_frames[i]
        end = scene_frames[i + 1] - 2  # PSNRとレシオのインデックスに合わせて -2

        threshold = scene_threshold_dict[scene_frames[i + 1]]

        for j in range(start, end + 1):
            if j >= len(psnr_values) or j >= len(psnr_ratios):
                continue

            psnr = psnr_values[j]
            ratio = psnr_ratios[j]

            if psnr > threshold and not (0.9 <= ratio <= 1.1):
                frame_index = f"{j + 2:08d}"  # +2でフレーム番号に変換
                frame_name = f"{frame_index}.jpg"
                frame_thinning.append(frame_name)

            # 進捗表示
            now = time.time()
            if now - last_time >= 0.5:
                info(f"[PROGRESS] {j + 2}/{file_count}", queue)
                last_time = now

    # 出力フォルダ作成
    os.makedirs(output_jpg, exist_ok=True)
    for file_name in file_list:
        shutil.copy(os.path.join(jpg_folder, file_name), output_jpg)

    # フレーム削除
    if lang == "ja":
        info("重複フレームを探し終わりました。", queue)
    elif lang == "en":
        info("Finished searching for duplicate frames.", queue)
    info(f"[PROGRESS] {file_count}/{file_count}", queue)
    if lang == "ja":
        info("重複フレームを削除しています・・・。", queue)
    elif lang == "en":
        info("Deleting duplicate frames...", queue)

    for frame in frame_thinning:
        file_to_delete = os.path.join(output_jpg, frame)
        if os.path.exists(file_to_delete):
            os.remove(file_to_delete)

    # 最後のフレームは必ず残す
    shutil.copy(os.path.join(jpg_folder, last_file), output_jpg)

    # 削除リストを保存
    output_file = os.path.join("temp", "frame_thinning.txt")
    with open(output_file, 'w', encoding="utf-8") as f:
        for value in frame_thinning:
            f.write(f"{value}\n")

    if lang == "ja":
        info("重複フレームの削除が終了しました。", queue)
    elif lang == "en":
        info("Finished deleting duplicate frames.", queue)

    # 入力フォルダを削除 → 出力をリネーム
    if os.path.exists(jpg_folder):
        shutil.rmtree(jpg_folder)
    shutil.move(output_jpg, jpg_folder)
