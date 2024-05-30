import json
import requests

from django.conf import settings
from django.template.response import TemplateResponse

from xtalk_account.models import AccessToken


class GetDoInfo:
    __is_valid = False
    __reason = ""
    __status_code = 500

    def __init__(self, username, p_id, do_id):
        self.__username = username
        self.__p_id = p_id
        self.__do_id = do_id
    
        self._get_info()
        '''
        access_token_objects = AccessToken.objects.filter(user__username=username)
        if len(access_token_objects) == 0:
            self.__reason = 'User :%s not found' % (username)
            self.__status_code = 404
        else:
            self.__access_token_object = access_token_objects.last()
            if self._check_access_token_object():
                self._get_info()
       '''                

    def _check_access_token_object(self):
        if self.__access_token_object.is_expired:
            try:
                self.__access_token_object.refresh()
            except:
                self.__reason = 'Access token refresh fail'
                return False
            access_token_objects = AccessToken.objects.filter(
                user__username=self.__username)
            if len(access_token_objects) == 0:
                self.__reason = 'User :%s not found' % (self.__username)
                return False
            self.__access_token_object = access_token_objects.last()
        return True

    def _get_info(self):
        data = {
            "api_name": "deviceobject.get",
            "payload": {
                "p_id": self.__p_id,
                "do_id": self.__do_id
            },
#            "access_token": self.__access_token_object.token
        }
        '''
        r = requests.post(settings.AUTOGEN_CCMAPI_URL, json=data)
        '''

        pid = self.__p_id# '566'
        doid =self.__do_id# '2845'
        v1url = f'https://classgui.iottalk.tw/api/v0/project/{pid}/deviceobject/{doid}'
        r1 = requests.get(v1url)
        info = json.loads(r1.text)
        '''
        body = json.loads(r.text)
        '''

        self.__status_code = r1.status_code
        '''
        self.__status_code = r.status_code
        '''

        if r1.status_code == 200:
            '''
            result = body['result']
            '''
            info = info['data'] 

            self.__dm1 = {'name': info['dm_name'], 'id': info['dm_id']}
            '''
            self.__dm = {'name': result['dm_name'], 'id': result['dm_id']}
            '''


            self.__idfs1, self.__odfs1 = ([
                {
                    'name': df['df_name'],
                    'df_type': ['float'], #[para['param_type'] for para in df['df_parameter']],
                    'used': 1 if df['df_name'] in info['do']['dfo'] else 0
                }
                for df in info['df_list']
                if df['df_type'] == df_type

            ] for df_type in ('input', 'output'))
            self.__is_valid = True

#            print(self.__idfs1)
#            print(self.__odfs1)

            '''
            self.__idfs, self.__odfs = ([
                {
                    'name': df['df_name'],
                    'df_type': [para['param_type'] for para in df['df_parameter']],
                    'used': 1 if df['df_name'] in result['do']['dfo'] else 0
                }
                for df in result['df_list']
                if df['df_type'] == df_type
            ] for df_type in ('input', 'output'))
            self.__is_valid = True
            '''
 #           print(self.__idfs)
 #           print(self.__odfs)

#        elif 'reason' in body:
#        elif 'reason' in info:
#            self.__reason = 'Error in AG!\n%s' % body['reason']
        else:
            self.__reason = 'Unknown reason.'




    @property
    def do_info(self):
        return {
            'dm': self.__dm1,
            'idf': self.__idfs1,
            'odf': self.__odfs1,
        }

    @property
    def reason(self):
        return self.__reason

    @property
    def status_code(self):
        return self.__status_code

    @property
    def is_valid(self):
        return self.__is_valid


class DeviceTalkErrorTemplateResponse(TemplateResponse):
    template_name = 'index_error.html'

    def __init__(self, request, reason, status_code=404):
        context = {
            'status_code': status_code,
            'error_reason': reason
        }
        super().__init__(request, self.template_name, context)
        self.status_code = status_code
