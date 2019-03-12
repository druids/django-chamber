Forms
=====

.. class:: chamber.forms.fields.DecimalField

``django.forms.DecimalField`` with ``step``, ``min``, and ``max`` parameters.

.. class:: chamber.forms.widgets.ReadonlyWidget

A widget for safe rendering of readonly form values.

.. class:: chamber.forms.fields.PriceField

``django.forms.NumberInput`` with ``currency`` as a placeholder.

.. class:: chamber.forms.fields.RestictedFileField

``django.forms.FileField`` where you can set ``allowed_content_types`` amd ``max_upload_size``. File type is validated by file extension and content::

    class FileForm(forms.Form):
        file = RestictedFileField(allowed_content_types=('image/jpeg', 'application/pdf'), max_upload_size=10)  # allowed JPEG or PDF file with max size 10 MB
