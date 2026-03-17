try:
    import cv2
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    cv2 = None
    HAS_NUMPY = False

import base64
from PIL import Image, ImageChops, ImageEnhance, ImageOps, ImageFilter
from loguru import logger
import io


class ImagePreprocessor:
    """
    Layer 3: Prepares the image for forensic analysis.
    Standardizes dimensions, generates grayscale, frequency maps, ELA heatmap, and noise map.
    """
    def __init__(self, target_size=(380, 380)):
        self.target_size = target_size

    # ── JET colormap (PIL pure-Python fallback) ────────────────────────
    def _apply_jet_pil(self, gray_img: Image.Image) -> Image.Image:
        """Map grayscale PIL image to JET thermal colormap (blue→cyan→yellow→red)."""
        rgb = Image.new("RGB", gray_img.size)
        px = rgb.load()
        gx = gray_img.load()
        for y in range(gray_img.height):
            for x in range(gray_img.width):
                v = gx[x, y]
                if v < 64:
                    r, g, b = 0, v * 4, 255
                elif v < 128:
                    r, g, b = 0, 255, 255 - (v - 64) * 4
                elif v < 192:
                    r, g, b = (v - 128) * 4, 255, 0
                else:
                    r, g, b = 255, 255 - (v - 192) * 4, 0
                px[x, y] = (r, g, b)
        return rgb

    # ── ELA heatmap (original PIL path — kept for compatibility) ────────
    def generate_ela_pil(self, image_path: str, quality: int = 90) -> Image.Image:
        """ELA via PIL. Kept as secondary path; thermal variant preferred."""
        try:
            original = Image.open(image_path).convert('RGB')
            buf = io.BytesIO()
            original.save(buf, 'JPEG', quality=quality)
            buf.seek(0)
            compressed = Image.open(buf)
            ela_image = ImageChops.difference(original, compressed)
            extrema = ela_image.getextrema()
            max_diff = max([ex[1] for ex in extrema]) if extrema else 1
            if max_diff == 0:
                max_diff = 1
            scale = 255.0 / max_diff
            ela_image = ImageEnhance.Brightness(ela_image).enhance(scale)
            ela_gray = ela_image.convert("L")
            return self._apply_jet_pil(ela_gray)
        except Exception as e:
            logger.error(f"generate_ela_pil failed: {e}")
            return None

    def get_base64(self, image_path: str) -> str:
        """Helper to return base64 string for context/semantic pipelines."""
        try:
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception:
            return None

    # ── High-fidelity thermal heatmaps (reference-quality) ────────────
    def _compute_thermal_heatmaps(self, pil_img: Image.Image):
        """
        Compute JET-colormap ELA + noise uniformity map.
        Matches the reference ai_detector implementation exactly.
        Returns (ela_b64, ela_score, noise_b64, noise_score).
        """
        ela_b64, ela_score = "", 0
        noise_b64, noise_score = "", 0

        # ── ELA: quality=65, amplify x14 ──────────────────────────────
        try:
            buf = io.BytesIO()
            pil_img.save(buf, format="JPEG", quality=65)
            buf.seek(0)
            recompressed = Image.open(buf).convert("RGB")

            orig_arr = np.array(pil_img, dtype=np.float32)
            reco_arr = np.array(recompressed, dtype=np.float32)

            diff = np.abs(orig_arr - reco_arr)
            ela_gray_arr = np.mean(diff, axis=2)
            ela_amp = np.clip(ela_gray_arr * 14, 0, 255).astype(np.uint8)

            ela_score = int(np.mean(ela_amp) / 255 * 100 * 1.6)
            ela_score = min(100, ela_score)

            if cv2 is not None:
                ela_colored = cv2.applyColorMap(ela_amp, cv2.COLORMAP_JET)
                ela_rgb = cv2.cvtColor(ela_colored, cv2.COLOR_BGR2RGB)
                ela_pil = Image.fromarray(ela_rgb)
            else:
                ela_pil = self._apply_jet_pil(Image.fromarray(ela_amp))

            buf2 = io.BytesIO()
            ela_pil.save(buf2, format="PNG")
            ela_b64 = base64.b64encode(buf2.getvalue()).decode()
        except Exception as e:
            logger.warning(f"ELA thermal heatmap failed: {e}")

        # ── Noise map: Gaussian high-pass ─────────────────────────────
        try:
            arr_gray = np.array(pil_img.convert("L"), dtype=np.float32)

            if cv2 is not None:
                blurred = cv2.GaussianBlur(arr_gray, (5, 5), 0)
            else:
                blurred = np.array(
                    pil_img.convert("L").filter(ImageFilter.GaussianBlur(radius=2)),
                    dtype=np.float32,
                )

            noise = np.abs(arr_gray - blurred)
            noise_amp = np.clip(noise * 7, 0, 255).astype(np.uint8)

            h, w = noise_amp.shape
            zone_means = [
                np.mean(noise_amp[zy * h // 4:(zy + 1) * h // 4, zx * w // 4:(zx + 1) * w // 4])
                for zy in range(4) for zx in range(4)
            ]
            std_zones = np.std(zone_means)
            mean_noise = np.mean(noise_amp)

            uniformity = max(0.0, 1.0 - std_zones / 15.0)
            noise_score = min(100, int(uniformity * 70 + (mean_noise / 255) * 40))

            if cv2 is not None:
                noise_colored = cv2.applyColorMap(noise_amp, cv2.COLORMAP_JET)
                noise_rgb = cv2.cvtColor(noise_colored, cv2.COLOR_BGR2RGB)
                noise_pil = Image.fromarray(noise_rgb)
            else:
                noise_pil = self._apply_jet_pil(Image.fromarray(noise_amp))

            buf3 = io.BytesIO()
            noise_pil.save(buf3, format="PNG")
            noise_b64 = base64.b64encode(buf3.getvalue()).decode()
        except Exception as e:
            logger.warning(f"Noise map failed: {e}")

        return ela_b64, ela_score, noise_b64, noise_score

    # ── Main entry point ───────────────────────────────────────────────
    def process(self, image_path: str) -> dict:
        processed = {
            "tensor_rgb": None,
            "ela_array": None,
            "base64": None,
            "ela_base64": None,       # PIL-heatmap base64 (PNG) — legacy key
            "ela_thermal_b64": None,  # JET thermal ELA heatmap (PNG)
            "noise_map_b64": None,    # JET noise uniformity map (PNG)
            "ela_score": 0,
            "noise_score": 0,
        }

        try:
            # 1. Original image base64
            processed["base64"] = self.get_base64(image_path)

            # 2. Open PIL image once
            img = Image.open(image_path).convert('RGB')

            # 3. ELA heatmap (PIL path — stored as lag-free PNG)
            ela_heatmap_img = self.generate_ela_pil(image_path)
            if ela_heatmap_img:
                buffered = io.BytesIO()
                ela_heatmap_img.save(buffered, format="PNG")
                processed["ela_base64"] = base64.b64encode(buffered.getvalue()).decode("utf-8")
                if HAS_NUMPY:
                    processed["ela_array"] = np.array(ela_heatmap_img)

            # 4. High-quality thermal heatmaps (reference-quality, numpy required)
            if HAS_NUMPY:
                ela_b64, ela_score, noise_b64, noise_score = self._compute_thermal_heatmaps(img)
                processed["ela_thermal_b64"] = ela_b64
                processed["ela_score"] = ela_score
                processed["noise_map_b64"] = noise_b64
                processed["noise_score"] = noise_score

            # 5. Standardize dimensions
            img_resized = img.resize(self.target_size)
            if HAS_NUMPY:
                processed["tensor_rgb"] = np.array(img_resized)

        except Exception as e:
            logger.error(f"Error during image preprocessing: {e}")

        return processed


preprocessor = ImagePreprocessor()
