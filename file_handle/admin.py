from django.contrib import admin

from file_handle.models import (
    UploadBatch,
    File
)


class FileAdmin(admin.ModelAdmin):
    readonly_fields = ('created_at', 'uuid')


admin.site.register(UploadBatch)
admin.site.register(File, FileAdmin)
