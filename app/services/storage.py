"""
Storage Service - Handles file storage for local and S3

Provides a unified interface for storing files whether locally
or in S3, determined by environment configuration.
"""
import os
from pathlib import Path
from flask import current_app


class StorageService:
    """
    Unified storage service supporting local filesystem and S3.

    Configuration via environment variables:
    - STATIC_STORAGE_URL: If set (non-empty), enables S3 mode
    - AWS_ACCESS_KEY_ID: AWS credentials
    - AWS_SECRET_ACCESS_KEY: AWS credentials
    - S3_BUCKET_NAME: Target bucket name
    - AWS_REGION: AWS region (default: us-east-1)
    """

    def __init__(self):
        self._s3_client = None

    @property
    def is_s3_enabled(self):
        """Check if S3 storage is enabled"""
        return bool(current_app.config.get('STATIC_STORAGE_URL'))

    @property
    def s3_client(self):
        """Lazy-load S3 client"""
        if self._s3_client is None and self.is_s3_enabled:
            import boto3
            self._s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_REGION', 'us-east-1')
            )
        return self._s3_client

    @property
    def bucket_name(self):
        """Get S3 bucket name from environment"""
        return os.getenv('S3_BUCKET_NAME')

    def save_file(self, file, relative_path, content_type=None):
        """
        Save a file to storage (local or S3).

        Args:
            file: File object (from request.files)
            relative_path: Path relative to static root (e.g., 'images/artists/Monet/painting.jpg')
            content_type: Optional MIME type for S3

        Returns:
            dict: {'success': bool, 'path': str, 'error': str}
        """
        if self.is_s3_enabled:
            return self._save_to_s3(file, relative_path, content_type)
        else:
            return self._save_to_local(file, relative_path)

    def _save_to_local(self, file, relative_path):
        """Save file to local filesystem"""
        from app.utils.security import validate_file_path

        try:
            base_dir = Path(current_app.static_folder)
            full_path = base_dir / relative_path

            # Validate path (security - prevent traversal)
            if not validate_file_path(base_dir, full_path):
                return {'success': False, 'error': 'Invalid file path'}

            # Create directory if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Save file
            file.save(str(full_path))

            return {'success': True, 'path': relative_path}

        except Exception as e:
            current_app.logger.error(f"Local save failed: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _save_to_s3(self, file, relative_path, content_type=None):
        """Save file to S3"""
        try:
            # Determine content type
            if content_type is None:
                ext = Path(relative_path).suffix.lower()
                content_types = {
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                    '.gif': 'image/gif',
                    '.webp': 'image/webp',
                    '.bmp': 'image/bmp',
                }
                content_type = content_types.get(ext, 'application/octet-stream')

            # Upload to S3
            self.s3_client.upload_fileobj(
                file,
                self.bucket_name,
                relative_path,
                ExtraArgs={
                    'ContentType': content_type,
                    'CacheControl': 'max-age=31536000',  # 1 year cache
                }
            )

            return {'success': True, 'path': relative_path}

        except Exception as e:
            current_app.logger.error(f"S3 upload failed: {str(e)}")
            return {'success': False, 'error': str(e)}

    def delete_file(self, relative_path):
        """
        Delete a file from storage.

        Args:
            relative_path: Path relative to static root

        Returns:
            dict: {'success': bool, 'error': str}
        """
        if self.is_s3_enabled:
            return self._delete_from_s3(relative_path)
        else:
            return self._delete_from_local(relative_path)

    def _delete_from_local(self, relative_path):
        """Delete file from local filesystem"""
        try:
            base_dir = Path(current_app.static_folder)
            full_path = base_dir / relative_path

            if full_path.exists():
                full_path.unlink()

            return {'success': True}

        except Exception as e:
            current_app.logger.error(f"Local delete failed: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _delete_from_s3(self, relative_path):
        """Delete file from S3"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=relative_path
            )
            return {'success': True}

        except Exception as e:
            current_app.logger.error(f"S3 delete failed: {str(e)}")
            return {'success': False, 'error': str(e)}

    def file_exists(self, relative_path):
        """Check if a file exists in storage"""
        if self.is_s3_enabled:
            try:
                self.s3_client.head_object(
                    Bucket=self.bucket_name,
                    Key=relative_path
                )
                return True
            except Exception:
                return False
        else:
            base_dir = Path(current_app.static_folder)
            return (base_dir / relative_path).exists()


# Global instance
storage = StorageService()
