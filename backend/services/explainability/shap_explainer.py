import numpy as np
from loguru import logger

try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False
    logger.warning("shap not installed — ShapExplainer will return empty results")


class ShapExplainer:
    def __init__(self, model=None):
        self.model = model

    def explain(self, input_data):
        if HAS_SHAP and self.model:
            try:
                return shap.Explainer(self.model)(np.array([input_data])).values.flatten().tolist()
            except Exception:
                pass
        return list(np.zeros(len(input_data) if hasattr(input_data, '__len__') else 5))