# src/storage/s3_handler.py
import os
import logging
from typing import Optional, BinaryIO, Dict, Any
import boto3
from botocore.exceptions import ClientError
import aioboto3
from pathlib import Path
import uuid
from datetime import datetime, timedelta
import mimetypes

logger = logging.getLogger(__name__)

class S3StorageHandler:
    """Handle file storage in S3 or MinIO"""
    
    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        bucket_name: Optional[str] = None,
        region: str = 'us-east-1',
        use_ssl: bool = True
    ):
        # Get from env if not provided
        self.endpoint_url = endpoint_url or os.getenv('S3_ENDPOINT_URL')
        self.access_key = access_key or os.getenv('S3_ACCESS_KEY', os.getenv('AWS_ACCESS_KEY_ID'))
        self.secret_key = secret_key or os.getenv('S3_SECRET_KEY', os.getenv('AWS_SECRET_ACCESS_KEY'))
        self.bucket_name = bucket_name or os.getenv('S3_BUCKET_NAME', 'prismy-storage')
        self.region = region or os.getenv('S3_REGION', 'us-east-1')
        self.use_ssl = use_ssl
        
        # Create clients
        self._create_clients()
        
    def _create_clients(self):
        """Create S3 clients"""
        # Configuration
        config = {
            'region_name': self.region,
            'aws_access_key_id': self.access_key,
            'aws_secret_access_key': self.secret_key
        }
        
        if self.endpoint_url:
            config['endpoint_url'] = self.endpoint_url
            config['use_ssl'] = self.use_ssl
        
        # Sync client
        self.s3_client = boto3.client('s3', **config)
        
        # Async session for aioboto3
        self.session = aioboto3.Session(
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region
        )
        
        logger.info(f"S3 storage initialized with bucket: {self.bucket_name}")
    
    def ensure_bucket_exists(self):
        """Ensure the bucket exists, create if not"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Bucket {self.bucket_name} exists")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                # Create bucket
                try:
                    if self.region == 'us-east-1':
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': self.region}
                        )
                    logger.info(f"Created bucket {self.bucket_name}")
                except Exception as e:
                    logger.error(f"Failed to create bucket: {e}")
                    raise
            else:
                logger.error(f"Error checking bucket: {e}")
                raise
    
    async def upload_file_async(
        self,
        file_path: str,
        object_key: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """Upload file to S3 asynchronously"""
        if not object_key:
            # Generate key based on file
            file_name = Path(file_path).name
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            object_key = f"uploads/{timestamp}/{file_name}"
        
        # Detect content type
        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = 'application/octet-stream'
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
        metadata['upload_timestamp'] = datetime.now().isoformat()
        metadata['original_filename'] = Path(file_path).name
        
        try:
            async with self.session.client(
                's3',
                endpoint_url=self.endpoint_url,
                use_ssl=self.use_ssl
            ) as s3:
                with open(file_path, 'rb') as f:
                    await s3.upload_fileobj(
                        f,
                        self.bucket_name,
                        object_key,
                        ExtraArgs={
                            'ContentType': content_type,
                            'Metadata': metadata
                        }
                    )
            
            logger.info(f"Uploaded {file_path} to s3://{self.bucket_name}/{object_key}")
            return object_key
            
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            raise
    
    def upload_file_sync(
        self,
        file_path: str,
        object_key: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """Upload file to S3 synchronously"""
        if not object_key:
            # Generate key based on file
            file_name = Path(file_path).name
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            object_key = f"uploads/{timestamp}/{file_name}"
        
        # Detect content type
        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = 'application/octet-stream'
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
        metadata['upload_timestamp'] = datetime.now().isoformat()
        metadata['original_filename'] = Path(file_path).name
        
        try:
            with open(file_path, 'rb') as f:
                self.s3_client.upload_fileobj(
                    f,
                    self.bucket_name,
                    object_key,
                    ExtraArgs={
                        'ContentType': content_type,
                        'Metadata': metadata
                    }
                )
            
            logger.info(f"Uploaded {file_path} to s3://{self.bucket_name}/{object_key}")
            return object_key
            
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            raise
    
    async def download_file_async(
        self,
        object_key: str,
        download_path: Optional[str] = None
    ) -> str:
        """Download file from S3 asynchronously"""
        if not download_path:
            # Use temp directory
            download_path = f"/tmp/{Path(object_key).name}"
        
        # Ensure directory exists
        Path(download_path).parent.mkdir(parents=True, exist_ok=True)
        
        try:
            async with self.session.client(
                's3',
                endpoint_url=self.endpoint_url,
                use_ssl=self.use_ssl
            ) as s3:
                with open(download_path, 'wb') as f:
                    await s3.download_fileobj(
                        self.bucket_name,
                        object_key,
                        f
                    )
            
            logger.info(f"Downloaded s3://{self.bucket_name}/{object_key} to {download_path}")
            return download_path
            
        except Exception as e:
            logger.error(f"Failed to download file: {e}")
            raise
    
    def generate_presigned_url(
        self,
        object_key: str,
        expiration: int = 3600,
        download_filename: Optional[str] = None
    ) -> str:
        """Generate presigned URL for download"""
        try:
            params = {
                'Bucket': self.bucket_name,
                'Key': object_key
            }
            
            if download_filename:
                params['ResponseContentDisposition'] = f'attachment; filename="{download_filename}"'
            
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params=params,
                ExpiresIn=expiration
            )
            
            logger.info(f"Generated presigned URL for {object_key}")
            return url
            
        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise
    
    def delete_file(self, object_key: str):
        """Delete file from S3"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            logger.info(f"Deleted s3://{self.bucket_name}/{object_key}")
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            raise
    
    def list_files(self, prefix: str = '', max_keys: int = 1000) -> list:
        """List files in S3 bucket"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'etag': obj['ETag']
                })
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            raise
    
    def get_file_info(self, object_key: str) -> Dict[str, Any]:
        """Get file metadata"""
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            
            return {
                'size': response['ContentLength'],
                'content_type': response.get('ContentType'),
                'last_modified': response['LastModified'],
                'etag': response['ETag'],
                'metadata': response.get('Metadata', {})
            }
            
        except Exception as e:
            logger.error(f"Failed to get file info: {e}")
            raise

# Singleton instance
_s3_handler = None

def get_s3_handler() -> S3StorageHandler:
    """Get or create S3 handler instance"""
    global _s3_handler
    if _s3_handler is None:
        _s3_handler = S3StorageHandler()
        _s3_handler.ensure_bucket_exists()
    return _s3_handler
