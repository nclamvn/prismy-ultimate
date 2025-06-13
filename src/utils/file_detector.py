# src/utils/file_detector.py
import os
import zipfile
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class FileTypeDetector:
    """Phát hiện chính xác loại file, không chỉ dựa vào phần mở rộng"""
    
    @staticmethod
    def detect_file_type(file_path: str) -> str:
        """
        Phát hiện loại file thực tế
        
        Args:
            file_path: Đường dẫn đến file
            
        Returns:
            Loại file: 'pdf', 'docx', 'txt', 'unknown'
        """
        try:
            # Kiểm tra file có tồn tại không
            if not os.path.exists(file_path):
                logger.error(f"File không tồn tại: {file_path}")
                return 'unknown'
            
            # Lấy phần mở rộng (dự phòng)
            file_ext = Path(file_path).suffix.lower()
            logger.info(f"Phần mở rộng file: {file_ext}")
            
            # Phương pháp phát hiện thủ công
            if FileTypeDetector._is_pdf(file_path):
                return 'pdf'
            elif FileTypeDetector._is_docx(file_path):
                return 'docx'
            elif FileTypeDetector._is_text(file_path):
                return 'txt'
            
            # Dự phòng dựa vào phần mở rộng
            if file_ext in ['.pdf']:
                return 'pdf'
            elif file_ext in ['.docx']:
                return 'docx'
            elif file_ext in ['.txt', '.md']:
                return 'txt'
            
            logger.warning(f"Không nhận diện được loại file: {file_path}")
            return 'unknown'
            
        except Exception as e:
            logger.error(f"Lỗi phát hiện loại file: {e}")
            return 'unknown'
    
    @staticmethod
    def _is_pdf(file_path: str) -> bool:
        """Kiểm tra xem file có phải PDF bằng cách đọc header"""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(8)
                is_pdf = header.startswith(b'%PDF-')
                logger.info(f"Kiểm tra PDF: {is_pdf}")
                return is_pdf
        except Exception as e:
            logger.error(f"Lỗi kiểm tra PDF: {e}")
            return False
    
    @staticmethod
    def _is_docx(file_path: str) -> bool:
        """Kiểm tra xem file có phải DOCX bằng cách kiểm tra cấu trúc ZIP"""
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                # Kiểm tra các file đặc trưng của DOCX
                contents = zip_file.namelist()
                is_docx = ('word/document.xml' in contents and 
                          '[Content_Types].xml' in contents)
                logger.info(f"Kiểm tra DOCX: {is_docx}")
                return is_docx
        except Exception as e:
            logger.error(f"Lỗi kiểm tra DOCX: {e}")
            return False
    
    @staticmethod
    def _is_text(file_path: str) -> bool:
        """Kiểm tra xem file có phải text bằng cách thử đọc UTF-8"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read(1024)  # Thử đọc 1KB đầu
            logger.info("Kiểm tra TEXT: True")
            return True
        except Exception as e:
            logger.error(f"Lỗi kiểm tra TEXT: {e}")
            return False

def get_appropriate_extractor(file_path: str):
    """Lấy bộ trích xuất phù hợp dựa trên loại file"""
    file_type = FileTypeDetector.detect_file_type(file_path)
    logger.info(f"Loại file được phát hiện: {file_type}")
    
    if file_type == 'pdf':
        from src.processors.pdf_extractor import PDFExtractor
        return PDFExtractor()
    elif file_type == 'docx':
        from src.processors.docx_extractor import DocxExtractor
        return DocxExtractor()
    elif file_type == 'txt':
        from src.processors.text_extractor import TextExtractor
        return TextExtractor()
    else:
        raise ValueError(f"Loại file không được hỗ trợ: {file_type} cho file: {file_path}")