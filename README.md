# BimVFI-interp-python (BIP)

BiM-VFIエンジンを活用し、GUIで簡単に操作できる動画フレーム補間ツールです。
重複フレームの削除やシーンチェンジの検出機能を備え、自然で滑らかな補間動画を生成します。

## ✨ 主な機能

* **使いやすいGUI**:<br> 
 直感的なインターフェースで、コマンドラインの知識がなくても操作可能。
* **スマートなデバイス自動判定**: 
  * Intel GPU (`torch.xpu` / Battlemage等) にネイティブ対応。
  * CUDA (NVIDIA) や ROCm (AMD) 環境も自動で認識して動作します。
  * GUIから「強制CPU動作 (GPU番号: 1)」への切り替えも可能。
* **高精度な補間ロジック**: 
  * PySceneDetectによるシーンチェンジ（カット変わり）の検出。不自然なブレンドを防ぎます。
  * 重複フレームを自動検出し、無駄な処理を省きつつ必要な箇所だけを的確に補間。
* **マルチスレッド対応**:<br> 
CPU動作時でも、PyTorchのマルチスレッドを活かして効率的に計算を行います。

## 💻 動作環境

* **OS**: Linux (Ubuntu推奨)
* **Python**: 3.10 以上
* **必須ソフトウェア**: `ffmpeg` (動画のエンコード/デコード用)
* **ハードウェア**: 
  * 推奨: Intel Arc, Radeon, GeForce（フルHD解像度の場合、VRAM12GB以上）
  * 最小: メモリ容量に余裕のあるマルチコアCPU (Ryzen等で動作確認済み)

## 🛠 インストール方法

1. **リポジトリのクローン**
   ```bash
   git clone https://github.com/toaru-ubuntu/bimvfi-interp-python.git
   cd bimvfi-interp-python
   
2. **Python仮想環境の作成と有効化**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    
3. **必要なパッケージのインストール**
    ```bash
    # XPU(Intel GPU)対応版のPyTorchをインストールする場合
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/xpu

    # その他の必須ライブラリ
    pip install opencv-python pyyaml scenedetect tqdm
    
Radeon,GeForceの場合は以下のリンクを参照
https://pytorch.org/
     
4. **学習済み重みファイルの配置**<br>
モデルの重みファイルはファイルサイズが大きいため、GitHubリポジトリには含まれていません。[BiM-VFIの公式](https://github.com/KAIST-VICLab/BiM-VFI)から重みファイル (bim_vfi.pth) をダウンロードし、以下の階層に配置してください。
    
    ```Plaintext
    bim_vfi/pretrained/bim_vfi.pth
    
5. **使い方**<br> 
仮想環境を有効化した状態で、メインスクリプトを実行します。
    ```bash
    python ./bimvfi_interp_python.py

# 注意事項

このスクリプトは [gyan.devのffmpegビルド](https://www.gyan.dev/ffmpeg/builds/) を自動ダウンロードして利用します。  
**このビルドは商用利用できません。個人利用・学習用途専用です。**
商用利用を希望する場合は、公式サイト [ffmpeg.org](https://ffmpeg.org/download.html) などから入手してください。

## 📄 ライセンス・謝辞 / License & Acknowledgements

本ソフトウェア（BimVFI-interp-python）は、以下の優れたプロジェクトを利用して構築されています。各プロジェクトの開発者に深く感謝いたしますとともに、ご利用の際は各ライセンスを遵守してください。

### 1. BiM-VFI (動画補間エンジン)
* **リポジトリ**: [KAIST-VICLab/BiM-VFI](https://github.com/KAIST-VICLab/BiM-VFI)
* **利用条件**: 本ツールおよび内部で使用されているBiM-VFIのソースコード・学習済みモデル（チェックポイント）は、**研究および教育目的でのみ**無償で使用できます。
* **商用利用について**: YouTubeの収益化動画、有料販売ツールへの組み込みなど、いかなる**商業利用も原則禁止**されています。商業目的で使用を希望する場合は、BiM-VFIの主任研究員から正式な許可を得る必要があります。

### 2. PySceneDetect (シーンチェンジ検出)
* **リポジトリ**: [breakthrough/PySceneDetect](https://github.com/breakthrough/pyscenedetect)
* **ライセンス**: BSD 3-Clause License
* **利用条件**: オープンソースであり、商用・非商用問わず自由に利用・改変が可能です。不自然なブレンドを防ぐためのカット検出処理として活用させていただいています。
