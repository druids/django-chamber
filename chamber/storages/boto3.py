import boto3
from botocore.client import Config

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import DefaultStorage

from storages.backends.s3boto3 import S3Boto3Storage


__all__ = (
    'S3Storage',
    'force_bytes_content',
    'get_storage_instance',
    's3_presigned_download_url',
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


def s3_presigned_download_url(url=None, file=None, expiration=3600):
    if not url and not file:
        raise ValueError('You must provide either a "url" or "file".')

    if url:
        return url
    if not settings.AWS_S3_ON:
        return file.url

    s3 = boto3.client('s3', config=Config(region_name=settings.AWS_REGION, signature_version='s3v4'))
    url = s3.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': file.storage.bucket_name,
            'Key': file.storage.get_full_relative_path(file.name),
        },
        ExpiresIn=expiration,
    )
    return url


def get_storage_instance(storage_class, default_storage_class=DefaultStorage):
    return storage_class() if settings.AWS_S3_ON else default_storage_class()


class S3Storage(S3Boto3Storage):

    def get_full_relative_path(self, filename):
        return '{}/{}'.format(self.location, filename) if self.location else filename

    def save(self, name, content, max_length=None):
        content, _ = force_bytes_content(content)
        return super().save(name, content, max_length)
