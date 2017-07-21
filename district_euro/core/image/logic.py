import cStringIO as StringIO

from core.models import Image
from core.storage import get_connection
from district_euro import settings
from .processing import resize_small, resize_landscape, resize_portrait, validate_image

access_key = settings.S3_ACCES_KEY
secret_key = settings.S3_SECRET_KEY
bucket_name = settings.S3_BUCKET_NAME


def _upload_image_s3(prefix, obj, image, file_name=None, resize_on_upload=True, object_field='object'):
    def resize_and_upload(_im, _original_key, _resize_fn):
        _resized_im, _new_file_name = _resize_fn(_im, _original_key.name)
        if _im == _resized_im:
            return _original_key
        _image_stream = StringIO.StringIO()
        _resized_im.save(_image_stream, format=_im.format)
        _key = conn.upload_from_file(_image_stream, _new_file_name)
        return _key

    with get_connection() as conn:
        im = validate_image(image)

        image_data = StringIO.StringIO()
        im.save(image_data, format=im.format)

        image_file_name = file_name or image.name

        key = conn.upload_from_file(image_data, key_name=file_name, prefix=prefix, file_name=image_file_name)

        if resize_on_upload:
            small_key = resize_and_upload(im, key, resize_small)
            portrait_key = resize_and_upload(im, key, resize_portrait)
            landscape_key = resize_and_upload(im, key, resize_landscape)
        else:
            small_key = portrait_key = landscape_key = key

        image_urls = dict(
            zip(
                ['url', 'small_url', 'portrait_url', 'landscape_url'],
                map(lambda x: x.generate_url(expires_in=0, query_auth=False),
                    [key, small_key, portrait_key, landscape_key])
            )
        )
        params = {
            object_field: obj
        }
        params.update(image_urls)
        image = Image.objects.create(name=key.name, **params)
    return image, key


def upload_image(prefix, obj, image, file_name=None, resize_on_upload=True):
    """
    Uploads an image and associate it with an object (Model).

    :type prefix: str
    :param prefix: name prefix. It can be a directory like path

    :type obj: Model
    :param obj: Object to which associate image

    :type image: Readable object
    :param image: Image data.

    :type file_name: str
    :param file_name: Name of file. If its None then it asign a random name.

    :type resize_on_upload: Bool
    :param resize_on_upload: If the image should be resized on upload.

    :return: models.Image
    """
    image, _ = _upload_image_s3(prefix, obj, image, file_name=file_name, resize_on_upload=resize_on_upload)
    return image


def upload_image2(prefix, obj, image, file_name=None, resize_on_upload=True):
    """
    Horrible way of having an object with two images sets. Default set is asign with upload_image, secondary set is
    assign with this.
    """
    image, _ = _upload_image_s3(prefix, obj, image, file_name=file_name, resize_on_upload=resize_on_upload, object_field='object2')
    return image



def delete_image(image):
    """
    Deletes an image

    :type image: core.models.Image or image pk
    :param image: image object to be deleted

    :return: True if success else False
    """

    if image:
        assert isinstance(image, Image) or isinstance(image, int), "delete image accepts only Image instance"
        # TODO: delete files from s3
        if isinstance(image, Image):
            pk = image.pk
        else:
            pk = image
        Image.objects.filter(pk=pk).delete()
        return True
    return False


def _get_models_with_images():
    """
    For now just models that vendor can upload images to.

    :return: set with models names lowercase.
    """
    return {
        'product',
        'incompleteproduct',
        'joinrequest'
    }


def is_model_valid(model):
    """
    Returns true if a model can be assoicated with images.

    :type model: str
    :param model: the model name

    :rtype: bool
    :return: if model can be asociated with images.
    """
    return model.lower() in _get_models_with_images()
