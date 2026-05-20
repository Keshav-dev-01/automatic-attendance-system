import os
from werkzeug.utils import secure_filename
from datetime import datetime
from PIL import Image
import imagehash

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
STATIC_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
UPLOAD_FOLDER = os.path.join(STATIC_FOLDER, 'uploads')
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_upload_file(file):
    """Save uploaded file and return relative static path"""
    if not file or file.filename == '':
        return None

    if not allowed_file(file.filename):
        return None

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = secure_filename(file.filename)
    name, ext = os.path.splitext(filename)
    filename = f"{timestamp}_{name}{ext}"

    full_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(full_path)

    return os.path.join('uploads', filename)


def extract_face_embedding(photo_path):
    """Extract a perceptual hash (phash) from the image and return hex string"""
    try:
        path = photo_path
        if not os.path.isabs(path):
            path = os.path.join(STATIC_FOLDER, path)

        img = Image.open(path).convert('L')
        phash = imagehash.phash(img)
        return str(phash)
    except Exception as e:
        print(f"Error extracting embedding: {e}")
        return None


def match_faces(uploaded_photo_path, stored_embedding):
    """Compare uploaded photo to stored perceptual hash.

    Returns (match_score, is_match)
    match_score: float between 0..1 where 1 is exact
    is_match: bool if distance <= threshold
    """
    try:
        uploaded_hash = extract_face_embedding(uploaded_photo_path)
        if not uploaded_hash or not stored_embedding:
            return 0.0, False

        uh = imagehash.hex_to_hash(uploaded_hash)
        sh = imagehash.hex_to_hash(stored_embedding)
        distance = uh - sh
        max_bits = uh.hash.size * uh.hash.size if hasattr(uh, 'hash') else 64
        if not max_bits:
            max_bits = 64

        match_score = max(0, 1.0 - (distance / max_bits))
        is_match = distance <= 10
        return float(match_score), bool(is_match)
    except Exception as e:
        print(f"Error matching faces: {e}")
        return 0.0, False


def match_faces_with_embeddings(uploaded_photo_path, stored_embeddings):
    """Try matching an uploaded photo against multiple embeddings."""
    if not stored_embeddings:
        return 0.0, False, None

    best_score = 0.0
    best_match = None
    best_is_match = False

    for embedding in stored_embeddings:
        score, matched = match_faces(uploaded_photo_path, embedding)
        if score > best_score:
            best_score = score
            best_is_match = matched
            best_match = embedding

    return best_score, best_is_match, best_match
