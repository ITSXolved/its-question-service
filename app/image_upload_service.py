"""
Image Upload Service for Questions
Handles uploading images to Supabase Storage for questions and options
"""
import os
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
import mimetypes

class ImageUploadService:
    def __init__(self, supabase_client):
        """
        Initialize Image Upload Service.

        Args:
            supabase_client: Initialized Supabase client
        """
        self.supabase = supabase_client
        self.bucket_name = "question-images"  # Supabase storage bucket name

    def create_bucket_if_not_exists(self):
        """
        Check if the storage bucket exists by attempting to list files.
        Note: Bucket creation must be done manually in Supabase Dashboard.
        """
        try:
            # Try to list files in the bucket - if it works, bucket exists
            self.supabase.storage().from_(self.bucket_name).list()
            return {
                "success": True,
                "message": f"Bucket '{self.bucket_name}' exists and is accessible"
            }
        except Exception as e:
            error_msg = str(e)
            return {
                "success": False,
                "error": error_msg,
                "message": (
                    f"Bucket '{self.bucket_name}' not found or not accessible. "
                    "Please create it manually in Supabase Dashboard:\n"
                    "1. Go to Storage in Supabase Dashboard\n"
                    "2. Click 'New bucket'\n"
                    f"3. Name it '{self.bucket_name}'\n"
                    "4. Set it to 'Public' for public image access"
                )
            }

    def upload_question_image(self,
                             question_id: str,
                             image_file,
                             file_name: str) -> Dict[str, Any]:
        """
        Upload an image for a question.

        Args:
            question_id: ID of the question
            image_file: File object or bytes
            file_name: Original file name

        Returns:
            Dict with upload status and URL
        """
        try:
            # Generate unique file name
            file_ext = os.path.splitext(file_name)[1]
            unique_filename = f"questions/{question_id}/question{file_ext}"

            # Detect content type
            content_type = mimetypes.guess_type(file_name)[0] or 'image/png'

            # Upload to Supabase Storage
            result = self.supabase.storage().from_(self.bucket_name).upload(
                unique_filename,
                image_file,
                file_options={"content-type": content_type}
            )

            # Get public URL
            public_url = self.supabase.storage().from_(self.bucket_name).get_public_url(unique_filename)

            return {
                "success": True,
                "url": public_url,
                "path": unique_filename,
                "message": "Image uploaded successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to upload image: {str(e)}"
            }

    def upload_option_image(self,
                           question_id: str,
                           option_key: str,
                           image_file,
                           file_name: str) -> Dict[str, Any]:
        """
        Upload an image for a specific option.

        Args:
            question_id: ID of the question
            option_key: Option identifier (e.g., 'A', 'B', 'C', 'D' or '0', '1', '2', '3')
            image_file: File object or bytes
            file_name: Original file name

        Returns:
            Dict with upload status and URL
        """
        try:
            # Generate unique file name for option
            file_ext = os.path.splitext(file_name)[1]
            unique_filename = f"questions/{question_id}/options/option_{option_key}{file_ext}"

            # Detect content type
            content_type = mimetypes.guess_type(file_name)[0] or 'image/png'

            # Upload to Supabase Storage
            result = self.supabase.storage().from_(self.bucket_name).upload(
                unique_filename,
                image_file,
                file_options={"content-type": content_type}
            )

            # Get public URL
            public_url = self.supabase.storage().from_(self.bucket_name).get_public_url(unique_filename)

            return {
                "success": True,
                "url": public_url,
                "path": unique_filename,
                "option_key": option_key,
                "message": "Option image uploaded successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to upload option image: {str(e)}"
            }

    def upload_multiple_option_images(self,
                                     question_id: str,
                                     option_images: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Upload multiple option images at once.

        Args:
            question_id: ID of the question
            option_images: List of dicts with 'option_key', 'file', 'file_name'

        Returns:
            Dict with upload results
        """
        results = []
        for option_img in option_images:
            result = self.upload_option_image(
                question_id=question_id,
                option_key=option_img['option_key'],
                image_file=option_img['file'],
                file_name=option_img['file_name']
            )
            results.append(result)

        success_count = sum(1 for r in results if r['success'])

        return {
            "success": success_count == len(option_images),
            "total": len(option_images),
            "success_count": success_count,
            "results": results,
            "message": f"Uploaded {success_count}/{len(option_images)} option images"
        }

    def delete_question_image(self, image_path: str) -> Dict[str, Any]:
        """
        Delete an image from storage.

        Args:
            image_path: Path to the image in storage

        Returns:
            Dict with deletion status
        """
        try:
            self.supabase.storage().from_(self.bucket_name).remove([image_path])
            return {
                "success": True,
                "message": "Image deleted successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to delete image: {str(e)}"
            }

    def delete_all_question_images(self, question_id: str) -> Dict[str, Any]:
        """
        Delete all images associated with a question.

        Args:
            question_id: ID of the question

        Returns:
            Dict with deletion status
        """
        try:
            # List all files in the question folder
            files = self.supabase.storage().from_(self.bucket_name).list(f"questions/{question_id}")

            if files:
                # Delete all files
                file_paths = [f"questions/{question_id}/{f['name']}" for f in files]
                self.supabase.storage().from_(self.bucket_name).remove(file_paths)

                return {
                    "success": True,
                    "deleted_count": len(file_paths),
                    "message": f"Deleted {len(file_paths)} images"
                }
            else:
                return {
                    "success": True,
                    "deleted_count": 0,
                    "message": "No images found to delete"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to delete images: {str(e)}"
            }
