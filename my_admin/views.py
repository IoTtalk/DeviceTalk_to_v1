import json

from urllib.parse import parse_qs

from django.contrib.auth import get_user_model
from django.template.response import TemplateResponse
from django.views.generic.base import View

from .utils import (
    remove_file_group,
    update_basicfile
)
from api.models import (
    BasicFile,
    Language
)
from api.utils import (
    DeviceTalkJsonResponse,
    DeviceTalkErrorJsonResponse
)
from xtalk_account.utils import (
    check_login,
    check_is_admin
)


class LanguageView(View):
    http_method_names = [
        'get',
        'put',
        'delete'
    ]

    @check_login
    @check_is_admin
    def get(self, request, *args, **kwargs):
        """ This function return the list of language.
        Query param::
            <None>

        Response format::

            {
                {
                    'state': 'OK',
                    'result': {
                        'languages': [list of language name],
                        'basic_files_map': {
                            language_name: [list of basicfile name],
                        }
                    }
                },
            }
        """
        languages = [
            language.name for language in Language.objects.all()
        ]
        basic_files = {
            language.name: {
                basicfile.id: basicfile.name
                for basicfile in language.basicfile_set.all()
            }
            for language in Language.objects.all()
        }
        return DeviceTalkJsonResponse({
            'languages': languages,
            'basic_files_map': basic_files
        })

    @check_login
    @check_is_admin
    def put(self, request, *args, **kwargs):
        """ This function create new language
        Request format::
            {
                'language': language name
            }

        Sucess Response format::
            {
                {
                    'state': 'OK',
                    'result': {}
                },
            }

        Error Response format::
            {
                {
                    'state': 'error',
                    'reason': '...'
                },
            }
        """
        body = json.loads(request.body)
        language = body.get('data', {}).get('language')
        try:
            Language.objects.create(name=language)
        except:
            return DeviceTalkErrorJsonResponse(
                f'Language "{language}" already exist or other error.',
                400
            )
        return DeviceTalkJsonResponse()

    @check_login
    @check_is_admin
    def delete(self, request, *args, **kwargs):
        """ This function delete a language
        Request format::
            {
                'language': language name
            }

        Sucess Response format::
            {
                {
                    'state': 'OK',
                    'result': {}
                },
            }

        Error Response format::
            {
                {
                    'state': 'error',
                    'reason': '...'
                },
            }
        """
        body = json.loads(request.body)
        language = body.get('data', {}).get('language')
        try:
            language_object = Language.objects.get(name=language)
        except:
            return DeviceTalkErrorJsonResponse(f'Language "{language}" not found.')
        basicfile_list = [b for b in language_object.basicfile_set.all()]
        for basicfile_object in basicfile_list:
            file_objects = [f for f in basicfile_object.file_set.all()]
            for file in file_objects:
                file.delete()
            basicfile_object.delete()
        language_object.delete()
        return DeviceTalkJsonResponse()


class BasicFileView(View):
    http_method_names = [
        'get',
        'put',
        'post',
        'delete'
    ]

    @check_login
    @check_is_admin
    def get(self, request, *args, **kwargs):
        """ This function return the list of basic files’ information.
        Query param::
            language: language's name
            basicfile: basicfile's id

        Response format::

            {
                {
                    'state': 'OK',
                    'result': {
                        'files': [
                            {
                                'uuid': 'abc123...',
                                'file_path': '/example/foo.py'
                            }, ...
                        ]
                    }
                },
            }
        """
        qs_body = parse_qs(request.GET.urlencode())
        language = qs_body.get('language', [None])[0]
        basicfile = qs_body.get('basicfile', [None])[0]

        try:
            basic_file_object = BasicFile.objects.get(
                id=basicfile
            )
        except:
            return DeviceTalkJsonResponse({'files': []})
        if basic_file_object.language.name != language:
            return DeviceTalkErrorJsonResponse(
                'Language name and Basicfile ID not match', 400)

        files_list = [
            {
                'uuid': file.uuid,
                'file_path': file.file_path
            }
            for file in basic_file_object.file_set.all()
        ]
        return DeviceTalkJsonResponse({
            'files': files_list
        })

    @check_login
    @check_is_admin
    def put(self, request, *args, **kwargs):
        """ Create new Basic File.
        Request format::
            {
                'state': "completed" | "failed",
                'file_upload_id': 10,
                'basicfile_name': 'Default',  # name of basicfile
                'language': 'Python'  # the language this basicfile belong to
            }

        Sucess Response format::
            {
                {
                    'state': 'OK',
                    'result': {}
                },
            }

        Error Response format::
            {
                {
                    'state': 'error',
                    'reason': '...'
                },
            }
        """
        body = json.loads(request.body)
        err_msg, code = update_basicfile(
            body.get('data', {}).get('file_upload_id'),
            body.get('data', {}).get('state'),
            body.get('data', {}).get('language'),
            body.get('data', {}).get('basicfile_name'),
            is_create=True,
        )

        if err_msg:
            return DeviceTalkErrorJsonResponse(err_msg, code)
        else:
            return DeviceTalkJsonResponse()

    @check_login
    @check_is_admin
    def post(self, request, *args, **kwargs):
        """ Update exist Basic File.
        Request format::
            {
                'state': "completed" | "failed",
                'file_upload_id': 10,
                'basicfile_name': 'Default',  # name of basicfile
                'language': 'Python'  # the language this basicfile belong to
            }

        Sucess Response format::
            {
                {
                    'state': 'OK',
                    'result': {}
                },
            }

        Error Response format::
            {
                {
                    'state': 'error',
                    'reason': '...'
                },
            }
        """
        body = json.loads(request.body)
        err_msg, code = update_basicfile(
            body.get('data', {}).get('file_upload_id'),
            body.get('data', {}).get('state'),
            body.get('data', {}).get('language'),
            body.get('data', {}).get('basicfile_name'),
            is_create=False,
        )

        if err_msg:
            return DeviceTalkErrorJsonResponse(err_msg, code)
        else:
            return DeviceTalkJsonResponse()

    @check_login
    @check_is_admin
    def delete(self, request, *args, **kwargs):
        """ This function check the uploaded file's format.
        Request format::
            {
                'basicfile': 10,  # id of basicfile
                'language': 'Python'  # the language this basicfile belong to
            }

        Sucess Response format::
            {
                {
                    'state': 'OK',
                    'result': {}
                },
            }

        Error Response format::
            {
                {
                    'state': 'error',
                    'reason': '...'
                },
            }
        """
        body = json.loads(request.body)
        language = body.get('data', {}).get('language')
        basicfile = body.get('data', {}).get('basicfile')
        try:
            basicfile_object = BasicFile.objects.get(
                id=basicfile,
                language__name=language
            )
        except:
            return DeviceTalkErrorJsonResponse('Basicfile not found.', 400)
        remove_file_group(basicfile_object)
        return DeviceTalkJsonResponse()


class IndexView(View):
    """
    This View return the my_admin's index page.
    """
    http_method_names = [
        'get',
    ]

    def get(self, request, *args, **kwargs):
        if 0: #not request.user.is_authenticated:
            context = {
                'language': '',
                'languages': [],
                'username': '',
                'is_admin': False
            }
            return TemplateResponse(request, 'my_admin.html', context)

        # Get all language name
        languages = [
            item.name for item in Language.objects.all()
        ]

        
        
#        user_object = get_user_model().objects.get(
#            username=request.user.username
#        )
        


        context = {
            'language': languages[0],
            'languages': languages,
            'username':  'ADMIN',#user_object.username,
            'is_admin': 1, #user_object.is_admin
        }
        return TemplateResponse(request, 'my_admin.html', context)
