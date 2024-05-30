import json

from django.http import HttpResponse
from django.template import loader
from django.views.generic.base import View

from .models import File
from .utils import (
    create_upload_batch,
    save_file
)
from api.utils import (
    DeviceTalkJsonResponse,
    DeviceTalkErrorJsonResponse
)
from devicetalk.utils import DeviceTalkErrorTemplateResponse
from xtalk_account.utils import check_login


class FileView(View):
    """
    Route: DEVICETALK_POSFIX/api/file/<str:uuid>
    GET: Get the file's content.
    POST: Upload the file to server.
    """
    http_method_names = [
        'get',
        'post'
    ]

    @check_login
    def get(self, request, *args, **kwargs):
        """ This function return the file's content in html format.
        """
        uuid = kwargs['uuid']
        try:
            # Get the file item from File table.
            f = File.objects.get(uuid=uuid).open('r')
        except:
            return DeviceTalkErrorTemplateResponse(request, 'File not found')

        template = loader.get_template('view_file.html')
        return HttpResponse(template.render({'words': f.read()}, request))

    @check_login
    def post(self, request, *args, **kwargs):
        """ This function that user upload the file's raw data.

        Request format::
            Header:
                Content-Type: application/octet-stream
            Body:
                file's raw data

        Response format::

            {
                {
                    'state': 'OK',
                    'result': {}
                },
            }
        """
        uuid = kwargs['uuid']
        err_msg, code = save_file(uuid, request.FILES.get('file'))
        if err_msg:
            return DeviceTalkErrorJsonResponse(err_msg, code)
        else:
            return DeviceTalkJsonResponse()


class UploadSetupView(View):
    '''
    Route: DEVICETALK_POSFIX/api/file
    PUT: Setup the UploadBatch and File object to start upload process.
    '''
    http_method_names = [
        'put'
    ]

    @check_login
    def put(self, request, *args, **kwargs):
        """ This function setup the UploadBatch and File object to start upload process.

        Request format::

            {
                'files': ['RPi_library/examples/foo.py', ...]  # list of file's path
            }

        Response format::

            {
                'state': 'OK',
                'result': {
                    'upload_info': {
                        # key: the file's path
                        # value: the corresponding uuid
                        'RPi_library/examples/foo.py': 'abc123...', ...
                    },
                    'file_upload_id': 10
                }
            }
        """
        body = json.loads(request.body)
        if body.get('data') is None:
            return DeviceTalkErrorJsonResponse('data not found', 400)
        return DeviceTalkJsonResponse(
            create_upload_batch(
                body.get('data').get('files', [])
            )
        )
