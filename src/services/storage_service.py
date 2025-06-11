"""
File Storage Service - Simple version without aiofiles
"""
import os
import shutil
import tempfile
from typing import Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class StorageService:
    """Handle file storage operations"""
    
    def __init__(self, base_path: str = "./storage"):
        self.base_path = Path(base_path)
        self.uploads_dir = self.base_path / "uploads"
        self.outputs_dir = self.base_path / "outputs"
        self.temp_dir = self.base_path / "temp"
        
        # Create directories
        for dir_path in [self.uploads_dir, self.outputs_dir, self.temp_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
            
    async def save_upload(self, file_data: bytes, filename: str) -> str:
        """Save uploaded file - simple sync version"""
        file_path = self.uploads_dir / filename
        
        # Simple sync write
        with open(file_path, 'wb') as f:
            f.write(file_data)
            
        logger.info(f"Saved upload: {file_path}")
        return str(file_path)
        
    async def save_output(self, content: bytes, filename: str) -> str:
        """Save output file - simple sync version"""
        file_path = self.outputs_dir / filename
        
        with open(file_path, 'wb') as f:
            f.write(content)
            
        logger.info(f"Saved output: {file_path}")
        return str(file_path)
        
    def get_temp_path(self, suffix: str = "") -> str:
        """Get temporary file path"""
        with tempfile.NamedTemporaryFile(
            dir=self.temp_dir,
            suffix=suffix,
            delete=False
        ) as tmp:
            return tmp.name
            
    def cleanup_temp(self):
        """Clean temporary files"""
        for file_path in self.temp_dir.glob("*"):
            try:
                if file_path.is_file():
                    file_path.unlink()
            except Exception as e:
                logger.error(f"Error cleaning {file_path}: {e}")
                
    def get_file_size(self, file_path: str) -> int:
        """Get file size in bytes"""
        return Path(file_path).stat().st_size
        
    def file_exists(self, file_path: str) -> bool:
        """Check if file exists"""
        return Path(file_path).exists()

# Singleton
storage_service = StorageService()
