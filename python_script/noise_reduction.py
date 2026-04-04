import os
import json
import shutil

def info(msg, queue=None):
    """キューがあればqueue.put、なければprintする共通メッセージ関数"""
    if queue is not None:
        queue.put(msg + "\n")
    else:
        print(msg)

def noise_reduction(config_path, scene_change_frame_file, final_jpg, queue=None):

    #倍率(scale)の読み込み (JSON形式)
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        # JSONから "scale" キーを取得し、数値(int)に変換。キーが無い場合はデフォルトで2倍
        magnification = int(config_data.get("scale", "2"))
    except Exception:
        # 万が一のエラー時の安全策
        magnification = 2 
            
    def process_frames(scene_change_frame_file, magnification, queue=None):
        delete_frame_list = []
        copy_frame_list = []

        # 読み込み処理
        with open(scene_change_frame_file, 'r', encoding='utf-8') as file:
            for frame_number in file:
                frame_number = int(frame_number.strip())
                # 削除フレームリスト作成
                for i in range(magnification - 1):
                    delete_number = frame_number * magnification - (magnification + i)
                    padded_frame = f"{delete_number:08d}.jpg"
                    delete_frame_list.append(padded_frame)
                
                # コピーフレームリスト作成
                copy_frame = frame_number * magnification - (2 * magnification - 1)
                padded_frame = f"{copy_frame:08d}.jpg"
                copy_frame_list.append(padded_frame)
        
        #info(f"削除リスト: {delete_frame_list}", queue)
        #info(f"コピーリスト: {copy_frame_list}", queue)

        # 削除処理
        for frame in delete_frame_list:
            frame_path = os.path.join(final_jpg, frame)
            if os.path.exists(frame_path):
                os.remove(frame_path)
                #info(f"削除ファイル: {frame}", queue)

        # コピー処理
        for i in range(len(copy_frame_list)):
            for j in range(magnification - 1):
                index = magnification * (i + 1) - ((magnification + i) - j)
                if index < len(delete_frame_list):  # インデックスチェック
                    src_frame = copy_frame_list[i]
                    dst_frame = delete_frame_list[index]
                    src_path = os.path.join(final_jpg, src_frame)
                    dst_path = os.path.join(final_jpg, dst_frame)
                    if os.path.exists(src_path):
                        shutil.copyfile(src_path, dst_path)
                        #info(f"コピー: {src_frame} から {dst_frame} へ", queue)
                        
    process_frames(scene_change_frame_file, magnification, queue)
