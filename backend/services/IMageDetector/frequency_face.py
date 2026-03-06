from loguru import logger
from PIL import Image, ImageFilter, ImageStat
import math

try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False


def _pil_frequency_heuristic(image_path: str) -> dict:
    """
    Pure-PIL frequency analysis fallback.
    Estimates high-frequency energy by comparing original vs blurred image.
    AI-generated images (diffusion/GAN) tend to have:
    - Suspiciously smooth gradients in backgrounds
    - OR unnatural sharpness artifacts at edges
    Returns score_frequency (0=fake, 100=authentic) and details list.
    """
    details = []
    try:
        img = Image.open(image_path).convert("L")
        orig_stat = ImageStat.Stat(img)

        # Heavy blur approximates low-pass filter
        blurred = img.filter(ImageFilter.GaussianBlur(radius=3))
        blur_stat = ImageStat.Stat(blurred)

        # High-frequency = what's lost in blur
        hf_energy = abs(orig_stat.stddev[0] - blur_stat.stddev[0])

        # Sharpness via Laplacian approximation (edge filter variance)
        edges = img.filter(ImageFilter.FIND_EDGES)
        edge_stat = ImageStat.Stat(edges)
        edge_variance = edge_stat.stddev[0]

        # Real images: hf_energy typically 5-25+, edge_variance 8-30+
        # AI images: often hf_energy < 3 (over-smooth) or edge_variance very uniform
        if hf_energy < 2.0:
            score = 22.0
            details.append(
                f"Very low high-frequency energy (HFE={hf_energy:.2f}). "
                "Consistent with diffusion model smoothing (Stable Diffusion / DALL-E signature)."
            )
        elif hf_energy < 5.0:
            score = 48.0
            details.append(f"Below-average high-frequency energy (HFE={hf_energy:.2f}). Mildly suspicious smoothness.")
        elif hf_energy > 25.0 and edge_variance < 3.0:
            # Unnaturally high HF but very uniform edges = GAN checkerboard artifact
            score = 32.0
            details.append(
                f"High HF energy (HFE={hf_energy:.2f}) but uniform edges (var={edge_variance:.2f}). "
                "Matches GAN checkerboard artifact pattern."
            )
        else:
            score = 82.0

        return {"score_frequency": max(0.0, min(100.0, score)), "details": details}

    except Exception as e:
        logger.error(f"PIL frequency heuristic failed: {e}")
        return {"score_frequency": 50.0, "details": ["Frequency analysis encountered an error."]}


def _pil_face_geometry_heuristic(image_path: str) -> dict:
    """
    Pure-PIL face geometry fallback.
    Checks for unnatural color banding and symmetry in central region
    (where faces typically appear) as a proxy for AI face generation.
    Returns score_pps (0=fake, 100=authentic) and details list.
    """
    details = []
    try:
        img = Image.open(image_path).convert("RGB")
        w, h = img.size

        # Crop central region (where face is most likely)
        cx, cy = w // 2, h // 2
        face_region_size = min(w, h) // 3
        left   = max(0, cx - face_region_size)
        top    = max(0, cy - face_region_size)
        right  = min(w, cx + face_region_size)
        bottom = min(h, cy + face_region_size)
        face_crop = img.crop((left, top, right, bottom))

        stat = ImageStat.Stat(face_crop)
        r_std, g_std, b_std = stat.stddev[:3]
        r_mean, g_mean, b_mean = stat.mean[:3]

        # AI portrait images tend to have very smooth skin tones in face region
        # (low std in R and G channels specifically)
        avg_std = (r_std + g_std + b_std) / 3.0

        # Check left vs right half symmetry (AI face synthesis often too symmetric)
        left_half  = img.crop((0, 0, w // 2, h))
        right_half = img.crop((w // 2, 0, w, h)).transpose(Image.FLIP_LEFT_RIGHT)
        # Resize to same size for comparison
        rh_resized = right_half.resize(left_half.size, Image.LANCZOS)
        lh_stat = ImageStat.Stat(left_half)
        rh_stat = ImageStat.Stat(rh_resized)
        symmetry_diff = abs(lh_stat.mean[0] - rh_stat.mean[0])

        score = 75.0  # Start neutral

        if avg_std < 12.0:
            score -= 35.0
            details.append(
                f"Face region very smooth (avg color std={avg_std:.1f}). "
                "AI-generated skin tones are characteristically over-smooth."
            )
        elif avg_std < 20.0:
            score -= 15.0
            details.append(f"Face region moderately smooth (avg color std={avg_std:.1f}).")

        if symmetry_diff < 1.5:
            score -= 20.0
            details.append(
                f"Image appears unnaturally symmetric (L/R brightness diff={symmetry_diff:.2f}). "
                "AI portrait generators produce near-perfect bilateral symmetry."
            )

        if not details:
            details.append(f"Face region: natural color variation (std={avg_std:.1f}) and normal symmetry.")

        return {"score_pps": max(0.0, min(100.0, score)), "details": details}

    except Exception as e:
        logger.error(f"PIL face geometry heuristic failed: {e}")
        return {"score_pps": 50.0, "details": ["Face geometry analysis encountered an error."]}


class FrequencyAnalyzer:
    """
    Layer 6: Detects GAN artifacts in the frequency domain using 2D FFT.
    Falls back to PIL-based frequency heuristics when OpenCV/NumPy unavailable.
    Provides Frequency Score (0=fake, 100=authentic).
    """
    def __init__(self):
        pass

    def analyze(self, image_path: str) -> dict:
        if not HAS_CV2:
            return _pil_frequency_heuristic(image_path)

        result = {
            "score_frequency": 50.0,
            "details": []
        }

        try:
            image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if image is None:
                raise ValueError("Could not read grayscale for FrequencyAnalyzer")

            f_transform = np.fft.fft2(image)
            f_shift = np.fft.fftshift(f_transform)
            magnitude_spectrum = 20 * np.log(np.abs(f_shift) + 1e-8)

            rows, cols = image.shape
            crow, ccol = rows // 2, cols // 2
            mask_size = 30
            magnitude_spectrum[crow - mask_size:crow + mask_size, ccol - mask_size:ccol + mask_size] = 0

            high_freq_energy = np.mean(magnitude_spectrum[magnitude_spectrum > 0])

            if high_freq_energy > 230:
                result["score_frequency"] = 25.0
                result["details"].append(
                    f"Abnormal high-frequency spectrum (Energy={high_freq_energy:.1f}). "
                    "Possible GAN checkerboard artifact or upscaling artifact."
                )
            elif high_freq_energy < 150:
                result["score_frequency"] = 35.0
                result["details"].append(
                    f"Unusually low high-frequency spectrum (Energy={high_freq_energy:.1f}). "
                    "Consistent with diffusion model over-smoothing."
                )
            else:
                result["score_frequency"] = 85.0

        except Exception as e:
            logger.error(f"Error in frequency analysis: {e}")
            result["score_frequency"] = 50.0

        return result


class FaceGeometryAnalyzer:
    """
    Layer 5: Checks biological facial proportions.
    Falls back to PIL-based symmetry and skin-tone analysis when MediaPipe unavailable.
    Provides Physiological Pattern Score (PPS) (0=fake, 100=authentic).
    """
    def __init__(self):
        self.face_mesh = None
        try:
            import mediapipe as mp
            self.mp = mp
            self.mp_face_mesh = mp.solutions.face_mesh
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5
            )
        except Exception as e:
            logger.warning(f"MediaPipe init failed or not installed: {e}")

    def analyze(self, image_path: str) -> dict:
        if not self.face_mesh or not HAS_CV2:
            # Use pure PIL heuristic
            return _pil_face_geometry_heuristic(image_path)

        result = {
            "score_pps": 50.0,
            "details": []
        }

        try:
            import cv2 as _cv2
            image = _cv2.imread(image_path)
            if image is None:
                raise ValueError("Could not read image for FaceGeometryAnalyzer")

            image_rgb = _cv2.cvtColor(image, _cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(image_rgb)

            if not results.multi_face_landmarks:
                result["score_pps"] = 70.0
                result["details"].append("No faces detected; geometry check skipped.")
                return result

            landmarks = results.multi_face_landmarks[0].landmark
            nose_tip       = landmarks[1]
            left_eye_center  = landmarks[159]
            right_eye_center = landmarks[386]

            def get_dist(p1, p2):
                return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)

            dist_left  = get_dist(nose_tip, left_eye_center)
            dist_right = get_dist(nose_tip, right_eye_center)
            symmetry_ratio = min(dist_left, dist_right) / (max(dist_left, dist_right) + 1e-6)

            if symmetry_ratio < 0.70:
                result["score_pps"] = 20.0
                result["details"].append(f"Highly abnormal facial symmetry (ratio={symmetry_ratio:.2f}).")
            elif symmetry_ratio < 0.85:
                result["score_pps"] = 55.0
                result["details"].append(f"Suspicious facial symmetry (ratio={symmetry_ratio:.2f}).")
            else:
                result["score_pps"] = 90.0
                result["details"].append(f"Facial geometry within natural range (symmetry={symmetry_ratio:.2f}).")

        except Exception as e:
            logger.error(f"Error in face geometry analysis: {e}")
            result["score_pps"] = 50.0

        return result


# Module-level singletons
frequency_analyzer = FrequencyAnalyzer()
face_geometry = FaceGeometryAnalyzer()
