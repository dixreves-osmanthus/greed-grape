from datetime import datetime


def get_level_name(level):
    """Get display name for education level."""
    levels = {
        'high_school': 'High School',
        'university': 'University'
    }
    return levels.get(level, level)


def get_difficulty_name(difficulty):
    """Get display name for question difficulty."""
    difficulties = {
        'easy': 'Easy',
        'medium': 'Medium',
        'hard': 'Hard'
    }
    return difficulties.get(difficulty, difficulty)


def get_document_type_name(doc_type):
    """Get display name for document type."""
    types = {
        'essay': 'Essay',
        'handout': 'Handout'
    }
    return types.get(doc_type, doc_type)


def format_date(date, format='%B %d, %Y'):
    """Format datetime object to string."""
    if not date:
        return ''
    if isinstance(date, str):
        date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
    return date.strftime(format)


def format_file_size(size_bytes):
    """Format file size in human-readable format."""
    if size_bytes == 0:
        return '0 Bytes'
    
    size_names = ['Bytes', 'KB', 'MB', 'GB', 'TB']
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.2f} {size_names[i]}"


def truncate_text(text, length=100, suffix='...'):
    """Truncate text to specified length."""
    if not text:
        return ''
    if len(text) <= length:
        return text
    return text[:length] + suffix


def generate_random_string(length=8):
    """Generate a random string of specified length."""
    import random
    import string
    
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for _ in range(length))


def sanitize_filename(filename):
    """Sanitize filename for safe display."""
    import re
    # Remove special characters and replace with underscore
    sanitized = re.sub(r'[^\w\-. ]', '_', filename)
    return sanitized.strip('_')
