from modules.models.base_model import BaseModel
from modules.models import register

@register('bim_vfi')
class BiMVFI(BaseModel):
    def __init__(self, cfg):
        # 親クラス(BaseModel)の初期化を呼び出すだけ
        super(BiMVFI, self).__init__(cfg)
        
    # ※推論には train_one_epoch や validate などの関数は一切不要なので全削除
