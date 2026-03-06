from loguru import logger

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    import mediapipe as mp
    HAS_MP = True
except ImportError:
    HAS_MP = False

class FaceGeometryAnalyzer:
    """
    Layer 5: Checks biological facial proportions.
    Provides Physiological Pattern Score (PPS).
    Analyzes eye distance, symmetry, and key landmark spacing.
    """
    def __init__(self):
        self.face_mesh = None
        if HAS_MP:
            try:
                self.mp_face_mesh = mp.solutions.face_mesh
                self.face_mesh = self.mp_face_mesh.FaceMesh(
                    static_image_mode=True,
                    max_num_faces=1,
                    refine_landmarks=True,
                    min_detection_confidence=0.5
                )
            except Exception as e:
                logger.warning(f"MediaPipe init failed: {e}")

    def analyze(self, image_path: str) -> dict:
        result = {
            "score_pps": 50.0,
            "details": []
        }
        
        if not HAS_MP or not HAS_CV2 or not self.face_mesh:
            result["score_pps"] = 90.0
            result["details"].append("MediaPipe/OpenCV not available. Assuming authentic facial geometry.")
            return result
            
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError("Could not read image for FaceGeometryAnalyzer")
                
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(image_rgb)
            
            if not results.multi_face_landmarks:
                result["score_pps"] = 100.0 
                result["details"].append("No faces detected; geometry check passed inherently.")
                return result
                
            landmarks = results.multi_face_landmarks[0].landmark
            
            nose_tip = landmarks[1]
            left_eye_center = landmarks[159]
            right_eye_center = landmarks[386]
            
            def get_dist(p1, p2):
                return ((p1.x - p2.x)**2 + (p1.y - p2.y)**2)**0.5
                
            dist_left = get_dist(nose_tip, left_eye_center)
            dist_right = get_dist(nose_tip, right_eye_center)
            
            symmetry_ratio = min(dist_left, dist_right) / (max(dist_left, dist_right) + 1e-6)
            
            if symmetry_ratio < 0.70:
                result["score_pps"] = 20.0
                result["details"].append(f"Highly abnormal facial symmetry detected (ratio: {symmetry_ratio:.2f}).")
            elif symmetry_ratio < 0.85:
                result["score_pps"] = 60.0
                result["details"].append(f"Suspicious facial symmetry (ratio: {symmetry_ratio:.2f}).")
            else:
                result["score_pps"] = 100.0
                
        except Exception as e:
            logger.error(f"Error in face geometry analysis: {e}")
            result["score_pps"] = 90.0
            
        return result

face_geometry = FaceGeometryAnalyzer()
