import configparser
import re
import jinja2
import traceback

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

__all__ = [
    'Language',
    'BasicFile',
    'Library',
    'DfType',
    'LibraryFunction',
    'SaFunction',
    'DeviceLibrary',
    'Device',
    'DeviceHasLibrary',
    'DeviceDf',
    'DeviceLibraryDf',
    'DeviceDfHasSaFunction',
    'DeviceLibraryDfHasSaFunction',
]


class Language(models.Model):
    name = models.CharField(
        max_length=30,
        blank=False
    )

    class Meta:
        unique_together = ['name']

    def __str__(self):
        return "%s" % (self.name)


class FileGroup(models.Model):
    name = models.CharField(
        max_length=100,
        blank=False
    )
    dir_path = models.CharField(
        max_length=255,
        blank=False,
        default='/'
    )

    class Meta:
        abstract = True

    def open(self, file_path, mode):
        file_object = self.file_set.get(file_path=file_path)
        return file_object.open(mode)


class BasicFile(FileGroup):
    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
    )

    class Meta:
        unique_together = ['name', 'language']

    def get_config(self, section, option):
        config_file_object = self.file_set.get(file_path='config.ini')
        config = configparser.ConfigParser()
        config.read(config_file_object.real_path)
        return config.get(section, option)

    def get_all_config(self):
        config_file_object = self.file_set.get(file_path='config.ini')
        config = configparser.ConfigParser()
        config.read(config_file_object.real_path)
        return {
            'template': config.get(*settings.BASICFILE_CONF_TEMPLATE_LIST).split(','),
            'device_lib_path': config.get(
                *settings.BASICFILE_CONF_DEVICE_LIB_PATH_LIST).split(','),
            'idf_template': config.get(*settings.BASICFILE_CONF_IDF_TEMPLATE),
            'odf_template': config.get(*settings.BASICFILE_CONF_ODF_TEMPLATE),
        }

    @property
    def lib_root(self):
        session = settings.BASICFILE_CONF_LIB_ROOT
        return self.get_config(*session)

    @property
    def lib_example_dir(self):
        session = settings.BASICFILE_CONF_LIB_EXAMPLE_DIR
        return self.get_config(*session)

    @property
    def manual(self):
        session = settings.BASICFILE_CONF_MANUAL
        return self.get_config(*session)

    def get_new_func_code(self, dftype, params_list, lib=None, lib_ref=None):
        """ This function render the SF^T code to SF* code.
            See the document for more detail.
        """
        try:
            template_string = None
            if dftype == 'idf' or dftype == 'odf':
                if dftype == 'idf':
                    template_file_path = self.get_config(
                        *settings.BASICFILE_CONF_IDF_TEMPLATE)
                else:
                    template_file_path = self.get_config(
                        *settings.BASICFILE_CONF_ODF_TEMPLATE)
                with self.open(template_file_path, 'r') as f:
                    template_string = f.read()
            tm = jinja2.Template(template_string)
        except:
            tb = traceback.format_exc()
            print(tb)
            return {
                'code': '(config.ini | new function file not found or jinja2 error)\n',
                'readonly_lines': [0],
            }

        # Create the render context of params information
        params = {
            'list': params_list,
            'set': set(params_list),
            'len': len(params_list),
            'set_len': len(set(params_list)),
        }
        # Create the render context of libs information
        # If not lib means, now is creating new sa-function.
        # otherwise means,  now is creating function from library-function.
        if not lib:
            lib = {
                k: ''
                for k in settings.LIB_FUNC_FIELDS
            }
        if not lib_ref:
            lib_ref = {
                'is_ref': False,
                'function_name': '',
                'library_name': ''
            }
        else:
            lib_ref['is_ref'] = True
        r = tm.render(params=params, lib=lib, lib_ref=lib_ref)
        # Delete all empty lines.
        r_split = r.split('\n')
        r_list = [
            r_split[i] for i in range(len(r_split))
            if not r_split[i].isspace() and r_split[i] != ''
        ]
        return {
            'code': '\n'.join(r_list),
            'readonly_lines': [i for i in range(len(r_list))],
        }

    def __str__(self):
        return '%d(%s)' % (self.id, self.name)


class Library(FileGroup):
    basic_file = models.ForeignKey(
        BasicFile,
        on_delete=models.CASCADE
    )
    global_var_setup = models.TextField(
        default=''
    )
    gvs_readonly_lines = models.JSONField(
        default=list
    )

    def __str__(self):
        return '%d(%s)' % (self.id, self.name)

    @property
    def f_id(self):
        return 'L%d' % self.id

    def delete(self, *args, **kwargs):
        # Delete all the file onjects before delete library object.
        files_objects = self.file_set.all()
        for file in files_objects:
            file.delete()
        return super().delete(*args, **kwargs)


class DfType(models.Model):
    class DF(models.TextChoices):
        IDF = 'idf', _('idf')
        ODF = 'odf', _('odf')
    df_type = models.CharField(
        _('Type'),
        max_length=10,
        choices=DF.choices,
        blank=False
    )
    params = models.JSONField(
        _('Parameters'),
        default=list,
    )

    class Meta:
        verbose_name = _('DfType')

    def __str__(self):
        return "%s:%s" % (
            self.df_type,
            str(self.params)
        )


class LibraryFunction(models.Model):
    library = models.ForeignKey(
        Library,
        on_delete=models.CASCADE,
    )
    name = models.CharField(
        max_length=100,
        blank=False
    )
    # Set all the value in LIB_FUNC_FIELDS as TextField
    for p in settings.LIB_FUNC_FIELDS:
        vars()[p] = models.TextField(blank=True)

    def __str__(self):
        return str(self.name)

    @property
    def f_id(self):
        return 'L%d' % self.id

    def get_content(self, dftype, params):
        # Create the render context of libs information
        lib_dict = {
            k: getattr(self, k, '')
            for k in settings.LIB_FUNC_FIELDS
        }
        lib_ref_dict = {
            'function_name': self.name,
            'library_name': self.library.name
        }
        # Get library-function content from new function template
        basic_file_object = self.library.basic_file
        gc = basic_file_object.get_new_func_code(dftype, params, lib_dict, lib_ref_dict)
        return {
            'func_id': self.id,
            'var_setup': getattr(self, settings.LIB_FUNC_VAR_SETUP_FIELD, ''),
            'code': gc['code'],
            'readonly_line': gc['readonly_lines'],
            'library_ref': -1
        }


class SaFunction(models.Model):
    name = models.CharField(
        max_length=100,
        blank=False
    )
    var_setup = models.TextField(blank=True)
    code = models.TextField()
    readonly_lines = models.JSONField(
        default=list
    )
    function_type = models.ForeignKey(
        DfType,
        on_delete=models.CASCADE
    )
    library_ref = models.ForeignKey(
        LibraryFunction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return "%d:%s(%s)" % (
            self.id,
            self.name,
            str(self.function_type)
        )

    def used_count(self):
        """ This function used at cleanup routine.
            Return the number of all devicelibrary and device that relate this sa-function.
        """
        return self.devicelibrary_set.count() + self.device_set.count()

    def is_same_code(self, var_setup, code, ro_line):
        """ This function check whether to sa-function content is same.
            Two sa-function is same iff all of their `code`, `var_setup`, `readonly_lines`
            are all same.
        """
        if code != self.code:
            return False
        if var_setup != self.var_setup:
            return False
        if ro_line != self.readonly_lines:
            return False
        return True

    @property
    def f_id(self):
        return 'D%d' % self.id

    def get_content(self):
        return {
            'func_id': self.id,
            'var_setup': self.var_setup,
            'code': self.code,
            'readonly_line': self.readonly_lines,
            'library_ref': -1 if not self.library_ref else self.library_ref.id
        }


class LibraryPoolBase(models.Model):
    name = models.CharField(
        max_length=100,
        blank=False
    )
    basic_file = models.ForeignKey(
        BasicFile,
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    global_var_setup = models.TextField(
        default=''
    )
    gvs_readonly_lines = models.JSONField(
        default=list
    )
    functions = models.ManyToManyField(
        SaFunction,
        blank=True
    )

    class Meta:
        abstract = True


class DeviceLibrary(LibraryPoolBase):
    dir_path = models.CharField(
        max_length=255,
        blank=False,
        default='/'
    )
    dependency_library = models.ManyToManyField(
        Library,
        blank=True
    )

    def __str__(self):
        return "%s{%s}[%s]" % (
            self.name,
            str(self.basic_file.language),
            str(self.user)
        )

    @property
    def f_id(self):
        return 'D%d' % self.id

    def add_df_functions(self, ddf_object):
        df_objects = self.df_set.filter(name=ddf_object.name)
        if len(df_objects) == 0:
            df_object = DeviceLibraryDf.objects.create(
                name=ddf_object.name,
                df_type=ddf_object.df_type,
                device_library=self
            )
        else:
            df_object = df_objects.first()
        df_object.set_json(ddf_object.content)


class Device(LibraryPoolBase):
    dm_name = models.CharField(
        _('Device Model Name'),
        max_length=100
    )
    server_url = models.CharField(
        max_length=255
    )
    device_address = models.CharField(
        max_length=50,
        default=''
    )
    push_interval = models.FloatField()

    class Meta:
        unique_together = ['name', 'dm_name', 'user']

    def __str__(self):
        return "%s: %s: %s" % (
            str(self.user),
            self.name,
            self.dm_name
        )

    # Return content of this device.
    @property
    def content(self):
        return {
            'DA': {
                'iottalk_server': self.server_url,
                'device_addr': self.device_address,
                'push_interval': self.push_interval
            },
            'SA': {
                'basic': {
                    'language': self.basic_file.language.name,
                    'basic_file': self.basic_file.id,
                    'global_var_setup': {
                        'content': self.global_var_setup,
                        'readonly_lines': self.gvs_readonly_lines,
                    }
                },
                'safuncs': {
                    dftype + 's': [
                        df.content
                        for df in self.df_set.filter(
                            df_type__df_type=dftype
                        )
                    ] for dftype in ('idf', 'odf')
                },
                'libs': [
                    libs.info
                    for libs in self.library_set.all()
                ],
                'safunction_list': [
                    {
                        'id': func.id,
                        'name': func.name,
                        'dftype': func.function_type.df_type,
                        'params': func.function_type.params,
                        'library_ref': None if not func.library_ref else func.library_ref.id
                    }
                    for func in self.functions.all()
                ]
            }
        }

    @content.setter
    def content(self, value):
        self.server_url = value['DA']['iottalk_server']
        self.device_addr = value['DA']['device_addr']
        self.push_interval = value['DA']['push_interval']
        self.global_var_setup = value['SA']['basic']['global_var_setup']['content']
        self.gvs_readonly_lines = value['SA']['basic']['global_var_setup']['readonly_lines']
        self.basic_file = BasicFile.objects.get(id=value['SA']['basic']['basic_file'])
        df_list = []
        df_list.extend(value['SA']['safuncs']['idfs'])
        df_list.extend(value['SA']['safuncs']['odfs'])
        for df in df_list:
            df_object = self.df_set.get(
                name=df['name']
            )
            df_object.set_json(df)
        self.library_set.all().delete()
        count = 0
        for lib_id in value['SA']['libs']:
            if lib_id[0] == 'L':
                library_objects = Library.objects.filter(id=int(lib_id[1:]))
                if len(library_objects) == 0:
                    continue
                DeviceHasLibrary.objects.create(
                    device=self,
                    library=library_objects.first(),
                    order=count
                )
                count += 1
            elif lib_id[0] == 'D':
                device_library_objects = DeviceLibrary.objects.filter(id=int(lib_id[1:]))
                if len(device_library_objects) == 0:
                    continue
                DeviceHasLibrary.objects.create(
                    device=self,
                    device_library=device_library_objects.first(),
                    order=count
                )
                count += 1
        self.functions.clear()
        for func_id in value['SA']['safunction_list']:
            self.functions.add(func_id)
        self.save()


class DeviceHasLibrary(models.Model):
    library = models.ForeignKey(
        Library,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    device_library = models.ForeignKey(
        DeviceLibrary,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='library_set'
    )
    order = models.BigIntegerField()

    class Meta:
        ordering = ('order',)

    @property
    def info(self):
        # Returns which library or device library this relationship object represents.
        if self.library:
            return "L%d" % self.library.id
        if self.device_library:
            return "D%d" % self.device_library.id
        return None


'''
Both `Device` and `DeviceLibrary` have a list of device-features.
Two Tables `DeviceDf` and `DeviceLibraryDf` is used to record two kind of df.
'''


class DeviceFeatureBase(models.Model):
    name = models.CharField(
        max_length=100,
        blank=False
    )
    df_type = models.ForeignKey(
        DfType,
        on_delete=models.CASCADE
    )

    class Meta:
        abstract = True

    def __str__(self):
        return "%s:%s" % (
            self.name,
            str(self.df_type)
        )

    @property
    def content(self):
        # Return the content in dict format.
        return {
            'name': self.name,
            'params': self.df_type.params,
            'functions': [
                {
                    'id': func_relation.function.id,
                    'var_setup': func_relation.var_setup,
                    'selected': func_relation.selected
                }
                for func_relation in self.function_relation_set.all()
            ]
        }

    def _set_json(self, value, RelationModel, relation_field, delete_flag):
        """ This function set the content from dict format.
            This parent fuction exists because `DeviceDf` and `DeviceLibraryDf` have
            difference relation table to `SaFunction`.
            Input::
                RelationModel: class object. Needs to be the relation table's object,
                           that is `DeviceDfHasSaFunction` or `DeviceLibraryDfHasSaFunction`
                relation_field: string. The feild's name of this DF table foreign key in the
                           relation table, that is `device` or `library`
                delete_flag: boolean. Whether to delete the old relation if the relationship
                           don't exist anaymore, that `device` sets to true and `library`
                           set to false.
            Output:: None
        """

        # {sa_func_id<int>: sa_func_object<SaFunction>}
        functions = {
            int(f['id']): f for f in value['functions']
        }

        # Check all the old function relation.
        func_relation_objects = self.function_relation_set.all()
        for func_relation_object in func_relation_objects:
            func_id = func_relation_object.function.id
            if func_id in functions:
                # If this relation exists in new function relation, udate the relation item.
                func_relation_object.var_setup = functions[func_id]['var_setup']
                func_relation_object.selected = functions[func_id]['selected']
                func_relation_object.save()
                del functions[func_id]
            else:
                # If this relation don't exist in new function relation.
                # For `DeviceDf`, needs to remove this relationship.
                # For `DeviceLibraryDf`, don't needs to remove this relationship,
                # just keep as the selection history.
                if delete_flag:
                    func_relation_object.delete()

        # Create new relation.
        for __, info in functions.items():
            fields = {
                'selected': info['selected'],
                'var_setup': info['var_setup'],
                'function_id': info['id'],
                relation_field: self
            }
            RelationModel.objects.create(**fields)

    def reset(self):
        self.functions.clear()

    @property
    def re_name(self):
        """ This function return the name that replace `-` to `_`
            This re-name is used as the variable name in the sa file,
            while `-` is not a valid token for variable's name.
        """
        return re.sub(r'-', r'_', self.name)


class DeviceDf(DeviceFeatureBase):
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='df_set'
    )
    functions = models.ManyToManyField(
        SaFunction,
        through='DeviceDfHasSaFunction',
        blank=True
    )

    def set_json(self, value):
        self._set_json(value, DeviceDfHasSaFunction, 'device', True)


class DeviceLibraryDf(DeviceFeatureBase):
    device_library = models.ForeignKey(
        DeviceLibrary,
        on_delete=models.CASCADE,
        related_name='df_set'
    )
    functions = models.ManyToManyField(
        SaFunction,
        through='DeviceLibraryDfHasSaFunction',
        blank=True
    )

    def set_json(self, value):
        self._set_json(value, DeviceLibraryDfHasSaFunction, 'device_library', False)


'''
The class `DeviceDfHasSaFunction` and `DeviceLibraryDfHasSaFunction` are the relation
table for `DeviceDf` and `LibraryDf` to `SaFunction`.
`DfHasSaFunctionBase` is the abstract class for them.
These relation tables are needed because that
two other fields `var_setup` and `selected` need to record in this relationship.
'''


class DfHasSaFunctionBase(models.Model):
    function = models.ForeignKey(
        SaFunction,
        on_delete=models.CASCADE,
    )
    var_setup = models.TextField(blank=True)
    selected = models.BooleanField(
        default=False
    )

    class Meta:
        abstract = True


class DeviceDfHasSaFunction(DfHasSaFunctionBase):
    device = models.ForeignKey(
        DeviceDf,
        on_delete=models.CASCADE,
        related_name='function_relation_set'
    )


class DeviceLibraryDfHasSaFunction(DfHasSaFunctionBase):
    device_library = models.ForeignKey(
        DeviceLibraryDf,
        on_delete=models.CASCADE,
        related_name='function_relation_set'
    )
