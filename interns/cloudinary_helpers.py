"""
Cloudinary helper utilities for secure payment screenshot handling.
Provides methods for generating signed URLs and uploading with error handling.
"""

import logging
import cloudinary
import cloudinary.uploader
import cloudinary.utils
from django.core.files.uploadedfile import UploadedFile
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger(__name__)


class CloudinaryHelper:
    """Helper class for Cloudinary operations with error handling and logging."""
    
    # Folder for payment screenshots
    PAYMENT_FOLDER = 'Compass_payment'
    
    @staticmethod
    def generate_signed_url(public_id: str, resource_type: str = 'image',
                           type: str = 'authenticated', expires_in: int = 3600,
                           use_extension: bool = False) -> Optional[str]:
        """
        Generate a signed URL for accessing authenticated Cloudinary resources.

        Args:
            public_id: The Cloudinary public ID of the resource
            resource_type: Type of resource (image, video, raw)
            type: Delivery type (upload, private, authenticated)
            expires_in: URL expiration time in seconds (default: 1 hour)
            use_extension: Whether to preserve file extension from public_id (default: False)

        Returns:
            Signed URL string or None if generation fails
        """
        try:
            import time
            conf = cloudinary.config()
            if not conf.cloud_name or not conf.api_key or not conf.api_secret:
                logger.error("Cloudinary configuration missing required credentials")
                return None

            # Calculate expiration timestamp
            expires_at = int(time.time()) + expires_in

            url, options = cloudinary.utils.cloudinary_url(
                public_id,
                resource_type=resource_type,
                type=type,
                sign_url=True,
                expires_at=expires_at,
                use_extension=use_extension
            )

            logger.info(f"Generated signed URL for {public_id}")
            return url

        except Exception as e:
            logger.error(f"Failed to generate signed URL for {public_id}: {str(e)}")
            return None
    
    @staticmethod
    def upload_payment_screenshot(file: UploadedFile, 
                                 public_id: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
        """
        Upload a payment screenshot to Cloudinary with authenticated access.
        
        Args:
            file: The uploaded file object
            public_id: Optional custom public ID (auto-generated if not provided)
            
        Returns:
            Tuple of (public_id, error_message) - public_id is None on failure
        """
        try:
            if not file:
                logger.error("No file provided for upload")
                return None, "No file provided"
            
            # Validate file size (max 10MB)
            if file.size > 10 * 1024 * 1024:
                logger.error(f"File size exceeds limit: {file.size} bytes")
                return None, "File size exceeds 10MB limit"
            
            # Validate file type
            allowed_types = ['image/jpeg', 'image/png', 'image/jpg', 'image/webp']
            if hasattr(file, 'content_type') and file.content_type not in allowed_types:
                logger.error(f"Invalid file type: {file.content_type}")
                return None, "Invalid file type. Only JPEG, PNG, and WebP images are allowed"
            
            upload_options = {
                'folder': CloudinaryHelper.PAYMENT_FOLDER,
                'type': 'authenticated',
                'resource_type': 'image',
                'transformation': [
                    {'quality': 'auto', 'fetch_format': 'auto'}
                ]
            }
            
            if public_id:
                upload_options['public_id'] = public_id
            
            result = cloudinary.uploader.upload(file, **upload_options)
            
            logger.info(f"Successfully uploaded payment screenshot to {result['public_id']}")
            return result['public_id'], None
            
        except cloudinary.api.Error as e:
            error_msg = f"Cloudinary API error: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error during upload: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
    
    @staticmethod
    def delete_payment_screenshot(public_id: str) -> Tuple[bool, Optional[str]]:
        """
        Delete a payment screenshot from Cloudinary.
        
        Args:
            public_id: The Cloudinary public ID of the resource to delete
            
        Returns:
            Tuple of (success, error_message) - success is False on failure
        """
        try:
            if not public_id:
                logger.error("No public_id provided for deletion")
                return False, "No public_id provided"
            
            result = cloudinary.uploader.destroy(
                public_id,
                resource_type='image',
                type='authenticated'
            )
            
            if result.get('result') == 'ok':
                logger.info(f"Successfully deleted payment screenshot: {public_id}")
                return True, None
            else:
                logger.warning(f"Deletion result for {public_id}: {result}")
                return False, f"Deletion failed: {result}"
            
        except cloudinary.api.Error as e:
            error_msg = f"Cloudinary API error during deletion: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error during deletion: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    @staticmethod
    def get_resource_info(public_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata about a Cloudinary resource.
        
        Args:
            public_id: The Cloudinary public ID of the resource
            
        Returns:
            Dictionary with resource metadata or None if retrieval fails
        """
        try:
            result = cloudinary.api.resource(
                public_id,
                resource_type='image',
                type='authenticated'
            )
            logger.info(f"Retrieved resource info for {public_id}")
            return result
            
        except cloudinary.api.Error as e:
            logger.error(f"Failed to retrieve resource info for {public_id}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving resource info: {str(e)}")
            return None


def is_admin_user(user) -> bool:
    """
    Check if a user has admin privileges for viewing payment screenshots.
    
    Args:
        user: The user object to check
        
    Returns:
        True if user is admin, False otherwise
    """
    return (
        user.is_authenticated and
        (user.is_staff or user.is_superuser or user.role == 'admin')
    )


class AdminRequiredMixin:
    """
    Mixin to ensure only admin users can access the view.
    """
    def dispatch(self, request, *args, **kwargs):
        if not is_admin_user(request.user):
            from django.contrib import messages
            messages.error(request, "You do not have permission to view payment screenshots.")
            from django.shortcuts import redirect
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
