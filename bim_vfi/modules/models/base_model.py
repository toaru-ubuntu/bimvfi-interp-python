import torch
from modules.components import make_components
from modules.models import register

@register('base_model')
class BaseModel:
    def __init__(self, cfgs):
        self.cfgs = cfgs
        # 外部（vip_bimvfi.py）から上書きされる前提のため、デフォルト値をセットするのみ
        self.device = torch.device('cpu')
        
        # 推論に必要なモデル本体の構築のみ行う（1回だけ実行）
        self.model = make_components(self.cfgs['model'])
        self.model_without_ddp = self.model

    def load_checkpoint(self, file_path):
        """
        推論用の重み(チェックポイント)だけをロードする
        """
        checkpoint = torch.load(file_path, map_location=self.device, weights_only=False)
        self.model_without_ddp.load_state_dict(checkpoint['model'])
        self.move_components_to_device()
        return None

    def move_components_to_device(self):
        """
        モデルを自動判別（または指定された）デバイスへ転送
        """
        self.model.to(self.device)
