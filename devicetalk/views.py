import json

from django.conf import settings
from django.template.response import TemplateResponse
from django.views.generic.base import View

from .utils import (
    GetDoInfo,
    DeviceTalkErrorTemplateResponse
)

from xtalk_account.utils import check_login
from api.models import (
    Language,
    Device,
    SaFunction
)
from api.utils import DeviceTalkJsonResponse


class MainPageView(View):
    '''
    Route: DEVICETALK_POSFIX/devicetalk/<str:username>/<int:p_id>/<int:do_id>/
    GET: Get the all the libraries information by language.
    PATCH: # TODO
    '''
    http_method_names = [
        'get',
        'patch'
    ]

#    @check_login
    def get(self, request, *args, **kwargs):
        """ This function return the devicetalk's main page
        """
        #username = kwargs['username']
        p_id = kwargs['p_id']
        do_id = kwargs['do_id']

        '''
        if request.user.username != username:
            return DeviceTalkErrorTemplateResponse(request, 'Wrong User', 400)
        '''
        #p_id = 435
        #do_id = 1208 
        username = 'larry891001'

        # Call AG to get df's information
        do_info = GetDoInfo(username, p_id, do_id)

        if not do_info.is_valid:
            return DeviceTalkErrorTemplateResponse(
                request, do_info.reason, do_info.status_code)
        results = do_info.do_info

#        print(do_info.do_info)

        languages = [
            {
                'name': item.name,
                'basic_file': [
                    {
                        'id': basicfile.id,
                        'name': basicfile.name,
                        'url': basicfile.manual
                    }
                    for basicfile in item.basicfile_set.all()
                ]
            }
            for item in Language.objects.all() if len(item.basicfile_set.all()) > 0
        ]


        device_name_list = [
            item.name
            for item in Device.objects.filter(
                dm_name=results['dm']['name'],
                user__username=username
            )
        ]

    

        global_device_objects = Device.objects.filter(
            dm_name=results['dm']['name'],
            user=None
        )
 #       print(global_device_objects)

        for device_object in global_device_objects:
            if device_object.name not in device_name_list:
                device_name_list.append(device_object.name)
        device_name_list.sort()

#        print(device_name_list)

        context = {
            'username': username,
            'p_id': p_id,
            'do_id': do_id,
            'languages': languages,
            'dm_result': results,
            'device_name_list': device_name_list,
            'DA_state_default': {
                'iottalk_server': 'https://class.iottalk.tw',#settings.DA_SERVER_URL_DEFAULT,
                'device_addr': '',
                'push_interval': settings.DA_PUSH_INTERVAL_DEFAULT,
            }
        }
#        print(context)
        return TemplateResponse(request, 'index.html', context)

    def patch(self, request, *args, **kwargs):
        """ This function delete all the tmp SA functions that don't related by any device

        Request format::

            {
                'saved_safunction': [2, 5, 10, ...]  # list of SA function id
            }

        Response format::

            {
                {
                    'state': 'OK',
                    'result': {}
                },
            }
        """
        body = json.loads(request.body)

        saved_safunction = body['data'].get('saved_safunction')
        function_objects = SaFunction.objects.filter(id__in=saved_safunction)
        for func in function_objects:
            if func.used_count() == 0:
                func.delete()
                
        return DeviceTalkJsonResponse()
