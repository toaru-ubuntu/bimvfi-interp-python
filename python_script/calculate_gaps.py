import os
import time

def info(msg, queue=None):
    """キューがあればqueue.put、なければprintする共通メッセージ関数"""
    if queue is not None:
        queue.put(msg + "\n")
    else:
        print(msg)

def calculate_gaps(jpg_folder, gap_file, queue=None, lang="en"):
    if lang == "ja":
        info("重複フレームを削除した情報を収集しています・・・。", queue)
    elif lang == "en":
        info("Collecting information after duplicate frames have been removed...", queue)
    # ベースファイルの数を定義
    file_count = len(os.listdir(jpg_folder))

    # ファイル名をソートしてリストに格納
    file_list = sorted(os.listdir(jpg_folder))

    # 出力ファイルを初期化
    with open(gap_file, 'w', encoding='utf-8') as f:
        pass

    # 最後の進捗表示時間を初期化
    last_time = time.time()

    # ループしてファイル間のギャップを計算
    previous_number = None
    first = True

    for file in file_list:
        if not file.endswith('.jpg'):
            continue

        # ファイル名から番号部分を抽出
        file_name = os.path.basename(file)
        number = file_name.split('.')[0]
        number = int(number.lstrip('0')) if number.lstrip('0') else 0

        if first:
            first = False
        else:
            # ギャップを計算
            if previous_number is not None:
                gap = number - previous_number - 1
                with open(gap_file, 'a', encoding='utf-8') as f:
                    f.write(f"{gap}\n")

        # 現在の時間を取得
        current_time = time.time()
        # 最後に進捗表示をした時から1秒経過したかを確認
        if current_time - last_time >= 1:
            info(f"[PROGRESS] {number}/{file_count}", queue)
            last_time = current_time

        previous_number = number

    if lang == "ja":
        info("重複フレームを削除した情報の収集が終わりました。", queue)
    elif lang == "en":
        info("Finished collecting information after duplicate frames have been removed.", queue)
    info(f"[PROGRESS] {file_count}/{file_count}", queue)

