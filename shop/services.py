"""
Supabase Storage Service for Medicine Images
"""
import os
from django.core.files.base import ContentFile
from supabase import create_client

def get_supabase_client():
    """Initialize Supabase client"""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    return create_client(supabase_url, supabase_key)


def upload_medicine_image(image_file, medicine_id):
    """
    Upload medicine image to Supabase Storage
    
    Args:
        image_file: InMemoryUploadedFile from form
        medicine_id: Medicine object ID or name
    
    Returns:
        Public URL of uploaded image or None if failed
    """
    try:
        supabase = get_supabase_client()
        
        # Generate unique file name
        file_name = f"medicines/{medicine_id}_{image_file.name}"
        file_content = image_file.read()
        
        # Upload to Supabase Storage bucket 'medicines'
        response = supabase.storage.from_('medicines').upload(
            path=file_name,
            file=file_content,
            file_options={"content-type": image_file.content_type}
        )
        
        # Get public URL
        public_url = supabase.storage.from_('medicines').get_public_url(file_name)
        return public_url
        
    except Exception as e:
        print(f"Error uploading image to Supabase: {str(e)}")
        return None


def delete_medicine_image(image_url):
    """
    Delete medicine image from Supabase Storage
    
    Args:
        image_url: Full public URL of the image
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if not image_url:
            return True
            
        supabase = get_supabase_client()
        
        # Extract file path from URL
        # URL format: https://xxx.supabase.co/storage/v1/object/public/medicines/medicines/...
        file_path = image_url.split('/medicines/')[-1]
        if not file_path:
            return True
        
        # Delete from Supabase Storage
        supabase.storage.from_('medicines').remove([f'medicines/{file_path}'])
        return True
        
    except Exception as e:
        print(f"Error deleting image from Supabase: {str(e)}")
        return False


def update_medicine_image(medicine, new_image_file):
    """
    Update medicine image: delete old one and upload new one
    
    Args:
        medicine: Medicine object
        new_image_file: New image file
    
    Returns:
        New public URL or None if failed
    """
    # Delete old image if exists
    if medicine.image:
        delete_medicine_image(medicine.image)
    
    # Upload new image
    return upload_medicine_image(new_image_file, medicine.id)
