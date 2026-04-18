import os
import cv2
import glob
import yaml
import torch
from tqdm import tqdm

# BiM-VFIのモジュール群
import modules.models as models

class VIP_Interpolator:
    def __init__(self, cfg_path='bim_vfi.yaml', weight_path='pretrained/bim_vfi.pth', gpu_id=0):
        """モデルの初期化とデバイスへのロード"""
        
        if gpu_id == 1:
            self.device = torch.device('cpu')
        else:
            if torch.cuda.is_available():
                self.device = torch.device('cuda')
            elif hasattr(torch, "xpu") and torch.xpu.is_available():
                self.device = torch.device('xpu')
            else:
                self.device = torch.device('cpu')
            
        print(f"使用デバイス: {self.device}")

        # ★★★ ここから追加：実行環境に最適なデータ型の自動判定 ★★★
        self.autocast_dtype = torch.float32 # デフォルトは最も安全なFP32

        if self.device.type == 'cuda':
            # NVIDIA GPUの場合：Ampere世代(RTX3000番台)以降ならbfloat16、それ以前はfloat16
            if torch.cuda.is_bf16_supported():
                self.autocast_dtype = torch.bfloat16
            else:
                self.autocast_dtype = torch.float16
        elif self.device.type == 'xpu':
            # Intel GPUの場合：Arcアーキテクチャはbfloat16に強力に最適化されているため一択
            self.autocast_dtype = torch.bfloat16
        else:
            # CPU等の場合：処理落ちやエラーを防ぐためFP32のまま計算
            self.autocast_dtype = torch.float32
            
        print(f"自動混合精度(AMP)の型: {self.autocast_dtype}")
        # ★★★ ここまで追加 ★★★
        
        # 設定の読み込み
        with open(cfg_path, 'r') as f:
            cfg = yaml.load(f, Loader=yaml.FullLoader)
        cfg['env'] = {'cudnn': False}; cfg['distributed'] = False; cfg['local_rank'] = 0  # エラー回避用のダミー環境変数
        
        # モデルの構築と重みのロード
        self.base_model = models.make(cfg)
        self.base_model.device = self.device
        self.base_model.load_checkpoint(weight_path)
        
        # ネットワーク本体を取り出して デバイス へ転送し、推論モードに
        self.model = self.base_model.model
        self.model.eval()
        self.model.to(self.device)
        self.model.float()
        
        self.cached_file = None
        self.cached_tensor = None
        
    def process_folder(self, input_dir, output_dir, ratio=2):
        """
        指定したフォルダの画像を読み込み、任意の倍率(ratio)で補間する
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # 画像のリストアップ
        img_paths = sorted(glob.glob(os.path.join(input_dir, '*.[pj][pn]*[g]')))
        if len(img_paths) < 2:
            print("エラー: 補間には最低2枚の画像が必要です。")
            return

        img0 = None
        out_idx = 1
        
        # 比率に応じた時間ステップを計算してデバイスへ転送
        time_range = torch.arange(1, ratio).view(ratio - 1, 1, 1, 1).to(self.device) / ratio

        with torch.no_grad():
            for i in tqdm(range(len(img_paths)), desc="フレーム処理"):
                img_np = cv2.imread(img_paths[i])[:, :, ::-1]  # BGR -> RGB
                # テンソル化して デバイス へ
                img_tensor = (torch.tensor(img_np.transpose(2, 0, 1).copy()).float() / 255.0).unsqueeze(0).to(self.device)

                # 1枚目の処理
                if img0 is None:
                    img0 = img_tensor
                    cv2.imwrite(os.path.join(output_dir, f"{out_idx:08d}.jpg"), img_np[:, :, ::-1])
                    out_idx += 1
                    
                    _, _, h, w = img0.shape
                    if h >= 2160: scale_factor, pyr_level = 0.25, 7
                    elif h >= 1080: scale_factor, pyr_level = 0.5, 6
                    else: scale_factor, pyr_level = 1, 5
                    continue

                # 中間フレームの生成
                for r in range(ratio - 1):
                    dis0 = torch.ones((1, 1, h, w), device=self.device) * (r / ratio)
                    dis1 = 1 - dis0
                    
                    with torch.autocast(device_type=self.device.type, dtype=self.autocast_dtype):
	                    results = self.model(
	                        img0=img0, img1=img_tensor, time_step=time_range[r], 
	                        dis0=dis0, dis1=dis1, scale_factor=scale_factor,
	                        ratio=(1 / scale_factor), pyr_level=pyr_level, nr_lvl_skipped=0
	                    )
                    
                    imgt_pred = torch.clip(results['imgt_pred'], 0, 1)
                    
                    out_img = (imgt_pred[0] * 255).byte().cpu().numpy().transpose(1, 2, 0)[:, :, ::-1]
                    cv2.imwrite(os.path.join(output_dir, f"{out_idx:08d}.jpg"), out_img)
                    out_idx += 1

                # 元のフレーム（終点）を保存
                cv2.imwrite(os.path.join(output_dir, f"{out_idx:08d}.jpg"), img_np[:, :, ::-1])
                out_idx += 1
                
                # 次のループに向けて始点を更新
                img0 = img_tensor


    def interpolate_single_frame(self, file1, file2, output_path, timestep=0.5):
        """
        VIP専用: 2枚の画像から指定した時間の補間画像を生成
        """
        if self.cached_file == file1:
            img0 = self.cached_tensor
        else:
            img1_np = cv2.imread(file1)[:, :, ::-1]
            img0 = (torch.tensor(img1_np.transpose(2, 0, 1).copy()).float() / 255.0).unsqueeze(0).to(self.device)

        img2_np = cv2.imread(file2)[:, :, ::-1]
        img1 = (torch.tensor(img2_np.transpose(2, 0, 1).copy()).float() / 255.0).unsqueeze(0).to(self.device)

        self.cached_file = file2
        self.cached_tensor = img1

        _, _, h, w = img0.shape
        if h >= 2160: scale_factor, pyr_level = 0.25, 7
        elif h >= 1080: scale_factor, pyr_level = 0.5, 6
        else: scale_factor, pyr_level = 1, 5

        # 4. 補間処理
        with torch.no_grad():
            dis0 = torch.ones((1, 1, h, w), device=self.device) * timestep
            dis1 = 1 - dis0
            time_tensor = torch.tensor([timestep]).view(1, 1, 1, 1).to(self.device)
            
            with torch.autocast(device_type=self.device.type, dtype=self.autocast_dtype):
                results = self.model(
                    img0=img0, img1=img1, time_step=time_tensor, 
                    dis0=dis0, dis1=dis1, scale_factor=scale_factor,
                    ratio=(1 / scale_factor), pyr_level=pyr_level, nr_lvl_skipped=0
                )
            
            imgt_pred = torch.clip(results['imgt_pred'], 0, 1)
            
            # 【追加】GPU側の処理完了を明示的に待機
            # ※ここでセグフォが起きる場合は、ROCm側のPyTorch仕様やVRAM枯渇(OOM)が原因と断定できます
            if self.device.type == 'cuda':
                torch.cuda.synchronize(self.device)
            
            # 【修正】CPUへ移し、Numpy配列に変換後、copy()でメモリを安全に連続させる
            out_tensor = (imgt_pred[0] * 255).byte().cpu()
            out_img = out_tensor.numpy().transpose(1, 2, 0)[:, :, ::-1].copy()
            
            # 保存
            cv2.imwrite(output_path, out_img)
            
            # ★追加: XPUのVRAMキャッシュを解放してゴミを捨てる
            #if self.device.type == 'cuda':
                #torch.cuda.empty_cache()
            #elif hasattr(torch, "xpu") and self.device.type == 'xpu':
                #torch.xpu.empty_cache()
                
if __name__ == '__main__':
    interp = VIP_Interpolator()
    interp.process_folder(
        input_dir="assets/demo/video1", 
        output_dir="vip_test_output", 
        ratio=2
    )
