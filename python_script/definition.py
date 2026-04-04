import os
import shutil

def info(msg, queue=None):
    """キューがあればqueue.put、なければprintする共通メッセージ関数"""
    if queue is not None:
        queue.put(msg + "\n")
    else:
        print(msg)
        
def all_definition(temp_folder, config_path, material_folder, queue=None, lang="en"):
    # tempフォルダ削除
    if os.path.exists(temp_folder):
        try:
            shutil.rmtree(temp_folder)
            if lang == "ja":
                info("前回の temp フォルダを削除しました。", queue)
            elif lang == "en":
                info("Previous temp folder was deleted.", queue)
        except Exception as e:
            if lang == "ja":
                info(f"[ERROR] temp フォルダ削除中にエラー: {e}", queue)
            elif lang == "en":
                info(f"[ERROR] Error occurred while deleting temp folder: {e}", queue)

    # temp_output.mkv と temp_audio.wav の削除
    for temp_file in ["temp_output.mkv", "temp_audio.wav"]:
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
                if lang == "ja":
                    info(f"{temp_file} を削除しました。", queue)
                elif lang == "en":
                    info(f"{temp_file} was deleted.", queue)
            except Exception as e:
                if lang == "ja":
                    info(f"[ERROR] {temp_file} 削除中にエラー: {e}", queue)
                elif lang == "en":
                    info(f"[ERROR] Error occurred while deleting {temp_file}: {e}", queue)
            
    # configファイルの有無を確認
    if not os.path.exists(config_path):
        if lang == "ja":
            info("[ERROR] configファイルが見つかりません。", queue)
            info("設定変更ウィンドウから、一度「設定の保存」をして下さい。", queue)
        elif lang == "en":
            info("[ERROR] Config file not found.", queue)
            info("Please save your settings once from the settings window.", queue)
        return None
                
    # materialフォルダの有無を確認
    if not os.path.exists(material_folder):
        if lang == "ja":
            info("[ERROR] material フォルダが見つかりません。", queue)
            info("materialフォルダを作成します。", queue)
        elif lang == "en":
            info("[ERROR] Material folder not found.", queue)
            info("Creating material folder.", queue)
        os.makedirs(material_folder, exist_ok=True)
        return None

    file_list = [entry.name for entry in os.scandir(material_folder) if entry.is_file()]
    if not file_list:
        if lang == "ja":
            info("[ERROR] material フォルダに動画ファイルが見つかりません。", queue)
            info("[ERROR] material フォルダに動画ファイルを置いて下さい。", queue)
        elif lang == "en":
            info("[ERROR] No video files found in the material folder.", queue)
            info("[ERROR] Please put a video file in the material folder.", queue)
        return "no_file"

