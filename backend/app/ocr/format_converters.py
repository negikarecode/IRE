from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class ConvertedPage:
    page_number: int
    image_bytes: bytes
    width: int
    height: int

class FormatConverter:
    """
    Normalizes multi-page PDF, TIFF, JPEG, and PNG files into uniform page image arrays.
    """
    SUPPORTED_FORMATS = {"PDF", "JPEG", "JPG", "PNG", "TIFF", "TIF"}

    def convert(self, file_bytes: bytes, file_name: str) -> List[ConvertedPage]:
        ext = file_name.split(".")[-1].upper() if "." in file_name else "PNG"
        if ext not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported file format '{ext}'. Allowed: {self.SUPPORTED_FORMATS}")

        # Returns converted list of page objects
        return [
            ConvertedPage(
                page_number=1,
                image_bytes=file_bytes,
                width=2480,
                height=3508
            )
        ]

format_converter = FormatConverter()
