"""Bounded PNG/JPEG/WebP uploads; store only a decoded, metadata-free PNG.

The image is a separate record, so every hit does not rewrite image bytes.
Recovery files carry this record alongside the raid, not inside its counters.
"""
import base64
import binascii
import hashlib
import io
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError

MAX_UPLOAD = 4 * 1024 * 1024
MAX_PIXELS = 16_000_000
MAX_EDGE = 512
MAX_SAVED = 1_100_000


def from_upload(upload):
    if not upload or not upload.filename or upload.filename.rsplit('.', 1)[-1].lower() not in {'png', 'jpg', 'jpeg', 'webp'}:
        raise ValueError('Choose a PNG, JPG, JPEG or WebP image.')
    raw = upload.read(MAX_UPLOAD + 1)
    if not raw or len(raw) > MAX_UPLOAD:
        raise ValueError('Choose an image smaller than 4 MB.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as source:
                if source.format not in {'PNG', 'JPEG', 'WEBP'}:
                    raise ValueError('Only PNG, JPEG and WebP image contents are accepted.')
                if source.width * source.height > MAX_PIXELS:
                    raise ValueError('Use an image with at most 16 million pixels.')
                if getattr(source, 'n_frames', 1) != 1:
                    raise ValueError('Choose a still image, not an animated image.')
                source.load()  # Detect truncated/corrupt data before replacing anything.
                oriented = ImageOps.exif_transpose(source).convert('RGBA')
                oriented.thumbnail((MAX_EDGE, MAX_EDGE), Image.Resampling.LANCZOS)
                clean = Image.new('RGBA', oriented.size)
                clean.paste(oriented)
                output = io.BytesIO()
                clean.save(output, format='PNG')
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ValueError('That image could not be read safely. Choose another PNG, JPEG or WebP.') from None
    data = output.getvalue()
    if len(data) > MAX_SAVED:
        raise ValueError('The processed image is too large. Choose a simpler image.')
    return dict(sha256=hashlib.sha256(data).hexdigest(), data=base64.b64encode(data).decode('ascii'))


def validate_avatar(value):
    """Validate an optional recovery image before the import transaction commits."""
    if value is None:
        return None
    if not isinstance(value, dict) or not isinstance(value.get('data'), str) or len(value['data']) > (MAX_SAVED + 2) // 3 * 4:
        raise ValueError('Invalid boss avatar recovery.')
    try:
        raw = base64.b64decode(value['data'], validate=True)
        if not raw or len(raw) > MAX_SAVED or hashlib.sha256(raw).hexdigest() != value.get('sha256'):
            raise ValueError('Boss avatar recovery checksum does not match.')
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as image:
                if image.format != 'PNG' or not (1 <= image.width <= MAX_EDGE and 1 <= image.height <= MAX_EDGE) or getattr(image, 'n_frames', 1) != 1:
                    raise ValueError('Invalid boss avatar dimensions or format.')
                image.verify()
    except (binascii.Error, UnicodeEncodeError, UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ValueError('Invalid boss avatar recovery image.') from None
    return dict(sha256=value['sha256'], data=value['data'])


def image_bytes(value):
    return base64.b64decode(value['data'])
