import os

def info(msg, queue=None):
    """キューがあればqueue.put、なければprintする共通メッセージ関数"""
    if queue is not None:
        queue.put(msg + "\n")
    else:
        print(msg)
        
def calculate_psnr_ratio(psnr_file_path, psnr_ratio_file_path, queue=None, lang="en"):
    # PSNR値を読み込む
    with open(psnr_file_path, "r", encoding="utf-8") as f:
        psnr_values = [float(line.strip()) for line in f if line.strip()]
    
    if lang == "ja":
        info("psnrレシオの計算中・・・。", queue)
    elif lang == "en":
        info("Calculating PSNR ratio...", queue)
        
    # 比率を計算（次 / 現在）
    psnr_ratio = []
    for i in range(len(psnr_values) - 1):
        current = psnr_values[i]
        next_val = psnr_values[i + 1]
        if current == 0:
            ratio = 0.0  # ゼロ割防止
        else:
            ratio = next_val / current
        psnr_ratio.append(ratio)

    # 最後に 1.000000 を追加
    psnr_ratio.append(1.0)
    
    if lang == "ja":
        info("psnrレシオの計算終了。", queue)
    elif lang == "en":
        info("PSNR ratio calculation finished.", queue)
    
    # 結果を保存
    with open(psnr_ratio_file_path, "w", encoding="utf-8") as f:
        for ratio in psnr_ratio:
            f.write(f"{ratio:.6f}\n")

