import mimetypes

import magic  # pylint: disable=E0401

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext
from django.template.defaultfilters import filesizeformat


class RestrictedFileValidator:

    def __init__(self, max_upload_size):
        self.max_upload_size = max_upload_size

    def __call__(self, data):
        if data.size > self.max_upload_size:
            raise ValidationError(
                ugettext('Please keep filesize under {max}. Current filesize {current}').format(
                    max=filesizeformat(self.max_upload_size),
                    current=filesizeformat(data.size)
                )
            )
        else:
            return data


class AllowedContentTypesByFilenameFileValidator:

    def __init__(self, content_types):
        self.content_types = content_types

    def __call__(self, data):
        extension_mime_type = mimetypes.guess_type(data.name)[0]

        if extension_mime_type not in self.content_types:
            raise ValidationError(ugettext('Extension of file name is not allowed'))

        return data


class AllowedContentTypesByContentFileValidator:

    def __init__(self, content_types):
        self.content_types = content_types

    def __call__(self, data):
        data.open()
        with magic.Magic(flags=magic.MAGIC_MIME_TYPE) as m:
            mime_type = m.id_buffer(data.read(1024))
            data.seek(0)
            if mime_type not in self.content_types:
                raise ValidationError(ugettext('File content was evaluated as not supported file type'))

        return data
