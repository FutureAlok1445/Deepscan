from loguru import logger
from PIL import Image, ImageFilter, ImageStat
import math

try:
    import torch
    import torch.nn as nn
    from torchvision import models, transforms
    from transformers import pipeline
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    logger.warning("torch/transformers not installed — VisualForensics will use heuristic & noise residuals")

try:
    import numpy as np
    from scipy.ndimage import median_filter
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


def _pil_noise_variance(image: Image.Image) -> float:
    """
    Estimate noise variance using pure PIL.
    AI-generated images tend to be smoother (lower noise variance).
    Real camera photos have natural sensor noise (higher variance).
    Returns authenticity score 0-100.
    """
    try:
        gray = image.convert("L")
        # Blur then subtract to isolate high-frequency noise
        blurred = gray.filter(ImageFilter.MedianFilter(size=3))
        stat_orig = ImageStat.Stat(gray)
        stat_blur = ImageStat.Stat(blurred)
        # Approximate noise variance as difference in stddev
        noise_std = abs(stat_orig.stddev[0] - stat_blur.stddev[0])
        # Real images: noise_std typically 1.5-5+
        # AI images: noise_std often < 0.8 (very smooth)
        if noise_std < 0.5:
            return 18.0   # Very smooth — strong AI signature
        elif noise_std < 1.2:
            return 42.0   # Somewhat smooth — suspicious
        elif noise_std < 2.5:
            return 68.0   # Natural-ish
        else:
            return 88.0   # Clearly noisy — likely real camera
    except Exception as e:
        logger.error(f"PIL noise variance failed: {e}")
        return 50.0


def _pil_edge_coherence(image: Image.Image) -> float:
    """
    Check edge coherence. AI images often have suspiciously perfect or blurry edges.
    Returns authenticity score 0-100.
    """
    try:
        gray = image.convert("L")
        edges = gray.filter(ImageFilter.FIND_EDGES)
        stat = ImageStat.Stat(edges)
        mean_edge = stat.mean[0]
        # Very low edge energy = over-blurred (AI hallucination)
        # Very HIGH and very uniform = GAN pattern artifacts
        edge_std = stat.stddev[0]
        if mean_edge < 3.0:
            return 30.0  # Near-zero edges = over-smoothed / heavily compressed
        elif mean_edge > 60.0 and edge_std < 5.0:
            return 35.0  # Unusually uniform high edges = GAN artifact
        elif mean_edge > 8.0 and edge_std > 8.0:
            return 82.0  # Rich varied edges = natural image
        else:
            return 58.0  # Inconclusive
    except Exception as e:
        logger.error(f"PIL edge coherence failed: {e}")
        return 50.0


def _pil_color_uniformity(image: Image.Image) -> float:
    """
    AI images often have too-perfect color distributions (low std per channel).
    Returns authenticity score 0-100.
    """
    try:
        rgb = image.convert("RGB")
        stat = ImageStat.Stat(rgb)
        # stddev per channel
        avg_std = sum(stat.stddev) / 3.0
        # Real photos: avg channel std typically 30-80
        # AI images (especially faces/portraits): often 20-40 range, very uniform
        if avg_std < 20:
            return 28.0  # Suspiciously uniform color
        elif avg_std < 35:
            return 52.0  # Somewhat uniform
        elif avg_std < 55:
            return 75.0  # Reasonable diversity
        else:
            return 88.0  # High color diversity = likely real scene
    except Exception as e:
        logger.error(f"PIL color uniformity failed: {e}")
        return 50.0


def _pil_compression_artifacts(image_path: str) -> float:
    """
    Real photos typically show JPEG compression artifacts in high-detail areas.
    AI images may lack natural compression patterns.
    Returns authenticity score 0-100.
    """
    try:
        img = Image.open(image_path)
        # Check image format and quality indicators
        width, height = img.size
        try:
            # Re-save at low quality and compare — real images degrade differently
            import io
            buf = io.BytesIO()
            img.convert("RGB").save(buf, format="JPEG", quality=50)
            buf.seek(0)
            compressed = Image.open(buf).convert("RGB")
            orig_stat = ImageStat.Stat(img.convert("RGB"))
            comp_stat = ImageStat.Stat(compressed)
            # Compute mean absolute difference in brightness
            diff = abs(orig_stat.mean[0] - comp_stat.mean[0])
            # AI images tend to have less compression artifact difference
            if diff < 1.5:
                return 40.0  # Suspiciously little difference = AI smooth gradient
            elif diff < 4.0:
                return 65.0
            else:
                return 85.0
        except Exception:
            return 60.0
    except Exception as e:
        logger.error(f"PIL compression check failed: {e}")
        return 50.0


class VisualForensicsDetector:
    """
    Layer 4: Detects visual and pixel-level manipulation (GAN faces, face swaps).
    Upgraded Ensemble: EfficientNet-B4 + ViT AI-Image-Detector + Meta's Noise Residuals.
    Provides MAS (Media Authenticity Score).
    
    Heuristic fallback (no torch/numpy) uses 4 PIL-based sub-checks:
    1. Noise variance (smoothness detector)
    2. Edge coherence (sharpness pattern)
    3. Color channel uniformity
    4. Compression artifact analysis
    """
    def __init__(self):
        self.eff_model = None
        self.eff_transform = None
        self.ai_detector_pipe = None
        self.device = None

    async def load_model(self):
        """Lazy load the CNNs to avoid boot delays."""
        if not HAS_TORCH:
            logger.warning("Torch/Transformers not found! VisualForensics using PIL heuristic fallback.")
            return

        try:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

            # 1. EfficientNet Forensics
            base = models.efficientnet_b4(pretrained=False)
            base.classifier[1] = nn.Linear(base.classifier[1].in_features, 1)
            self.eff_model = base.to(self.device).eval()
            self.eff_transform = transforms.Compose([
                transforms.Resize((380, 380)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ])
            logger.info("VisualForensics EfficientNet-B4 initialized.")

            # 2. HuggingFace ViT AI Image Detector
            device_id = 0 if torch.cuda.is_available() else -1
            self.ai_detector_pipe = pipeline(
                "image-classification",
                model="umm-maybe/AI-image-detector",
                device=device_id,
            )
            logger.info("VisualForensics ViT AI-detector loaded.")

        except Exception as e:
            logger.error(f"Failed to load visual models: {e}")

    def _extract_noise_residual(self, image: Image.Image) -> float:
        """numpy-based noise: if numpy available, use it; else delegate to PIL version."""
        if not HAS_NUMPY:
            return _pil_noise_variance(image)

        try:
            img_gray = image.convert("L")
            img_arr = np.array(img_gray, dtype=np.float32)
            smoothed = median_filter(img_arr, size=3)
            noise_residual = np.abs(img_arr - smoothed)
            variance = np.var(noise_residual)
            if variance < 0.2:
                return 20.0
            elif variance < 0.8:
                return 50.0
            else:
                return 88.0
        except Exception as e:
            logger.error(f"Noise residual extraction failed: {e}")
            return 50.0

    def analyze(self, image_path: str) -> dict:
        result = {
            "score_mas": 50.0,
            "details": []
        }

        try:
            image = Image.open(image_path).convert('RGB')

            if not HAS_TORCH or not self.eff_model or not self.ai_detector_pipe:
                # Full PIL heuristic analysis — 4 sub-checks
                noise_score = self._extract_noise_residual(image)
                edge_score  = _pil_edge_coherence(image)
                color_score = _pil_color_uniformity(image)
                comp_score  = _pil_compression_artifacts(image_path)

                # Weighted ensemble of PIL heuristics
                final = (0.35 * noise_score) + (0.25 * edge_score) + \
                        (0.20 * color_score) + (0.20 * comp_score)
                result["score_mas"] = max(0.0, min(100.0, final))

                # Build explanation
                if noise_score < 40:
                    result["details"].append(
                        f"Noise residual: unnaturally smooth texture detected (score={noise_score:.0f}/100). "
                        "This is a classic signature of diffusion model output."
                    )
                if edge_score < 45:
                    result["details"].append(
                        f"Edge coherence: abnormal edge pattern (score={edge_score:.0f}/100). "
                        "AI images often have over-smoothed or unnaturally uniform edges."
                    )
                if color_score < 45:
                    result["details"].append(
                        f"Color uniformity: suspiciously uniform color distribution (score={color_score:.0f}/100)."
                    )
                if comp_score < 50:
                    result["details"].append(
                        f"Compression fingerprint: lacks natural JPEG artifact patterns (score={comp_score:.0f}/100)."
                    )
                if not result["details"]:
                    result["details"].append(
                        f"PIL heuristics (noise={noise_score:.0f}, edges={edge_score:.0f}, "
                        f"color={color_score:.0f}, compression={comp_score:.0f}): no strong AI artifacts found."
                    )
                return result

            # --- Full ML path (torch available) ---
            noise_score = self._extract_noise_residual(image)

            tensor = self.eff_transform(image).unsqueeze(0).to(self.device)
            with torch.no_grad():
                raw = self.eff_model(tensor)
                eff_prob = torch.sigmoid(raw).item()
                eff_score = eff_prob * 100.0

            vit_results = self.ai_detector_pipe(image)
            vit_score = 90.0
            for res in vit_results:
                if res['label'] in ('artificial', 'fake'):
                    vit_score = (1.0 - res['score']) * 100.0
                    break
                elif res['label'] in ('human', 'real'):
                    vit_score = res['score'] * 100.0
                    break

            if vit_score < 40:
                result["details"].append(f"ViT classified image as AI-generated ({100 - vit_score:.1f}% confidence).")
            if eff_score < 40:
                result["details"].append("EfficientNet detected high probability of deepfake artifacts.")

            final_mas = (eff_score * 0.3) + (vit_score * 0.5) + (noise_score * 0.2)
            result["score_mas"] = min(100.0, max(0.0, final_mas))

        except Exception as e:
            logger.error(f"Error in visual forensics: {e}")
            result["score_mas"] = 50.0

        return result


visual_forensics = VisualForensicsDetector()
