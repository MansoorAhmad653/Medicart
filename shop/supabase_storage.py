import os
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from supabase import create_client, Client

@deconstructible
class SupabaseStorage(Storage):
    def __init__(self, bucket_name='medicines'):
        self.bucket_name = bucket_name
        self._supabase_url = os.getenv('SUPABASE_URL')
        self._supabase_key = os.getenv('SUPABASE_KEY')
        if self._supabase_url and self._supabase_key:
            self._client = create_client(self._supabase_url, self._supabase_key)
        else:
            self._client = None

    @property
    def client(self) -> Client:
        if self._client is None:
            raise ValueError("Supabase URL and Key are not properly set in environment variables.")
        return self._client

    def _open(self, name, mode='rb'):
        # Opening/reading files directly via Django isn't typical for this flow,
        # but if needed we can retrieve it from the public url.
        raise NotImplementedError("This storage backend does not support opening files directly.")

    def _save(self, name, content):
        # Extract the base filename
        clean_name = os.path.basename(name)
        
        # Read the file content
        content.seek(0)
        file_data = content.read()
        
        # Get content type
        import mimetypes
        content_type, _ = mimetypes.guess_type(clean_name)
        file_options = {"cache-control": "3600", "upsert": "true"}
        if content_type:
            file_options["content-type"] = content_type

        try:
            # Upload data to Supabase Storage
            self.client.storage.from_(self.bucket_name).upload(
                path=clean_name,
                file=file_data,
                file_options=file_options
            )
        except Exception as e:
            raise Exception(
                f"Failed to upload image to Supabase Storage bucket '{self.bucket_name}'. "
                f"Please verify that the bucket exists in your Supabase dashboard and is public. "
                f"Error details: {str(e)}"
            )
        
        return clean_name

    def exists(self, name):
        clean_name = os.path.basename(name)
        try:
            res = self.client.storage.from_(self.bucket_name).list(search=clean_name)
            for item in res:
                if item.get('name') == clean_name:
                    return True
            return False
        except Exception:
            return False

    def url(self, name):
        clean_name = os.path.basename(name)
        try:
            return self.client.storage.from_(self.bucket_name).get_public_url(clean_name)
        except Exception:
            # Fallback if connection details are missing or client fails
            if self._supabase_url:
                return f"{self._supabase_url}/storage/v1/object/public/{self.bucket_name}/{clean_name}"
            return f"/media/{self.bucket_name}/{clean_name}"

    def size(self, name):
        clean_name = os.path.basename(name)
        try:
            res = self.client.storage.from_(self.bucket_name).list(search=clean_name)
            for item in res:
                if item.get('name') == clean_name:
                    metadata = item.get('metadata', {})
                    return metadata.get('size', 0)
            return 0
        except Exception:
            return 0

    def delete(self, name):
        clean_name = os.path.basename(name)
        try:
            self.client.storage.from_(self.bucket_name).remove([clean_name])
        except Exception:
            pass
