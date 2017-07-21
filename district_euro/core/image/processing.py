import cStringIO as StringIO

from PIL import Image
from resizeimage import resizeimage
from resizeimage.imageexceptions import ImageSizeError

from core.exceptions import FileTooBigException, InvalidImageFileException

_ONE_MB = 2 ** 20
CHUNK_SIZE = _ONE_MB
MINIMUM_MULTIPART_SIZE = 5 * _ONE_MB
MAX_IMAGE_SIZE = 10 * _ONE_MB


MINIMUM_IMAGE_WIDTH = 400
MINIMUM_IMAGE_HEIGHT = 400

PORTRAIT_HEIGHT = 600
PORTRAIT_WIDTH = 400

LANDSCAPE_WIDTH = PORTRAIT_HEIGHT
LANDSCAPE_HEIGHT = PORTRAIT_WIDTH


def validate_image(data):
    """
    Validates image format and size. If successful returns an PIL.Image object.

    :param data:  django.core.files.uploadedfile.UploadedFile (request.FILES)
    :return: PIL.Image
    """
    if data.size > MAX_IMAGE_SIZE:
        raise FileTooBigException()

    file_stream = StringIO.StringIO()

    for chunk in data.chunks(CHUNK_SIZE):
        file_stream.write(chunk)
    file_stream.seek(0)

    im = Image.open(file_stream)

    try:
        im.verify()
    except Exception as e:
        raise InvalidImageFileException()

    file_stream.seek(0)
    im = Image.open(file_stream)

    return im


def _get_filename_with_suffix(filename, suffix):
    extension = filename.split('.')[-1]
    if extension == filename:
        extension = ''
        name = filename
    else:
        extension = ".%s" % extension
        name = filename[:-len(extension)]

    return "%s_%s%s" % (name, suffix, extension)


def resize_small(im, filename):
    """
    Return an image croped to specified size.

    :param im: PIL.Image
    :param filename: str
    :return: PIL.Image, str
    """
    im.seek(0)
    try:
        crop = resizeimage.resize_cover(im, [MINIMUM_IMAGE_WIDTH, MINIMUM_IMAGE_HEIGHT])
    except ImageSizeError:
        crop = im
    return crop, _get_filename_with_suffix(filename, 'small')


def resize_portrait(im, filename):
    """
    Return an image resized to portrait.

    :param im: PIL.Image
    :param filename: str
    :return: PIL.Image, str
    """
    im.seek(0)
    try:
        crop = resizeimage.resize_cover(im, [PORTRAIT_WIDTH, PORTRAIT_HEIGHT])
    except ImageSizeError:
        crop = im
    return crop, _get_filename_with_suffix(filename, 'portrait')


def resize_landscape(im, filename):
    """
    Return an image resized to portrait.

    :param im: PIL.Image
    :param filename: str
    :return: PIL.Image, str
    """
    im.seek(0)
    try:
        crop = resizeimage.resize_cover(im, [LANDSCAPE_WIDTH, LANDSCAPE_HEIGHT])
    except ImageSizeError:
        crop = im
    return crop, _get_filename_with_suffix(filename, 'landscape')