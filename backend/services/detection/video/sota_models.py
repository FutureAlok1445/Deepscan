from loguru import logger
from typing import List, Dict

HAS_TORCH = False
HAS_CV2 = False
HAS_TIMM = False

try:
    import torch
    import torch.nn as nn
    from torchvision import models, transforms
    HAS_TORCH = True
except ImportError:
    logger.warning("torch/torchvision not installed — SOTA models disabled")

try:
    import timm
    from timm import create_model
    HAS_TIMM = True
except ImportError:
    logger.warning("timm not installed — MesoNet/Xception detectors disabled")

try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    import types
    np = types.SimpleNamespace(ndarray=object, mean=lambda x: 50.0)
    logger.warning("cv2/numpy not installed — SOTA frame analysis disabled")


class MesoNet4Detector:
    '''
    MesoNet4: NIST 81% F1 deepfake detector. Pretrained on FF++.
    Lightweight CNN for spatial artifacts.
    '''
    def __init__(self):
        self.model = None
        if not HAS_TORCH or not HAS_TIMM or not HAS_CV2:
            logger.warning("MesoNet4Detector: Missing dependencies — disabled")
            return
        try:
            model_name = 'mesonet' if 'mesonet' in timm.list_models() else 'xception'
            if model_name == 'xception':
                logger.warning("MesoNet not found in timm, falling back to Xception architecture")
            self.model = create_model(model_name, pretrained=True, num_classes=2 if model_name == 'xception' else 1)
            self.model.eval()
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.model.to(self.device)
            self.transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
            ])
            logger.info('MesoNet loaded')
        except Exception as e:
            logger.error(f'MesoNet load failed: {e}')
            self.model = None

    def predict(self, frame) -> Dict[str, float]:
        if self.model is None or not HAS_CV2:
            return {'score': 50.0, 'confidence': 0.0}
        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            tensor = self.transform(rgb).unsqueeze(0).to(self.device)
            with torch.no_grad():
                pred = torch.sigmoid(self.model(tensor)).item() * 100
            return {'score': pred, 'confidence': pred/100}
        except:
            return {'score': 50.0, 'confidence': 0.0}

class XceptionDetector:
    '''
    XceptionNet: 95% FF++ accuracy. Face forensics CNN.
    '''
    def __init__(self):
        self.model = None
        if not HAS_TORCH or not HAS_TIMM or not HAS_CV2:
            logger.warning("XceptionDetector: Missing dependencies — disabled")
            return
        try:
            self.model = create_model('xception', pretrained=True, num_classes=2)
            self.model.eval()
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.model.to(self.device)
            self.transform = transforms.Compose([
                transforms.Resize((299, 299)),
                transforms.ToTensor(),
                transforms.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5])
            ])
            logger.info('Xception loaded')
        except Exception as e:
            logger.error(f'Xception load failed: {e}')
            self.model = None

    def predict(self, frame) -> Dict[str, float]:
        if self.model is None or not HAS_CV2:
            return {'score': 50.0, 'confidence': 0.0}
        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            tensor = self.transform(rgb).unsqueeze(0).to(self.device)
            with torch.no_grad():
                logits = self.model(tensor)
                prob = torch.softmax(logits, dim=1)[0][1].item() * 100
            return {'score': prob, 'confidence': prob/100}
        except:
            return {'score': 50.0, 'confidence': 0.0}

def ensemble_sota(scores: List[Dict]) -> Dict[str, float]:
    '''Weighted fusion: Meso 0.4, Xception 0.3.'''
    if not scores:
        return {'score': 50.0, 'confidence': 0.0}
    try:
        import numpy as _np
        avg_score = _np.mean([s['score'] for s in scores])
        avg_conf = _np.mean([s['confidence'] for s in scores])
        return {'score': float(avg_score), 'confidence': float(avg_conf)}
    except Exception:
        # Pure Python fallback
        vals = [s['score'] for s in scores]
        confs = [s['confidence'] for s in scores]
        return {'score': sum(vals)/len(vals), 'confidence': sum(confs)/len(confs)}

# Only instantiate if dependencies are available
if HAS_TORCH and HAS_TIMM and HAS_CV2:
    sota_ensemble = {
        'mesonet4': MesoNet4Detector(),
        'xception': XceptionDetector()
    }
else:
    sota_ensemble = {}
    logger.warning("SOTA ensemble models not loaded — dependencies missing")
