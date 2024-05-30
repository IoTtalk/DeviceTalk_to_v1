import json
import os
from urllib.parse import parse_qs

from django.conf import settings
from django.contrib.auth import get_user_model
from django.views.generic.base import View

from .utils import (
    ContentRender,
    copy_file,
    create_library,
    function_render,
    DeviceTalkJsonResponse,
    DeviceTalkErrorJsonResponse
)
from .models import (
    Language,
    BasicFile,
    Library,
    DfType,
    LibraryFunction,
    SaFunction,
    DeviceLibrary,
    Device,
    DeviceDf,
)
from file_handle.models import File
from xtalk_account.utils import check_login


class LibraryManagerView(View):
    '''
    Route: DEVICETALK_POSFIX/api/library/<str:language>/<int:basic_file_id>
    GET: Get the all the libraries information by language.
    PUT: Check the uploaded file's format and create library object
    '''
    http_method_names = [
        'get',
        'put'
    ]

    @check_login
    def get(self, request, *args, **kwargs):
        """ This function return the list of basic files’ information.
        Query param::
            username:

        Response format::
            {
                'state': 'OK',
                'result': {
                    'library_list': [
                        # The format of library
                        {
                            'id': "L10"  # Should br "L"+id
                            'name': "RPi_library",
                            'type': 'library',  # MUST be "library"
                            'dependency': [],
                            'functions': [
                                "GPIO_input", ...
                            ]  # List of its functions
                        },
                        # The format of device library
                        {
                            'id': "D5"  # Should br "D"+id
                            'name': "Dummy_library",
                            'type': 'device_library',  # MUST be "device_library"
                            'dependency': ["L10", ...], # List of libraries id
                            'functions': [
                                "GPIO_input", ...
                            ]  # List of its functions
                        },...
                    ]
                }
            }
        """
        language = kwargs.get('language', None)
        basic_file_id = kwargs.get('basic_file_id', None)
        if len(BasicFile.objects.filter(id=basic_file_id, language__name=language)) == 0:
            DeviceTalkErrorJsonResponse('Wrong language and basic file mapping.', 400)

        qs_body = parse_qs(request.GET.urlencode())
        username = qs_body.get('username', [None])[0]
        try:
            user_object = get_user_model().objects.get(username=username)
        except:
            return DeviceTalkErrorJsonResponse('User not found')

        library_list = []
        # Get the device-libraries
        # First, get all the user's device-libraries
        user_device_library_objects = DeviceLibrary.objects.filter(
            basic_file_id=basic_file_id,
            user=user_object
        )
        device_library_name_list = [
            device_object.name for device_object in user_device_library_objects
        ]
        device_library_list = [
            device_object for device_object in user_device_library_objects
        ]

        # Then, get all the global device-libraries
        # global device-library <=> user == None
        global_device_library_objects = DeviceLibrary.objects.filter(
            basic_file_id=basic_file_id,
            user=None
        )
        for device_object in global_device_library_objects:
            if device_object.name in device_library_name_list:
                # Two library with same name will confuse user.
                # If there is a non-global device-library with the same name,
                # skip the global device-library
                continue
            device_library_list.append(device_object)
            device_library_name_list.append(device_object.name)

        for device_library_object in device_library_list:
            library_list.append({
                'id': device_library_object.f_id,
                'name': device_library_object.name,
                'type': 'device_library',
                'dependency': [
                    lib.f_id
                    for lib in device_library_object.dependency_library.all()
                ],
                'functions': [
                    func.name
                    for func in device_library_object.functions.all()
                ]
            })

        # Get all libaries
        library_objects = Library.objects.filter(
            basic_file_id=basic_file_id,
        )
        for library_object in library_objects:
            library_list.append({
                'id': library_object.f_id,
                'name': library_object.name,
                'type': 'library',
                'dependency': [],
                'functions': [
                    func.name
                    for func in library_object.libraryfunction_set.all()
                ]
            })
        library_list.sort(key=lambda x: x['name'])

        return DeviceTalkJsonResponse({
            'library_list': library_list
        })

    def put(self, request, *args, **kwargs):
        """ This function check the uploaded file's format and create library object
        Request format::
            {
                'state': "completed" | "failed",
                'file_upload_id': <file_uploaded_id>,
                'language': '<language>',
            }

        Sucess Response format::
            {
                'state': 'OK',
                'result': {}
            }

        Error Response format::
            {
                'state': 'error',
                'reason': '...'
            }
        """
        language = kwargs.get('language', None)
        basic_file_id = kwargs.get('basic_file_id', None)

        body = json.loads(request.body)
        state = body['data'].get('state', None)
        file_upload_id = body['data'].get('file_upload_id', None)

        err_msg, code = create_library(
            language,
            basic_file_id,
            file_upload_id,
            state,
        )
        if err_msg:
            return DeviceTalkErrorJsonResponse(err_msg, code)
        else:
            return DeviceTalkJsonResponse()


class ListFunctionManagerView(View):
    '''
    Route: DEVICETALK_POSFIX/api/function
    GET: Get the list of function by libraries
    '''
    http_method_names = [
        'get',
    ]

    @check_login
    def get(self, request, *args, **kwargs):
        """ This function return the list of basic files’ information.
        Query param::
            libs:  The list of libs sorted by selection order.
                Example: ?libs=L1&libs=D3&libs=D1
                    means the selection order is L1->D3->D1
                    L1 is Library (id=1)
                    D3 is Device Library (id=3)
                    D1 is Device Library (id=1)

        Response format::
            {
                'state': 'OK',
                'result': {
                    'safunction_list': [
                        {
                            'id': 10,  # the id of this sa function
                            'name': "random",
                            'dftype': "idf",
                            'params': ["int", ],
                            'library_ref': None | 1  # the id of imported library function
                        }, ...
                    ],
                    'df_safuncs': {
                        'idfs':[
                            # The object of DF context.
                            {
                                'name': "DummySensor-I",
                                'params': ["int", ],
                                'functions': [
                                    {
                                        'id': 10,  # This means SA-function(id=10) is in
                                                     the pull downlist of "DummySensor-I"
                                        'var_setup': "...",
                                    }, ...
                                ]
                            }, ...
                        ],
                        'odfs':[
                            {
                                # Same as the format in IDFs list.
                            }, ...
                        ],
                    },
                    'libfunction_list': [
                        {
                            'id': "L1",  # the id of library
                            'name': "RPi_library",
                            'functions': [
                                {
                                    'id': 12,  # the id of library function in this library
                                    'name': "GPIO_input"
                                }, ...
                            ]
                        }, ...
                    ],
                    'global_var_setup': {
                        'content': '...',
                        'readonly_lines': []
                    },
                }
            }
        """
        qs_body = parse_qs(request.GET.urlencode())
        libs = qs_body.get('libs', [])
        libs.reverse()

        # Init the result list
        safunction_list = []
        df_safuncs = {'idfs': [], 'odfs': []}
        safunction_name_list = []
        df_safuncs_name = {'idfs': [], 'odfs': []}
        safunction_libref_id_list = []
        lib_function_list = []
        global_var = {
            'readonly': [],
            'editable': []
        }

        # This function update the global_var_setup's content by library_object.
        # The rules:
        #     Merge all the `read-only` part to the top
        #     If there two lines with same instruction in different libraries,
        #         use the first one and ignore the latter one. Cause the for loop
        #         below visit the later library first, we need to remove the previoues
        #         ones if same instruction appears.
        def update_global_var_setup_content(library_object):
            readonly = []
            editable = []
            content_lines = library_object.global_var_setup.split('\n')
            readonly_lines = library_object.gvs_readonly_lines
            for i in range(len(content_lines)):
                if i in readonly_lines:
                    readonly.append(content_lines[i])
                else:
                    editable.append(content_lines[i])
            for line in readonly:
                if line in global_var['editable']:
                    global_var['editable'].remove(line)
                if line in global_var['readonly']:
                    global_var['readonly'].remove(line)
            for line in editable:
                if line in global_var['editable']:
                    global_var['editable'].remove(line)
            global_var['readonly'] = readonly + global_var['readonly']
            global_var['editable'] = editable + global_var['editable']

        # This function update the safunction_list by function_object.
        def insert_sa_functions(function_object):
            # If already exist SaFunction with same name.
            # Skip this SaFunction.
            if function_object.name not in safunction_name_list:
                # If this SaFunction ref a library, but that library isn't selected
                # Skip this SaFunction.
                if function_object.library_ref:
                    if function_object.library_ref.f_id not in libs:
                        return
                safunction_name_list.append(function_object.name)
                library_ref = function_object.library_ref
                safunction_list.append({
                    'id': function_object.id,
                    'name': function_object.name,
                    'dftype': function_object.function_type.df_type,
                    'params': function_object.function_type.params,
                    'library_ref': None if not library_ref else library_ref.id
                })
                # Add this function's imported library-function's id in
                # `safunction_libref_id_list`
                if function_object.library_ref:
                    safunction_libref_id_list.append(function_object.library_ref.id)

        for lib in libs:
            if lib[0] == 'D':
                try:
                    device_library_object = DeviceLibrary.objects.get(id=int(lib[1:]))
                except:
                    continue
                update_global_var_setup_content(device_library_object)
                for funcs in device_library_object.functions.all():
                    insert_sa_functions(funcs)
                # Insert df's function
                for idf in device_library_object.df_set.filter(df_type__df_type='idf'):
                    if idf.name not in df_safuncs_name['idfs']:
                        df_safuncs_name['idfs'].append(idf.name)
                        df_safuncs['idfs'].append(idf.content)
                for odf in device_library_object.df_set.filter(df_type__df_type='odf'):
                    if odf.name not in df_safuncs_name['odfs']:
                        df_safuncs_name['odfs'].append(odf.name)
                        df_safuncs['odfs'].append(odf.content)

            elif lib[0] == 'L':
                try:
                    library_object = Library.objects.get(id=int(lib[1:]))
                except:
                    continue
                update_global_var_setup_content(library_object)
                library_object_info = {
                    'id': library_object.f_id,
                    'name': library_object.name,
                    'functions': [
                        {
                            'id': func.id,
                            'name': func.name
                        }
                        for func in library_object.libraryfunction_set.all()
                    ]
                }
                # Insert this library's infomation only if this library include
                # library-function
                if len(library_object_info['functions']) > 0:
                    lib_function_list.append(library_object_info)

        # This for loop check that
        # for all the library-function have even imported by one of the SA-function,
        # there must at last one of the SA-function been selected
        for lib in libs:
            if lib[0] == 'L':
                try:
                    library_object = Library.objects.get(id=int(lib[1:]))
                except:
                    continue
                # Check if this library has library function
                for lib_func in library_object.libraryfunction_set.all():
                    if len(lib_func.safunction_set.all()) == 0:
                        continue
                    # If this library-function have even imported by SA-function
                    # but none of them been selected, add the last relation SA-function
                    if lib_func.id not in safunction_libref_id_list:
                        function_object = lib_func.safunction_set.last()
                        if function_object.name not in safunction_name_list:
                            safunction_name_list.append(function_object.name)
                            library_ref = function_object.library_ref
                            safunction_list.append({
                                'id': function_object.id,
                                'name': function_object.name,
                                'dftype': function_object.function_type.df_type,
                                'params': function_object.function_type.params,
                                'library_ref': None if not library_ref else library_ref.id
                            })

        global_var_setup = {
            'content': '\n'.join(global_var['readonly'] + global_var['editable']),
            'readonly_lines': [i for i in range(len(global_var['readonly']))]
        }
        return DeviceTalkJsonResponse({
            'safunction_list': safunction_list,
            'df_safuncs': df_safuncs,
            'libfunction_list': lib_function_list,
            'global_var_setup': global_var_setup
        })


class NewFunctionManagerView(View):
    '''
    GET: Get new sa function's template.
        Route: DEVICETALK_POSFIX/api/function/new/<str:language>/<int:basic_file>
    PUT: Save new sa function.
        Route: DEVICETALK_POSFIX/api/function/new
    '''
    http_method_names = [
        'get',
        'put'
    ]

    @check_login
    def get(self, request, *args, **kwargs):
        """ This function get new sa function's template.

        URL param::
            language: language name
            basic_file: ID of the basic_file

        Query param::
            dftype: must be "idf" or "odf".
            params: list of params.

        Sucess Response format::
            {
                'state': 'OK',
                'result': {
                    'func_id': -1,
                    'var_setup': "",
                    'code': "...",
                    'readonly_line': [0, 1, 3, ...],
                    'library_ref': -1
                }
            }

        Error Response format::
            {
                'state': 'error',
                'reason': '...'
            }
        """
        language = kwargs.get('language', None)
        basic_file_id = kwargs.get('basic_file', None)
        qs_body = parse_qs(request.GET.urlencode())
        dftype = qs_body.get('dftype', [None])[0]
        params = qs_body.get('dfparam', [None])

        if dftype != 'idf' and dftype != 'odf':
            DeviceTalkErrorJsonResponse('Wrong df type', 400)

        try:
            language_object = Language.objects.get(name=language)
        except:
            DeviceTalkErrorJsonResponse('Language not found')
        # Get new function code from basic file
        try:
            basic_file_object = language_object.basicfile_set.get(id=basic_file_id)
        except:
            DeviceTalkErrorJsonResponse('Basic file not found')
        gc = basic_file_object.get_new_func_code(
            dftype,
            params
        )
        return DeviceTalkJsonResponse({
            'func_id': -1,
            'var_setup': '',
            'code': gc['code'],
            'readonly_line': gc['readonly_lines'],
            'library_ref': -1
        })

    def put(self, request, *args, **kwargs):
        """ This function save new sa function.

        URL param::
            language: language name
            basic_file: ID of the basic_file

        Request format::
            {
                'func_name': "random",
                'dftype': 'idf',  # Should be 'idf' or 'odf'
                'params': ["int",...],  # List of params
                'var_setup': "...",
                'code': "...",
                'readonly_lines': [0, 1, 4, ...],
                'library_ref': 2  # the id the of ref's library-function
            }

        Sucess Response format::
            {
                'state': 'OK',
                'result': {
                    'func_id': 15
                }
            }

        Error Response format::
            {
                'state': 'error',
                'reason': '...'
            }
        """
        body = json.loads(request.body)
        func_name = body['data'].get('func_name')
        dftype = body['data'].get('dftype')
        params = body['data'].get('params')
        var_setup = body['data'].get('var_setup', "")
        code = body['data'].get('code', "")
        readonly_lines = body['data'].get('readonly_line', [])
        library_ref = body['data'].get('library_ref')

        if dftype != 'idf' and dftype != 'odf':
            DeviceTalkErrorJsonResponse('Wrong df type', 400)

        dftype_object, _ = DfType.objects.get_or_create(
            df_type=dftype,
            params=params
        )
        safunc_object = SaFunction.objects.create(
            name=func_name,
            var_setup=var_setup,
            code=code,
            readonly_lines=readonly_lines,
            function_type=dftype_object,
            library_ref_id=library_ref
        )

        return DeviceTalkJsonResponse({
            'func_id': safunc_object.id,
        })


class SingleFunctionManagerView(View):
    '''
    Route: DEVICETALK_POSFIX/api/function/<str:function_type>/<int:function_id>
    GET: Get the sa-function's or library-function's content.
    POST: Update the sa-function's content.
    '''
    http_method_names = [
        'get',
        'post'
    ]

    @check_login
    def get(self, request, *args, **kwargs):
        """ This function get the sa-function's or library-function's content.

        Url Params::
            func_id: the id of the function
            func_type: should be "S" or "L"
                "S": SA function
                "L": Library function

        Query param::
            dftype: must be "idf" or "odf".
            params: list of params.

        Sucess Response format::
            {
                'state': 'OK',
                'result': {
                    'func_id': 10,
                    'var_setup': "...",
                    'code': "...",
                    'readonly_line': [0, 1, 3, ...],
                    'library_ref': 5
                }
            }

        Error Response format::
            {
                'state': 'error',
                'reason': '...'
            }
        """
        func_id = int(kwargs['function_id'])
        func_type = kwargs['function_type']
        qs_body = parse_qs(request.GET.urlencode())
        dftype = qs_body.get('dftype', [None])[0]
        params = qs_body.get('dfparam', [None])

        if func_type != 'S' and func_type != 'L':
            DeviceTalkErrorJsonResponse('Wrong function type', 400)

        if func_type == 'S':
            safunc_objects = SaFunction.objects.filter(id=int(func_id))
            if len(safunc_objects) == 0:
                return DeviceTalkErrorJsonResponse('Function not found')
            safunc_object = safunc_objects.first()
            response_result = safunc_object.get_content()

        else:  # func_type == 'L'
            libfunc_objects = LibraryFunction.objects.filter(id=int(func_id))
            if len(libfunc_objects) == 0:
                return DeviceTalkErrorJsonResponse('Function not found')
            libfunc_object = libfunc_objects.first()
            response_result = libfunc_object.get_content(dftype, params)

        return DeviceTalkJsonResponse(response_result)

    def post(self, request, *args, **kwargs):
        """ This function update the sa-function's content.

        Request format::
            {
                'func_id': 10,
                'func_type': "S",  # MUST be "S"
                'func_name': "random",
                'dftype': 'idf',  # Should be 'idf' or 'odf'
                'params': ["int",...],  # List of params
                'var_setup': "...",
                'code': "...",
                'readonly_lines': [0, 1, 4, ...],
                'library_ref': 2  # the id the of ref's library-function
            }

        Sucess Response format::
            {
                'state': 'OK',
                'result': {
                    'func_id': 15
                }
            }

        Error Response format::
            {
                'state': 'error',
                'reason': '...'
            }
        """
        body = json.loads(request.body)
        func_id = int(kwargs['function_id'])
        func_type = kwargs['function_type']

        func_name = body['data'].get('func_name')
        dftype = body['data'].get('dftype')
        params = body['data'].get('params')
        var_setup = body['data'].get('var_setup', "")
        code = body['data'].get('code', "")
        readonly_lines = body['data'].get('readonly_line', [])
        library_ref = body['data'].get('library_ref')

        if func_type != 'S':
            DeviceTalkErrorJsonResponse('Wrong function type', 400)

        try:
            safunc_object = SaFunction.objects.get(id=func_id)
        except:
            return DeviceTalkErrorJsonResponse('Function not found')

        # If the target function already used by other device-library
        # Save as new function to avoid overwrite.
        if len(safunc_object.devicelibrary_set.all()) > 0:
            dftype_object, _ = DfType.objects.get_or_create(
                df_type=dftype,
                params=params
            )
            safunc_object = SaFunction.objects.create(
                name=func_name,
                var_setup=var_setup,
                code=code,
                readonly_lines=readonly_lines,
                function_type=dftype_object,
                library_ref_id=library_ref
            )
        else:
            safunc_object.code = code
            safunc_object.var_setup = var_setup
            safunc_object.readonly_lines = readonly_lines
        safunc_object.save()

        return DeviceTalkJsonResponse({
            'func_id': safunc_object.id,
        })


class DeviceManagerView(View):
    '''
    GET: Get the device's content and selected libraries info.
    POST: Upload the device's metadata and create SA code.
    '''
    http_method_names = [
        'get',
        'post'
    ]

    @check_login
    def get(self, request, *args, **kwargs):
        """ This function get the device's content and selected libraries info.

        Query param::
            dm_name: the device model name
            d_name: the device name
            username: the username

        Sucess Response format::
            {
                'state': 'OK',
                'result': {
                    'device': {...}  # Detail format: api.models.Device.content
                    'libfunction_list': [
                        # List of library infomation
                        {
                            'id': "L10",  # id of api.models.Library
                            'name': "RPi_library",
                            'functions': [
                                {
                                    'id': 20,  # id of api.models.LibraryFunction
                                    'name': "GPIO_input"
                                },...
                            ]
                        },...
                    ]
                }
            }

        Error Response format::
            {
                'state': 'error',
                'reason': '...'
            }
        """
        qs_body = parse_qs(request.GET.urlencode())
        dm_name = qs_body.get('dm_name', [None])[0]
        d_name = qs_body.get('d_name', [None])[0]
        username = qs_body.get('username', [None])[0]

        # Get device object
        device_objects = Device.objects.filter(
            dm_name=dm_name,
            name=d_name,
            user=None
        )
        user_device_objects = Device.objects.filter(
            dm_name=dm_name,
            name=d_name,
            user__username=username
        )
        # First check if there is device belong to the user.
        if len(user_device_objects) > 0:
            device_object = user_device_objects.first()
        # Then check if there is global device (user == None).
        elif len(device_objects) > 0:
            device_object = device_objects.first()
        # Response error if device not found.
        else:
            return DeviceTalkErrorJsonResponse('Device not found')

        # Collect libraries information
        lib_function_list = []
        for lib_ref in device_object.library_set.all():
            # Ignore device-library. It function infomation is in device's
            # content already.
            if lib_ref.library:
                library_object = lib_ref.library
                library_object_info = {
                    'id': library_object.f_id,
                    'name': library_object.name,
                    'functions': [
                        {
                            'id': func.id,
                            'name': func.name
                        }
                        for func in library_object.libraryfunction_set.all()
                    ]
                }
                if len(library_object_info['functions']) > 0:
                    lib_function_list.append(library_object_info)

        return DeviceTalkJsonResponse({
            'device': device_object.content,
            'libfunction_list': lib_function_list
        })

    def post(self, request, *args, **kwargs):
        """ This function upload the device's metadata and create SA code.

        Request format::
            {
                'is_new': True | False,  # True means create new device
                'dm_result': the dm_result,
                'd_name': 'Dummy_demo',
                'username': 'IoTtalk',
                'content': {...}  # Detail format: api.models.Device.content
            }

        Sucess Response format::
            {
                'state': 'OK',
                'result': {
                    'zip_path': '/upload/result/...',  # The url to get the zip file
                    'zip_name': 'Dummy_demo.zip'
                }
            }

        Error Response format::
            {
                'state': 'error',
                'reason': '...'
            }
        """
        try:
            body = json.loads(request.body)
            is_new = body['data'].get('is_new')
            dm_result = body['data'].get('dm_result')
            d_name = body['data'].get('d_name')
            content = body['data'].get('content')
            username = body['data'].get('username')
        except:
            DeviceTalkErrorJsonResponse('Wrong request parameter.', 400)

        user_object = get_user_model().objects.get(username=username)
        language = content['SA']['basic']['language']
        basic_file_id = content['SA']['basic']['basic_file']
        dm_name = dm_result['dm']['name']

        # Check language name and basic file id
        if len(BasicFile.objects.filter(id=basic_file_id, language__name=language)) == 0:
            DeviceTalkErrorJsonResponse('Wrong language and basic file mapping.', 400)

        # Save device
        device_object = None
        new_device_is_global = True

        device_objects = Device.objects.filter(
            dm_name=dm_name,
            name=d_name
        )
        if len(device_objects) > 0:
            new_device_is_global = False
        device_objects = device_objects.filter(user=user_object)
        if len(device_objects) > 0:
            device_object = device_objects.first()

        if is_new:
            device_object = None

        if not device_object:
            device_object = Device.objects.create(
                dm_name=dm_name,
                name=d_name,
                server_url=content['DA']['iottalk_server'],
                device_address=content['DA']['device_addr'],
                push_interval=content['DA']['push_interval'],
                basic_file=BasicFile.objects.get(id=basic_file_id),
                user=None if new_device_is_global else user_object,
            )

            # Create new file object.
            device_file_file_path = d_name + '.zip'
            device_file_uuid_code = File.uuid_generate()
            device_file_real_path = '%s/%s.zip' % (
                settings.RESULT_DIR + device_file_uuid_code.hex,
                d_name
            )
            File.objects.create(
                file_path=device_file_file_path,
                real_path=device_file_real_path,
                uuid=device_file_uuid_code,
                is_upload=True,
                device=device_object
            )

            # Create all the dfs object.
            # No matter that df is used in this device.
            for df_type in ('idf', 'odf'):
                df_list = dm_result[df_type]
                for df in df_list:
                    dftype_object, _ = DfType.objects.get_or_create(
                        df_type=df_type,
                        params=df['df_type']
                    )
                    DeviceDf.objects.create(
                        name=df['name'],
                        df_type=dftype_object,
                        device=device_object,
                    )

        # Update device's content.
        device_object.content = content
        device_object.save()

        # Create the device-library
        config_result = device_object.basic_file.get_all_config()

        # Not all df is used in this device.
        # Create a list with all the used df's name.
        used_df_list = []
        for df_type in ('idf', 'odf'):
            for df in dm_result[df_type]:
                if df['used'] == 1:
                    used_df_list.append(df['name'])

        # Create the render context
        jinja2_render_data = {
            'sa': {
                'device_name': device_object.name,
                'global_variable_setup': device_object.global_var_setup
            },
            'da': {
                'server_url': device_object.server_url,
                'device_model': device_object.dm_name,
                'device_addr': device_object.device_address,
                'push_interval': device_object.push_interval,
            },
            'functions': [
                function_render(df_object)
                for df_object in device_object.df_set.all()
                if df_object.name in used_df_list
            ],
            'idf': {
                'name_list': [
                    idf_object.name
                    for idf_object in device_object.df_set.filter(df_type__df_type='idf')
                    if idf_object.name in used_df_list
                ],
                'info': [
                    {
                        'name': idf_object.name,
                        'func_name': idf_object.re_name,
                        'params': {
                            'list': idf_object.df_type.params,
                            'set': set(idf_object.df_type.params),
                            'len': len(idf_object.df_type.params),
                            'set_len': len(set(idf_object.df_type.params)),
                        }
                    }
                    for idf_object in device_object.df_set.filter(df_type__df_type='idf')
                    if idf_object.name in used_df_list
                ]
            },
            'odf': {
                'name_list': [
                    odf_object.name
                    for odf_object in device_object.df_set.filter(df_type__df_type='odf')
                    if odf_object.name in used_df_list
                ],
                'info': [
                    {
                        'name': odf_object.name,
                        'func_name': odf_object.re_name,
                        'params': {
                            'list': odf_object.df_type.params,
                            'set': set(odf_object.df_type.params),
                            'len': len(odf_object.df_type.params),
                            'set_len': len(set(odf_object.df_type.params)),
                        }
                    }
                    for odf_object in device_object.df_set.filter(df_type__df_type='odf')
                    if odf_object.name in used_df_list
                ]
            },
        }
        jinja2_content_render = ContentRender(jinja2_render_data)

        # New lib file
        # render the lib path from format-string. Ex:
        # config_result['device_lib_path'][0]: libraries/{sa[device_name]}_library/...
        # new_lib_file_path: libraries/Dummy_demo_library/...
        new_lib_file_path = jinja2_content_render.render_string(
            config_result['device_lib_path'][0], False
        )
        # Get the new_library_name. Ex:
        # new_lib_file_path: libraries/Dummy_demo_library/...
        # device_object.basic_file.lib_root: libraries/
        # After os.path.relpath the result become `Dummy_demo_library/...`,
        # so the library name is at first item of the path.
        lib_root = device_object.basic_file.lib_root
        new_lib_file_path = os.path.relpath(
            new_lib_file_path, device_object.basic_file.lib_root
        )
        new_library_name = new_lib_file_path.split('/')[0]

        # Save device library

        # If the exist device-library with same name
        # Set new device-library non-global.
        device_lib_objects = DeviceLibrary.objects.filter(
            basic_file__language__name=language,
            name=new_library_name
        )
        new_dl_is_global = len(device_lib_objects) == 0

        device_lib_objects = device_lib_objects.filter(
            user=user_object
        )
        # If this user already saved this device, device_lib_objects won't be empty
        # after the filter.
        if len(device_lib_objects) == 0:
            # Create new device-library.
            device_lib_object = DeviceLibrary.objects.create(
                name=new_library_name,
                basic_file=device_object.basic_file,
                user=None if new_dl_is_global else device_object.user,
                global_var_setup=device_object.global_var_setup,
                dir_path=('%s/' % (new_library_name)),
            )
            new_lib_uuid_code = File.uuid_generate()
            new_lib_real_path = settings.FILE_UPLOAD_DIR + new_lib_uuid_code.hex
            # Get file extension name. ex: 'zip'
            file_extension = new_lib_file_path.split('/')[-1].split('.')[-1]
            if len(file_extension) > 1:
                new_lib_real_path = new_lib_real_path + '.' + file_extension
            File.objects.create(
                file_path=new_lib_file_path,
                real_path=new_lib_real_path,
                uuid=new_lib_uuid_code,
                device_library=device_lib_object,
                is_upload=True
            )
        else:
            # Just over-write the existed device-library.
            device_lib_object = device_lib_objects.first()

        # Get SA template from basic file and write the result into device-library file.
        with device_object.basic_file.open(config_result['device_lib_path'][0], 'r') as f:
            new_lib_file_template = f.read()
        with device_lib_object.file.first().open('w') as f:
            content_string = jinja2_content_render.render_string(new_lib_file_template)
            f.write(content_string)

        # Copy all the functions' relation from device to device-library.
        # device's related functions
        device_lib_object.functions.clear()
        for func in device_object.functions.all():
            device_lib_object.functions.add(func)
        # device's related libraries
        device_lib_object.dependency_library.clear()
        for lib in device_object.library_set.all():
            if lib.library:
                device_lib_object.dependency_library.add(lib.library)
        # all df's related libraries
        for df in device_object.df_set.all():
            device_lib_object.add_df_functions(df)
        # global variable's settings.
        device_lib_object.global_var_setup = device_object.global_var_setup
        device_lib_object.gvs_readonly_lines = device_object.gvs_readonly_lines
        device_lib_object.save()

        # Generate SA code
        dst_outer_dir = '/'.join(device_object.file.real_path.split('/')[:-1])
        dst_dir = '%s/%s/' % (
            dst_outer_dir,
            d_name
        )
        # Get all SA code's file objects.
        basic_files = [
            file for file in device_object.basic_file.file_set.all()
        ]
        # Get the list of all dependency library's file objects.
        lib_files = [
            [file for file in library.file_set.all()]
            for library in device_lib_object.dependency_library.all()
        ]
        # Append device-library's file objects into the list.
        lib_files.append([file for file in device_lib_object.file.all()])
        # Flat 2D list to 1D list.
        lib_files = sum(lib_files, [])

        # Render templates to file or copy other files to the dest. dir.
        # Ignore config file, device-library template(device_lib_path),
        # new sa function template (idf_template, odf_template)
        for file in basic_files:
            if file.file_path in config_result['template']:
                jinja2_content_render.render_file(file, dst_dir + file.file_path)
            elif file.file_path == settings.BASICFILE_CONF_FILENAME:
                pass
            elif file.file_path in config_result['idf_template']:
                pass
            elif file.file_path in config_result['odf_template']:
                pass
            elif file.file_path in config_result['device_lib_path']:
                pass
            else:
                copy_file(file, os.path.join(dst_dir, file.file_path))
        # Copy all the libraries files
        for file in lib_files:
            # Need to add lib_root in front all the files
            copy_file(file, os.path.join(dst_dir, lib_root, file.file_path))
        # Zip the dir
        exec_str = 'cd %s; zip -FSr %s.zip %s > /dev/null; rm -r %s/' % (
            dst_outer_dir,
            d_name,
            d_name,
            d_name,
        )
        os.system(exec_str)

        return DeviceTalkJsonResponse({
            'zip_path': device_object.file.url,
            'zip_name': device_object.file.file_path
        })
