import os
import time
import json
from scenedetect import SceneManager, open_video, AdaptiveDetector

def info(msg, queue=None):
    """キューがあればqueue.put、なければprintする共通メッセージ関数"""
    if queue is not None:
        queue.put(msg + "\n")
    else:
        print(msg)

def value_definitions(config_path, psnr_file_path, file_count_file, scene_change_frame_file, queue=None, lang="en"):
    if lang == "ja":
        info("PySceneDetectでシーンチェンジを検出しています・・・。", queue)
    elif lang == "en":
        info("Detecting scene changes with PySceneDetect...", queue)
    
    # 1. 設定ファイルからしきい値を読み込む
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        # ※注意: GUIのデフォルト値(19)がそのまま渡ってくると高すぎるため、
        # 万が一に備えてデフォルトは3.0にしています
        scene_change_threshold = float(config_data.get("scene_thresh", "3.0"))
    except Exception:
        scene_change_threshold = 3.0

    # 2. 動画ファイルのパスを特定する
    # filename.txt は psnr_file_path (tempフォルダ) と同じ階層にあることを利用します
    temp_dir = os.path.dirname(psnr_file_path)
    filename_txt_path = os.path.join(temp_dir, "filename.txt")
    
    if os.path.exists(filename_txt_path):
        with open(filename_txt_path, "r", encoding="utf-8") as f:
            video_filename = f.readline().strip()
        video_path = os.path.join("material", video_filename)
    else:
        info("[ERROR] filename.txtが見つからないため、動画を特定できません。", queue)
        return

    if not os.path.exists(video_path):
        info(f"[ERROR] 動画ファイルが見つかりません: {video_path}", queue)
        return

    # 3. PySceneDetectの実行
    video = open_video(video_path, backend='pyav')
    scene_manager = SceneManager()
    scene_manager.add_detector(AdaptiveDetector(adaptive_threshold=scene_change_threshold))
    
    scene_manager.detect_scenes(video)
    scene_list = scene_manager.get_scene_list()
    
    scene_change_frames = []
    
    # プログレス表示用（pyscenedetectは処理が一瞬で終わるため開始・終了の報告メインになります）
    for i, scene in enumerate(scene_list):
        if i == 0:
            continue
        # PySceneDetectのフレーム番号(0始まり)を、FFmpegで連番出力した画像(1始まり)に合わせるため +1 しています
        start_frame = scene[0].get_frames() + 1
        scene_change_frames.append(start_frame)

    if lang == "ja":
        info("シーンチェンジのフレーム検出が終了しました。", queue)
    elif lang == "en":
        info("Scene change frame detection finished.", queue)

    # 4. 結果の書き出し
    with open(scene_change_frame_file, "w", encoding="utf-8") as f:
        for value in scene_change_frames:
            f.write(f"{value}\n")
