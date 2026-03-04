import io
import base64
from loguru import logger

try:
    from PIL import Image, ImageChops, ImageEnhance
    import numpy as np
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    logger.warning("Pillow/numpy not installed — ELA analysis will return empty results")


def run_ela(image_path: str, quality: int = 90) -> dict:
    if not HAS_PIL:
        return {"ela_score": 0.0, "heatmap_b64": "", "anomaly_regions": [], "analysis_note": "Pillow not available"}
    try:
        original = Image.open(image_path).convert('RGB')
        buffer = io.BytesIO()
        original.save(buffer, 'JPEG', quality=quality)
        buffer.seek(0)
        
        diff = ImageChops.difference(original, Image.open(buffer).convert('RGB'))
        extrema = diff.getextrema()
        max_diff = max([ex[1] for ex in extrema])
        scale = 255.0 / max_diff if max_diff != 0 else 1.0
        enhanced_diff = ImageEnhance.Brightness(diff).enhance(scale * 10.0)
        
        out_buffer = io.BytesIO()
        enhanced_diff.save(out_buffer, format="PNG")
        
        return {
            "ela_score": min(float(np.mean(np.array(diff)) * 5), 100.0),
            "heatmap_b64": base64.b64encode(out_buffer.getvalue()).decode('utf-8'),
            "anomaly_regions": [],
            "analysis_note": "Error Level Analysis amplifies artifacts introduced by multiple JPEG compressions."
        }
    except Exception as e:
        return {"ela_score": 0.0, "heatmap_b64": "", "anomaly_regions": [], "analysis_note": str(e)}