import os
import json

def info(msg, queue=None):
    if queue is not None:
        queue.put(msg + "\n")
    else:
        print(msg)
        
def setting_information(config_path, queue=None, lang="en"):
    # configファイルから値取得 (JSON形式で読み込み)
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
    except Exception as e:
        # 万が一読み込みに失敗した場合は空の辞書にして、デフォルト値を使わせる
        config_data = {}

    # 辞書からキー名を指定して取得（ファイルにキーが無い場合のデフォルト値も設定）
    magnification = config_data.get("scale", "2")
    device = config_data.get("gpu", "0")
    video_codec = config_data.get("video_codec", "h264")
    bitrate = config_data.get("bitrate", "3000k")
    scene_change = config_data.get("scene_thresh", "3")
    ratio = config_data.get("thin", "1.05")
    
    if device == "0":
        use_device = "GPU"
    else:
        use_device = "CPU"
    
    if lang == "ja":
        info(f"補間倍率{magnification}倍。", queue)
        info(f"{use_device}を使って処理をします。", queue)
        info(f"{video_codec}でエンコードします。", queue)
        info(f"ビットレートは{bitrate}。", queue)
        info(f"シーンチェンジのしきい値は{scene_change}。", queue)
        info(f"間引き係数は{ratio}。", queue)
    elif lang == "en":
        info(f"Interpolation magnification: {magnification}x.", queue)
        info(f"Starting processing with {use_device}...", queue)
        info(f"Encoding with {video_codec}.", queue)
        info(f"Bitrate: {bitrate}.", queue)
        info(f"Scene change threshold: {scene_change}.", queue)
        info(f"Frame thinning coefficient: {ratio}.", queue)

