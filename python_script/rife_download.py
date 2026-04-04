import os
import platform
import urllib.request
import zipfile
import shutil

def info(msg, queue=None):
    """キューがあればqueue.put、なければprintする共通メッセージ関数"""
    if queue is not None:
        queue.put(msg + "\n")
    else:
        print(msg)
        
def download_rife(rife_dest_dir="rife", queue=None, lang="en"):
    system = platform.system().lower()
    if system == "windows":
        zip_url = "https://github.com/nihui/rife-ncnn-vulkan/releases/download/20221029/rife-ncnn-vulkan-20221029-windows.zip"
        rife_binary = "rife-ncnn-vulkan.exe"
        extracted_folder_name = "rife-ncnn-vulkan-20221029-windows"
    elif system == "linux":
        zip_url = "https://github.com/nihui/rife-ncnn-vulkan/releases/download/20221029/rife-ncnn-vulkan-20221029-ubuntu.zip"
        rife_binary = "rife-ncnn-vulkan"
        extracted_folder_name = "rife-ncnn-vulkan-20221029-ubuntu"
    else:
        if lang == "ja":
            info(f"{system} は未対応です。", queue)
        elif lang == "en":
            info(f"{system} is not supported.", queue)
        return

    rife_bin_path = os.path.join(rife_dest_dir, rife_binary)
    
    # rife-ncnn-vulkanが存在するか確認
    if os.path.exists(rife_bin_path):
        if lang == "ja":
            info(f"{rife_binary}はダウンロード済みです。", queue)
        elif lang == "en":
            info(f"{rife_binary} is already downloaded.", queue)
        return
        
    zip_name = "rife.zip"
    temp_extract_dir = "rife_temp"

    os.makedirs(rife_dest_dir, exist_ok=True)

    if lang == "ja":
        info(f"{rife_binary} をダウンロードしています...", queue)
    elif lang == "en":
        info(f"Downloading {rife_binary}...", queue)
    try:
        urllib.request.urlretrieve(zip_url, zip_name)
    except Exception as e:
        if lang == "ja":
            info(f"{rife_binary}のダウンロード中にエラーが発生しました: {e}", queue)
        elif lang == "en":
            info(f"An error occurred while downloading {rife_binary}: {e}", queue)
        return
        
    if lang == "ja":
        info("展開中...", queue)
    elif lang == "en":
        info("Extracting...", queue)
        
    with zipfile.ZipFile(zip_name, 'r') as zip_ref:
        zip_ref.extractall(temp_extract_dir)

    extracted_root = os.path.join(temp_extract_dir, extracted_folder_name)
    if not os.path.exists(extracted_root):
        if lang == "ja":
            info(f"展開後のフォルダが見つかりません: {extracted_root}", queue)
        elif lang == "en":
            info(f"Extracted folder not found: {extracted_root}", queue)
        raise FileNotFoundError(f"Extracted folder not found: {extracted_root}")

    for item in os.listdir(extracted_root):
        src_path = os.path.join(extracted_root, item)
        dst_path = os.path.join(rife_dest_dir, item)
        shutil.move(src_path, dst_path)

    # Linuxの場合は実行権限を付与
    if system == "linux":
        os.chmod(rife_bin_path, 0o755)

    shutil.rmtree(temp_extract_dir)
    os.remove(zip_name)

    if lang == "ja":
        info(f"{rife_binary} のセットアップが完了しました。", queue)
    elif lang == "en":
        info(f"{rife_binary} setup is complete.", queue)

