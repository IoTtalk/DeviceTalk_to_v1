from django.contrib import admin
from .models import (
    Language,
    BasicFile,
    Library,
    DfType,
    LibraryFunction,
    SaFunction,
    DeviceLibrary,
    Device,
    DeviceHasLibrary,
    DeviceDf,
    DeviceLibraryDf,
    DeviceDfHasSaFunction,
    DeviceLibraryDfHasSaFunction,
)


class DfTypeAdmin(admin.ModelAdmin):
    list_display = ('df_type', 'params')
    list_filter = ('df_type',)


class SaFunctionAdmin(admin.ModelAdmin):
    readonly_fields = ('updated_at',)
    list_display = ('id', 'name', 'function_type', )
    list_filter = ('function_type', )


class LibraryPoolAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user')


admin.site.register(Language)
admin.site.register(BasicFile)
admin.site.register(Library)
admin.site.register(DfType, DfTypeAdmin)

admin.site.register(LibraryFunction)

admin.site.register(SaFunction, SaFunctionAdmin)
admin.site.register(DeviceLibrary, LibraryPoolAdmin)
admin.site.register(Device, LibraryPoolAdmin)

admin.site.register(DeviceHasLibrary)
admin.site.register(DeviceDf)
admin.site.register(DeviceLibraryDf)
admin.site.register(DeviceDfHasSaFunction)
admin.site.register(DeviceLibraryDfHasSaFunction)
