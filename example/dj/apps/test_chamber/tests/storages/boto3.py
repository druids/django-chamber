from django.core.files.base import ContentFile
from django.test import TestCase

from chamber.storages.boto3 import force_bytes_content

from germanium.decorators import data_provider


class S3StorageTestCase(TestCase):

    TEST_DATA = (
        ('Hello, this is str content.', b'Hello, this is str content.', True),
        (b'Hello, this is bytes content.', b'Hello, this is bytes content.', False),
    )

    @data_provider(TEST_DATA)
    def test_s3storage_casts_content_to_bytes_if_needed(self, content, content_result, should_cast):
        file = ContentFile(content)
        result, casted = force_bytes_content(file)
        casted_content = result.read()
        self.assertEqual(should_cast, casted)
        self.assertEqual(bytes, type(casted_content))
        self.assertEqual(content_result, casted_content)
