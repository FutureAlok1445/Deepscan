from loguru import logger

try:
    import torch
    import torch.nn.functional as F
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    logger.warning("torch not installed — GradCAM will return empty results")

import numpy as np


class GradCAMGenerator:
    def __init__(self, model=None, target_layer=None):
        self.model = model
        self.target_layer = target_layer
        self.activations = None
        self.gradients = None
        if HAS_TORCH and model and target_layer:
            self.target_layer.register_forward_hook(self.save_activation)
            self.target_layer.register_backward_hook(self.save_gradient)

    def save_activation(self, module, input, output):
        self.activations = output

    def save_gradient(self, module, grad_in, grad_out):
        self.gradients = grad_out[0]

    def generate(self, input_tensor):
        if not HAS_TORCH or not self.model:
            return np.zeros((8, 8))
        self.model.eval()
        output = self.model(input_tensor)
        self.model.zero_grad()
        output.backward(torch.ones_like(output))
        pooled_gradients = torch.mean(self.gradients, dim=[0, 2, 3])
        for i in range(self.activations.shape[1]):
            self.activations[:, i, :, :] *= pooled_gradients[i]
        heatmap = F.relu(torch.mean(self.activations, dim=1).squeeze())
        return (heatmap / torch.max(heatmap)).cpu().detach().numpy()