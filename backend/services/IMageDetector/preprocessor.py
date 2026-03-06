try:
    import cv2
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

import base64
from PIL import Image, ImageChops, ImageEnhance, ImageOps
from loguru import logger
import io

class ImagePreprocessor:
    """
    Layer 3: Prepares the image for forensic analysis.
    Standardizes dimensions, generates grayscale, frequency maps, and ELA.
    """
    def __init__(self, target_size=(380, 380)):
        self.target_size = target_size

    def generate_ela_pil(self, image_path: str, quality=90) -> Image.Image:
        """
        Generates Error Level Analysis (ELA) map using pure PIL.
        Resaves image at lower quality and compares pixel differences. 
        Authentic areas have similar error levels.
        """
        try:
            original = Image.open(image_path).convert('RGB')
            # Save temporary compressed version in memory
            temp_io = io.BytesIO()
            original.save(temp_io, 'JPEG', quality=quality)
            temp_io.seek(0)
            
            compressed = Image.open(temp_io)
            # Find diff
            ela_image = ImageChops.difference(original, compressed)
            
            # Enhance brightness to see errors visually
            extrema = ela_image.getextrema()
            max_diff = max([ex[1] for ex in extrema]) if extrema else 1
            if max_diff == 0:
                max_diff = 1 # avoid division by zero
                
            scale = 255.0 / max_diff
            ela_image = ImageEnhance.Brightness(ela_image).enhance(scale)
            
            # Convert to Jet/Inferno like colormap using pure PIL (black->blue->red)
            ela_gray = ela_image.convert("L")
            # Create a heatmap: low error = dark blue, medium = yellow/orange, high = red/white
            heatmap = ImageOps.colorize(
                ela_gray, 
                black="#000033",   # Dark blue for authentic/unchanged regions
                white="#ff0000",   # Bright red for manipulated regions
                mid="#ff8800"      # Orange for suspicious regions
            )
            return heatmap
        except Exception as e:
            logger.error(f"Error generating ELA: {e}")
            return None

    def get_base64(self, image_path: str) -> str:
        """Helper to return base64 string for context/semantic pipelines."""
        try:
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception:
            return None

    def process(self, image_path: str) -> dict:
        processed = {
            "tensor_rgb": None,  # Original standardized
            "ela_array": None,   # ELA map as numpy array (if available)
            "base64": None,      # Original image base64
            "ela_base64": None   # Heatmap base64
        }
        
        try:
            # 1. Base64 original
            processed["base64"] = self.get_base64(image_path)
            
            # 2. ELA Map (Pure PIL heatmap)
            heatmap_img = self.generate_ela_pil(image_path)
            
            if heatmap_img:
                # Convert heatmap to base64 directly from PIL
                buffered = io.BytesIO()
                heatmap_img.save(buffered, format="JPEG")
                processed["ela_base64"] = base64.b64encode(buffered.getvalue()).decode("utf-8")
                
                # Provide numpy array ONLY if numpy is installed
                if HAS_NUMPY:
                    processed["ela_array"] = np.array(heatmap_img)
            
            # 3. Standardize dimensions using PIL
            img = Image.open(image_path).convert('RGB')
            img_resized = img.resize(self.target_size)
            if HAS_NUMPY:
                processed["tensor_rgb"] = np.array(img_resized)
            
        except Exception as e:
            logger.error(f"Error during image preprocessing: {e}")

        return processed

preprocessor = ImagePreprocessor()
