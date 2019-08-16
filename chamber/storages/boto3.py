from django.core.files.base import ContentFile

from storages.backends.s3boto3 import S3Boto3Storage


__all__ = (
    'S3Storage',
    'force_bytes_content',
)


def force_bytes_content(content, blocksize=1024):
    '''Returns a tuple of content (file-like object) and bool indicating wheter the content has been casted or not'''
    block = content.read(blocksize)
    content.seek(0)

    if not isinstance(block, bytes):
        _content = bytes(
            content.read(),
            'utf-8' if not hasattr(content, 'encoding') or content.encoding is None else content.encoding,
        )
        return ContentFile(_content), True
    return content, False


class S3Storage(S3Boto3Storage):

    def save(self, name, content, max_length=None):
        content, _ = force_bytes_content(content)
        return super().save(name, content, max_length)
