import os
from webdav3.client import Client
from app.core.config import settings

def get_webdav_client() -> Client:
    options = {
        'webdav_hostname': settings.WEBDAV_HOSTNAME,
        'webdav_login': settings.WEBDAV_LOGIN,
        'webdav_password': settings.WEBDAV_PASSWORD
    }
    return Client(options)

def upload_to_webdav_stream(local_path: str, remote_filename: str):
    """
    Uploads a file to WebDAV using a streaming generator to keep memory footprint low.
    """
    client = get_webdav_client()
    
    # Ensure remote directory exists (simple check)
    if not client.check(settings.WEBDAV_ROOT):
        client.mkdir(settings.WEBDAV_ROOT)
        
    remote_path = f"{settings.WEBDAV_ROOT}/{remote_filename}"
    
    chunk_size = 8 * 1024 * 1024  # 8MB chunk
    
    def file_chunk_generator():
        with open(local_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    # webdavclient3's upload works with file paths directly or file-like objects.
    # We will use requests directly or the client's underlying method if it supports generators.
    # webdavclient3 upload_sync uses pure requests.put. We can bypass it for true generator streaming:
    
    import requests
    from requests.auth import HTTPBasicAuth
    
    url = f"{settings.WEBDAV_HOSTNAME.rstrip('/')}/{remote_path.lstrip('/')}"
    auth = HTTPBasicAuth(settings.WEBDAV_LOGIN, settings.WEBDAV_PASSWORD)
    
    response = requests.put(url, data=file_chunk_generator(), auth=auth)
    
    if response.status_code not in (200, 201, 204):
        raise Exception(f"Failed to upload to WebDAV: {response.status_code} {response.text}")
    
    # Cleanup local file upon successful upload
    if os.path.exists(local_path):
        os.remove(local_path)
