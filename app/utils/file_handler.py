import os
from werkzeug.utils import secure_filename
from config import Config
from datetime import datetime


def is_allowed_extension(filename, allowed_extensions=None):
    """Check if file extension is allowed."""
    if allowed_extensions is None:
        allowed_extensions = Config.ALLOWED_EXTENSIONS
    
    if not filename:
        return False
    
    # Get file extension
    ext = get_file_extension(filename)
    
    return ext.lower() in [e.lower() for e in allowed_extensions]


def get_file_extension(filename):
    """Get file extension from filename."""
    if not filename:
        return ''
    
    # Handle filenames with dots
    parts = filename.rsplit('.', 1)
    if len(parts) > 1:
        return '.' + parts[1]
    return ''


def generate_unique_filename(filename):
    """Generate a unique filename to prevent conflicts."""
    ext = get_file_extension(filename)
    base_name = secure_filename(filename.rsplit('.', 1)[0] if '.' in filename else filename)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    
    # Add timestamp to ensure uniqueness
    unique_name = f"{base_name}_{timestamp}{ext}"
    
    return unique_name


def save_file(file, upload_folder=None, allowed_extensions=None):
    """
    Save uploaded file to the specified folder.
    
    Args:
        file: FileStorage object from Flask
        upload_folder: Path to upload folder (defaults to config)
        allowed_extensions: Set of allowed extensions
        
    Returns:
        tuple: (success: bool, message: str, file_path: str, file_name: str)
    """
    if upload_folder is None:
        upload_folder = Config.UPLOAD_FOLDER
    
    if allowed_extensions is None:
        allowed_extensions = Config.ALLOWED_EXTENSIONS
    
    # Check if file is present
    if not file or file.filename == '':
        return False, 'No file selected', None, None
    
    # Check if file extension is allowed
    if not is_allowed_extension(file.filename, allowed_extensions):
        return False, f'File type not allowed. Allowed: {', '.join(allowed_extensions)}', None, None
    
    # Ensure upload folder exists
    os.makedirs(upload_folder, exist_ok=True)
    
    # Generate unique filename
    unique_filename = generate_unique_filename(file.filename)
    file_path = os.path.join(upload_folder, unique_filename)
    
    try:
        # Save the file
        file.save(file_path)
        return True, 'File uploaded successfully', file_path, unique_filename
    except Exception as e:
        return False, f'Error saving file: {str(e)}', None, None


def delete_file(file_path):
    """
    Delete a file from the filesystem.
    
    Args:
        file_path: Full path to the file
        
    Returns:
        tuple: (success: bool, message: str)
    """
    if not file_path or not os.path.exists(file_path):
        return False, 'File not found'
    
    try:
        os.remove(file_path)
        return True, 'File deleted successfully'
    except Exception as e:
        return False, f'Error deleting file: {str(e)}'


def get_file_info(file_path):
    """Get file information (size, type, etc.)."""
    if not os.path.exists(file_path):
        return None
    
    stat = os.stat(file_path)
    return {
        'size': stat.st_size,
        'modified': datetime.fromtimestamp(stat.st_mtime),
        'created': datetime.fromtimestamp(stat.st_ctime)
    }
