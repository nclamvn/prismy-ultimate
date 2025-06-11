# src/storage/storage_manager.py
import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import shutil
from datetime import datetime

from .s3_handler import S3StorageHandler, get_s3_handler

logger = logging.getLogger(__name__)

class StorageManager:
    """Manage file storage with S3 and local fallback"""
    
    def __init__(self):
        self.use_s3 = os.getenv('USE_S3_STORAGE', 'false').lower() == 'true'
        self.local_base_path = os.getenv('LOCAL_STORAGE_PATH', 'output')
        
        if self.use_s3:
            try:
                self.s3_handler = get_s3_handler()
                logger.info("Using S3 storage")
            except Exception as e:
                logger.error(f"Failed to initialize S3, falling back to local: {e}")
                self.use_s3 = False
                self.s3_handler = None
        else:
            logger.info("Using local file storage")
            self.s3_handler = None
    
    async def store_file(
        self,
        file_path: str,
        category: str = 'general',
        job_id: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Store file in S3 or locally"""
        
        if self.use_s3 and self.s3_handler:
            # Generate S3 key
            timestamp = datetime.now().strftime('%Y/%m/%d')
            filename = Path(file_path).name
            
            if job_id:
                object_key = f"{category}/{timestamp}/{job_id}/{filename}"
            else:
                object_key = f"{category}/{timestamp}/{filename}"
            
            # Upload to S3
            try:
                await self.s3_handler.upload_file_async(
                    file_path,
                    object_key,
                    metadata
                )
                
                # Generate presigned URL
                url = self.s3_handler.generate_presigned_url(
                    object_key,
                    expiration=86400  # 24 hours
                )
                
                return {
                    'storage_type': 's3',
                    'key': object_key,
                    'url': url,
                    'bucket': self.s3_handler.bucket_name,
                    'local_path': file_path  # Keep for cleanup
                }
                
            except Exception as e:
                logger.error(f"S3 upload failed, falling back to local: {e}")
                # Fall through to local storage
        
        # Local storage
        rel_path = self._organize_local_file(file_path, category, job_id)
        
        return {
            'storage_type': 'local',
            'path': rel_path,
            'absolute_path': os.path.abspath(rel_path),
            'url': f"/files/{rel_path}"  # For API serving
        }
    
    def _organize_local_file(
        self,
        file_path: str,
        category: str,
        job_id: Optional[str]
    ) -> str:
        """Organize file in local storage"""
        timestamp = datetime.now().strftime('%Y/%m/%d')
        filename = Path(file_path).name
        
        if job_id:
            dest_dir = Path(self.local_base_path) / category / timestamp / job_id
        else:
            dest_dir = Path(self.local_base_path) / category / timestamp
        
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / filename
        
        # Copy file if not already in destination
        if Path(file_path).resolve() != dest_path.resolve():
            shutil.copy2(file_path, dest_path)
        
        return str(dest_path)
    
    async def retrieve_file(
        self,
        storage_info: Dict[str, Any],
        download_path: Optional[str] = None
    ) -> str:
        """Retrieve file from storage"""
        
        if storage_info['storage_type'] == 's3' and self.s3_handler:
            # Download from S3
            return await self.s3_handler.download_file_async(
                storage_info['key'],
                download_path
            )
        else:
            # Local file
            local_path = storage_info.get('absolute_path', storage_info.get('path'))
            
            if download_path and local_path != download_path:
                shutil.copy2(local_path, download_path)
                return download_path
            
            return local_path
    
    def get_download_url(
        self,
        storage_info: Dict[str, Any],
        filename: Optional[str] = None,
        expiration: int = 3600
    ) -> str:
        """Get download URL for stored file"""
        
        if storage_info['storage_type'] == 's3' and self.s3_handler:
            # Generate new presigned URL
            return self.s3_handler.generate_presigned_url(
                storage_info['key'],
                expiration=expiration,
                download_filename=filename
            )
        else:
            # Return local file URL
            return storage_info.get('url', f"/files/{storage_info['path']}")
    
    async def cleanup_job_files(self, job_id: str):
        """Cleanup files for a job"""
        if self.use_s3 and self.s3_handler:
            # List and delete S3 files for each category
            for category in ['uploads', 'reconstructed', 'test', 'temp']:
                try:
                    # Search for files in category with job_id
                    prefix = f"{category}/"
                    files = self.s3_handler.list_files(prefix=prefix)
                    
                    # Filter files that contain job_id
                    for file_info in files:
                        if job_id in file_info['key']:
                            try:
                                self.s3_handler.delete_file(file_info['key'])
                                logger.info(f"Deleted S3 file: {file_info['key']}")
                            except Exception as e:
                                logger.error(f"Failed to delete {file_info['key']}: {e}")
                except Exception as e:
                    logger.error(f"Error listing files in {category}: {e}")
        
        # Also cleanup local files
        for category in ['uploads', 'reconstructed', 'temp']:
            pattern = Path(self.local_base_path) / category / '**' / job_id
            for path in Path(self.local_base_path).glob(f"{category}/**/*{job_id}*"):
                if path.is_dir() and job_id in path.name:
                    shutil.rmtree(path)
                    logger.info(f"Cleaned up local directory: {path}")
                elif path.is_file() and job_id in path.stem:
                    path.unlink()
                    logger.info(f"Cleaned up local file: {path}")

# Global instance
_storage_manager = None

def get_storage_manager() -> StorageManager:
    """Get or create storage manager instance"""
    global _storage_manager
    if _storage_manager is None:
        _storage_manager = StorageManager()
    return _storage_manager
