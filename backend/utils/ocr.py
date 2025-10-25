"""
OCR (Optical Character Recognition) utilities for text extraction from images.

Supports multiple OCR backends:
- Tesseract OCR (local, free)
- EasyOCR (deep learning-based, better accuracy)
- PaddleOCR (fast and accurate)

Priority: EasyOCR > PaddleOCR > Tesseract
"""

import logging
import os
from typing import Optional, Dict, List, Any
from pathlib import Path
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class OCRService:
    """OCR service with multiple backend support."""

    def __init__(self, backend: str = 'auto'):
        """
        Initialize OCR service.

        Args:
            backend: OCR backend to use ('auto', 'easyocr', 'paddle', 'tesseract')
        """
        self.backend = backend
        self.ocr_engine = None
        self._initialized = False

    def _ensure_initialized(self):
        """Ensure OCR engine is initialized."""
        if not self._initialized:
            self._initialize_ocr_engine()
            self._initialized = True

    def _initialize_ocr_engine(self):
        """Initialize the OCR engine based on backend preference."""
        if self.backend == 'auto':
            # Try engines in order of preference
            if self._try_initialize_easyocr():
                return
            elif self._try_initialize_paddleocr():
                return
            elif self._try_initialize_tesseract():
                return
            else:
                logger.warning("No OCR backend available. Install one of: easyocr, paddleocr, pytesseract")
                self.backend = 'none'
        elif self.backend == 'easyocr':
            self._try_initialize_easyocr()
        elif self.backend == 'paddle':
            self._try_initialize_paddleocr()
        elif self.backend == 'tesseract':
            self._try_initialize_tesseract()

    def _try_initialize_easyocr(self) -> bool:
        """Try to initialize EasyOCR."""
        try:
            import easyocr
            self.ocr_engine = easyocr.Reader(['en'], gpu=self._has_gpu())
            self.backend = 'easyocr'
            logger.info("OCR initialized with EasyOCR backend")
            return True
        except ImportError:
            logger.debug("EasyOCR not available")
            return False
        except Exception as e:
            logger.debug(f"Failed to initialize EasyOCR: {e}")
            return False

    def _try_initialize_paddleocr(self) -> bool:
        """Try to initialize PaddleOCR."""
        try:
            from paddleocr import PaddleOCR
            self.ocr_engine = PaddleOCR(
                lang='en',
                use_gpu=self._has_gpu(),
                show_log=False
            )
            self.backend = 'paddle'
            logger.info("OCR initialized with PaddleOCR backend")
            return True
        except ImportError:
            logger.debug("PaddleOCR not available")
            return False
        except Exception as e:
            logger.debug(f"Failed to initialize PaddleOCR: {e}")
            return False

    def _try_initialize_tesseract(self) -> bool:
        """Try to initialize Tesseract OCR."""
        try:
            import pytesseract
            # Test if tesseract is installed
            pytesseract.get_tesseract_version()
            self.ocr_engine = pytesseract
            self.backend = 'tesseract'
            logger.info("OCR initialized with Tesseract backend")
            return True
        except ImportError:
            logger.debug("pytesseract not available")
            return False
        except Exception as e:
            logger.debug(f"Failed to initialize Tesseract: {e}")
            return False

    def _has_gpu(self) -> bool:
        """Check if GPU is available."""
        try:
            import torch
            return torch.cuda.is_available()
        except:
            return False

    def extract_text(self, image_path: str) -> Optional[str]:
        """
        Extract text from an image file.

        Args:
            image_path: Path to the image file

        Returns:
            Extracted text or None if extraction fails
        """
        self._ensure_initialized()

        if self.backend == 'none':
            logger.warning("No OCR backend available")
            return None

        try:
            if not os.path.exists(image_path):
                logger.error(f"Image file not found: {image_path}")
                return None

            if self.backend == 'easyocr':
                return self._extract_with_easyocr(image_path)
            elif self.backend == 'paddle':
                return self._extract_with_paddleocr(image_path)
            elif self.backend == 'tesseract':
                return self._extract_with_tesseract(image_path)

        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}")
            return None

    def extract_text_detailed(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        Extract text with detailed information (bounding boxes, confidence).

        Args:
            image_path: Path to the image file

        Returns:
            Dictionary containing text and detailed results
        """
        self._ensure_initialized()

        if self.backend == 'none':
            return None

        try:
            if not os.path.exists(image_path):
                return None

            if self.backend == 'easyocr':
                return self._extract_detailed_easyocr(image_path)
            elif self.backend == 'paddle':
                return self._extract_detailed_paddleocr(image_path)
            elif self.backend == 'tesseract':
                return self._extract_detailed_tesseract(image_path)

        except Exception as e:
            logger.error(f"Detailed OCR extraction failed: {str(e)}")
            return None

    def _extract_with_easyocr(self, image_path: str) -> str:
        """Extract text using EasyOCR."""
        results = self.ocr_engine.readtext(image_path)
        # results is list of (bbox, text, confidence)
        texts = [text for (bbox, text, conf) in results if conf > 0.5]
        return ' '.join(texts) if texts else None

    def _extract_with_paddleocr(self, image_path: str) -> str:
        """Extract text using PaddleOCR."""
        results = self.ocr_engine.ocr(image_path, cls=True)
        if not results or not results[0]:
            return None

        texts = []
        for line in results[0]:
            if line and len(line) >= 2:
                text = line[1][0]  # Extract text from result
                conf = line[1][1]  # Extract confidence
                if conf > 0.5:
                    texts.append(text)

        return ' '.join(texts) if texts else None

    def _extract_with_tesseract(self, image_path: str) -> str:
        """Extract text using Tesseract."""
        image = Image.open(image_path)
        text = self.ocr_engine.image_to_string(image, lang='eng')
        return text.strip() if text and text.strip() else None

    def _extract_detailed_easyocr(self, image_path: str) -> Dict[str, Any]:
        """Extract detailed text information using EasyOCR."""
        results = self.ocr_engine.readtext(image_path)

        detailed_results = []
        all_text = []

        for bbox, text, confidence in results:
            if confidence > 0.3:  # Lower threshold for detailed results
                detailed_results.append({
                    'text': text,
                    'confidence': float(confidence),
                    'bounding_box': bbox
                })
                if confidence > 0.5:
                    all_text.append(text)

        return {
            'text': ' '.join(all_text) if all_text else None,
            'detailed_results': detailed_results,
            'backend': 'easyocr',
            'total_detections': len(results)
        }

    def _extract_detailed_paddleocr(self, image_path: str) -> Dict[str, Any]:
        """Extract detailed text information using PaddleOCR."""
        results = self.ocr_engine.ocr(image_path, cls=True)

        if not results or not results[0]:
            return {
                'text': None,
                'detailed_results': [],
                'backend': 'paddle',
                'total_detections': 0
            }

        detailed_results = []
        all_text = []

        for line in results[0]:
            if line and len(line) >= 2:
                bbox = line[0]
                text = line[1][0]
                confidence = line[1][1]

                if confidence > 0.3:
                    detailed_results.append({
                        'text': text,
                        'confidence': float(confidence),
                        'bounding_box': bbox
                    })
                    if confidence > 0.5:
                        all_text.append(text)

        return {
            'text': ' '.join(all_text) if all_text else None,
            'detailed_results': detailed_results,
            'backend': 'paddle',
            'total_detections': len(results[0])
        }

    def _extract_detailed_tesseract(self, image_path: str) -> Dict[str, Any]:
        """Extract detailed text information using Tesseract."""
        import pytesseract

        image = Image.open(image_path)

        # Get detailed data
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

        detailed_results = []
        all_text = []

        n_boxes = len(data['text'])
        for i in range(n_boxes):
            text = data['text'][i].strip()
            conf = int(data['conf'][i])

            if text and conf > 30:  # Tesseract confidence is 0-100
                bbox = [
                    data['left'][i],
                    data['top'][i],
                    data['left'][i] + data['width'][i],
                    data['top'][i] + data['height'][i]
                ]

                detailed_results.append({
                    'text': text,
                    'confidence': conf / 100.0,  # Normalize to 0-1
                    'bounding_box': bbox
                })

                if conf > 50:
                    all_text.append(text)

        return {
            'text': ' '.join(all_text) if all_text else None,
            'detailed_results': detailed_results,
            'backend': 'tesseract',
            'total_detections': len(detailed_results)
        }

    def health_check(self) -> Dict[str, Any]:
        """Check OCR service health."""
        self._ensure_initialized()

        return {
            'ocr_available': self.backend != 'none',
            'backend': self.backend,
            'initialized': self._initialized
        }


# Global OCR service instance
_ocr_service = None


def get_ocr_service(backend: str = 'auto') -> OCRService:
    """
    Get or create global OCR service instance.

    Args:
        backend: OCR backend to use

    Returns:
        OCRService instance
    """
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService(backend=backend)
    return _ocr_service


def extract_text_from_image(image_path: str) -> Optional[str]:
    """
    Convenience function to extract text from an image.

    Args:
        image_path: Path to the image file

    Returns:
        Extracted text or None
    """
    ocr_service = get_ocr_service()
    return ocr_service.extract_text(image_path)


def extract_text_detailed(image_path: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to extract detailed text information.

    Args:
        image_path: Path to the image file

    Returns:
        Dictionary with text and detailed results
    """
    ocr_service = get_ocr_service()
    return ocr_service.extract_text_detailed(image_path)
