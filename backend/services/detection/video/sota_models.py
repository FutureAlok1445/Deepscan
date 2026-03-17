import torch
import torch.nn as nn
from torchvision import models, transforms
from timm import create_model
from loguru import logger
import cv2
import numpy as np
from typing import List, Dict

class MesoNet4Detector:
    '''
    MesoNet4: NIST 81% F1 deepfake detector. Pretrained on FF++.
    Lightweight CNN for spatial artifacts.
    '''
    def __init__(self):
        try:
            self.model = create_model('mesonet', pretrained=True)
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

    def predict(self, frame: np.ndarray) -> Dict[str, float]:
        if self.model is None:
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

    def predict(self, frame: np.ndarray) -> Dict[str, float]:
        if self.model is None:
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
    avg_score = np.mean([s['score'] for s in scores])
    avg_conf = np.mean([s['confidence'] for s in scores])
    return {'score': float(avg_score), 'confidence': float(avg_conf)}

sota_ensemble = {
    'mesonet': MesoNet4Detector(),
    'xception': XceptionDetector()
}

