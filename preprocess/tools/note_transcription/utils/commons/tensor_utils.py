import torch
import torch.distributed as dist


def reduce_tensors(metrics):
    new_metrics = {}
    for k, v in metrics.items():
        if isinstance(v, torch.Tensor):
            dist.all_reduce(v)
            v = v / dist.get_world_size()
        if type(v) is dict:
            v = reduce_tensors(v)
        new_metrics[k] = v
    return new_metrics


def tensors_to_scalars(tensors):
    if isinstance(tensors, torch.Tensor):
        tensors = tensors.item()
        return tensors
    elif isinstance(tensors, dict):
        new_tensors = {}
        for k, v in tensors.items():
            v = tensors_to_scalars(v)
            new_tensors[k] = v
        return new_tensors
    elif isinstance(tensors, list):
        return [tensors_to_scalars(v) for v in tensors]
    else:
        return tensors


def tensors_to_np(tensors):
    if isinstance(tensors, dict):
        new_np = {}
        for k, v in tensors.items():
            if isinstance(v, torch.Tensor):
                v = v.cpu().numpy()
            if type(v) is dict:
                v = tensors_to_np(v)
            new_np[k] = v
    elif isinstance(tensors, list):
        new_np = []
        for v in tensors:
            if isinstance(v, torch.Tensor):
                v = v.cpu().numpy()
            if type(v) is dict:
                v = tensors_to_np(v)
            new_np.append(v)
    elif isinstance(tensors, torch.Tensor):
        v = tensors
        if isinstance(v, torch.Tensor):
            v = v.cpu().numpy()
        if type(v) is dict:
            v = tensors_to_np(v)
        new_np = v
    else:
        raise Exception(f'tensors_to_np does not support type {type(tensors)}.')
    return new_np


def move_to_cpu(tensors):
    ret = {}
    for k, v in tensors.items():
        if isinstance(v, torch.Tensor):
            v = v.cpu()
        if type(v) is dict:
            v = move_to_cpu(v)
        ret[k] = v
    return ret


def move_to_device(batch, device=None):
    """Move batch to specified device (MPS, CUDA, or CPU).
    
    Args:
        batch: Data to move (tensor, list, tuple, or dict)
        device: Target device. If None, uses MPS if available, else CPU.
    """
    if device is None:
        if torch.backends.mps.is_available():
            device = torch.device('mps')
        else:
            device = torch.device('cpu')
    elif isinstance(device, int):
        # Legacy support for GPU ID - now just use MPS or CPU
        if torch.backends.mps.is_available():
            device = torch.device('mps')
        else:
            device = torch.device('cpu')
    elif isinstance(device, str):
        device = torch.device(device)
    
    # base case: object can be directly moved using `to`
    if callable(getattr(batch, 'to', None)):
        return batch.to(device, non_blocking=True)
    elif isinstance(batch, list):
        for i, x in enumerate(batch):
            batch[i] = move_to_device(x, device)
        return batch
    elif isinstance(batch, tuple):
        batch = list(batch)
        for i, x in enumerate(batch):
            batch[i] = move_to_device(x, device)
        return tuple(batch)
    elif isinstance(batch, dict):
        for k, v in batch.items():
            batch[k] = move_to_device(v, device)
        return batch
    return batch


# Alias for backward compatibility
def move_to_cuda(batch, gpu_id=0):
    """Legacy alias for move_to_device. Uses MPS on Apple Silicon."""
    return move_to_device(batch, device=None)
