import os
import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from api.models import (
    BasicFile,
    Library,
    DeviceLibrary,
    Device
)

__all__ = [
    'UploadBatch',
    'File'
]


class UploadBatch(models.Model):
    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return str(self.id)


class File(models.Model):
    file_path = models.CharField(
        max_length=100,
        blank=False
    )
    real_path = models.CharField(
        max_length=200,
        blank=False
    )
    is_upload = models.BooleanField(
        default=False
    )
    uuid = models.UUIDField(
        editable=False,
        unique=True
    )
    created_at = models.DateTimeField(
        _('created time'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('updated time'),
        auto_now=True
    )
    upload_batch = models.ForeignKey(
        UploadBatch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    library = models.ForeignKey(
        Library,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    device_library = models.ForeignKey(
        DeviceLibrary,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="file"
    )
    basic_file = models.ForeignKey(
        BasicFile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    device = models.OneToOneField(
        Device,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="file"
    )

    def __str__(self):
        return f'[{self.id}]{self.file_path}'

    # Open the file in file system.
    def open(self, mode):
        return open(self.real_path, mode)

    # Before delete this item, delete the file in file system.
    def delete(self, *args, **kwargs):
        os.remove(self.real_path)
        return super().delete(*args, **kwargs)

    @property
    def url(self):
        return os.path.join(
            '/', settings.STATIC_URL,
            os.path.relpath(self.real_path, settings.FILE_UPLOAD_DIR)
        )

    # Generate a unique uuid4
    @staticmethod
    def uuid_generate():
        uuid_code = uuid.uuid4()
        while len(File.objects.filter(uuid=uuid_code.hex)) > 0:
            uuid_code = uuid.uuid4()
        return uuid_code
