from typing import List, Dict

# Try to import PaddleOCR, but make it optional for local development
try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
    PaddleOCR = None

# Simple cache for OCR engines
_ocr_cache = {}


def get_ocr(lang: str = "en"):
    if not PADDLEOCR_AVAILABLE:
        raise ImportError("PaddleOCR is not installed. Install with: pip install paddleocr")
    if lang not in _ocr_cache:
        _ocr_cache[lang] = PaddleOCR(
            use_angle_cls=True,
            lang=lang,
            use_gpu=False,  # Cloud Run CPU-only
        )
    return _ocr_cache[lang]


def run_ocr_on_image_bytes(image_bytes: bytes, lang: str = "en") -> List[Dict]:
    if not PADDLEOCR_AVAILABLE:
        raise ImportError("PaddleOCR is not installed. Install with: pip install paddleocr")
    ocr = get_ocr(lang)
    result = ocr.ocr(image_bytes, cls=True)
    output = []
    if result and result[0]:
        for line in result[0]:
            box, (text, conf) = line
            output.append(
                {
                    "bbox": box,
                    "text": text,
                    "confidence": float(conf),
                }
            )
    return output

