import boto3
from botocore.client import Config

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import DefaultStorage

from storages.backends.s3boto3 import S3Boto3Storage

from chamber.config import settings


__all__ = (
    'BaseS3Storage',
    'BasePrivateS3Storage',
    'BasePrivateS3DataStorage',
    'force_bytes_content',
    'get_storage_instance',
)


def force_bytes_content(content, blocksize=1024):
    """Returns a tuple of content (file-like object) and bool indicating wheter the content has been casted or not"""
    block = content.read(blocksize)
    content.seek(0)

    if not isinstance(block, bytes):
        _content = bytes(
            content.read(),
            'utf-8' if not hasattr(content, 'encoding') or content.encoding is None else content.encoding,
        )
        return ContentFile(_content), True
    return content, False


def get_storage_class(s3_storage_class, default_storage_class=DefaultStorage):
    return s3_storage_class if settings.AWS_S3_ON else default_storage_class


def get_storage_instance(s3_storage_class, default_storage_class=DefaultStorage):
    return s3_storage_class() if settings.AWS_S3_ON else default_storage_class()


class BaseS3Storage(S3Boto3Storage):

    def _clean_name(self, name):
        # pathlib support
        return super()._clean_name(str(name))

    def save(self, name, content, max_length=None):
        content, _ = force_bytes_content(content)
        return super().save(name, content, max_length)


class BasePrivateS3Storage(BaseS3Storage):

    expiration = settings.PRIVATE_S3_STORAGE_URL_EXPIRATION

    def url(self, name):
        s3 = boto3.client('s3', config=Config(region_name=settings.AWS_REGION, signature_version='s3v4'))
        url = s3.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': self.bucket_name,
                'Key': self._normalize_name(name),
            },
            ExpiresIn=self.expiration,
        )
        return url


class BasePrivateS3DataStorage(BaseS3Storage):

    def url(self, name):
        raise RuntimeError('You cannot generate data storage URL')
