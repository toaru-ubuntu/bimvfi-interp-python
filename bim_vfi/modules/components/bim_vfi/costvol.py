import torch
import torch.nn.functional as F

class costvol_func:
    @staticmethod
    def apply(tenOne, tenTwo, intKernelSize):
        pad = intKernelSize // 2
        tenTwo_padded = F.pad(tenTwo, (pad, pad, pad, pad), mode='constant', value=0.0)
        
        cost_list = []
        H, W = tenOne.shape[2], tenOne.shape[3]
        
        for dy in range(intKernelSize):
            for dx in range(intKernelSize):
                shifted = tenTwo_padded[:, :, dy:dy+H, dx:dx+W]
                cost = (tenOne * shifted).sum(dim=1, keepdim=True)
                cost_list.append(cost)
                
        return torch.cat(cost_list, dim=1)
