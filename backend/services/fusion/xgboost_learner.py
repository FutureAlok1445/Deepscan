import os
import numpy as np
from loguru import logger

try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False
    logger.warning("xgboost not installed — XGBoostMetaLearner will use mean fallback")


class XGBoostMetaLearner:
    def __init__(self, model_path: str = "meta_model.json"):
        self.model = None
        self.is_fitted = False
        if HAS_XGB:
            self.model = xgb.XGBRegressor()
            self.is_fitted = os.path.exists(model_path)
            if self.is_fitted:
                self.model.load_model(model_path)

    def predict(self, features: list) -> float:
        if self.is_fitted and self.model:
            return float(self.model.predict(np.array([features]))[0])
        return float(np.mean(features))