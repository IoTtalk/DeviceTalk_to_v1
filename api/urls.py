from django.urls import (
    include,
    path,
)
from .views import (
    LibraryManagerView,
    DeviceManagerView,
    ListFunctionManagerView,
    NewFunctionManagerView,
    SingleFunctionManagerView,
)

app_name = 'api'

urlpatterns = [
    path(
        'library/<str:language>/<int:basic_file_id>',
        LibraryManagerView.as_view(),
        name='api_library_endpoint'
    ),
    path(
        'function',
        ListFunctionManagerView.as_view(),
        name='list_function_endpoint'
    ),
    path(
        'function/new/<str:language>/<int:basic_file>',
        NewFunctionManagerView.as_view(),
        name='get_new_function_endpoint'
    ),
    path(
        'function/new',
        NewFunctionManagerView.as_view(),
        name='put_new_function_endpoint'
    ),
    path(
        'function/<str:function_type>/<str:function_id>',
        SingleFunctionManagerView.as_view(),
        name='singel_function_endpoint'
    ),
    path('device', DeviceManagerView.as_view(), name='device_endpoint'),
    path('file/', include('file_handle.urls')),
]
