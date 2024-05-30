import errno
import jinja2
import json
import os
import re
import shutil
import traceback

from django.conf import settings
from django.http import JsonResponse

from .models import (
    BasicFile,
    DeviceDfHasSaFunction,
    Library,
    LibraryFunction,
)
from file_handle.models import UploadBatch
from my_admin.utils import remove_file_group


class ContentRender:
    """ This class hold a context.
        When calling `render_string` or `render_file`, this class will
        use Jinja2 or str-format to render the input-data using self.ctx,
        and return the result string or save to a file.
    """
    def __init__(self, context, env=None):
        self.ctx = context
        self.env = env
        if self.env:
            self.render_function = self.env.from_string
        else:
            self.render_function = jinja2.Template

    def render_string(self, input_string, render_flag=True):
        """ This function input template and return the result in string format
        Args:
           input_string (str): The template string.
           render_flag (bool): Default value is True
               render_flag == True means using jinja2
               render_flag == False means using str.format

        Returns:
           str.  The render result::

        """
        if render_flag:
            tm = self.render_function(input_string)
            return tm.render(self.ctx)
        else:
            return input_string.format(**self.ctx)

    def render_file(self, file_object, dst):
        """ This function input template and return the result in string format
        Args:
           file_object (file_handle.models.File): The template's target file.
           dst (str): The render result should be written in this file.

        Returns:
           None

        """
        try:
            with file_object.open('r') as f:
                tem_str = f.read()
            r = self.render_string(tem_str)
        except Exception as e:
            # traceback.print_stack()
            traceback.print_tb(e)
            return
        # Create the file's dir if not exist.
        if not os.path.exists(os.path.dirname(dst)):
            try:
                os.makedirs(os.path.dirname(dst))
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
        # Write the result in the dst file.
        with open(dst, 'w') as s:
            s.write(r)


class ExampleParser:
    """ This class read the example file and parse all the sections in it.
        See the document for more detail.
    """
    def __init__(self, f):
        """
            Input::
                f: python's open object(class `_io.TextIOWrapper`)
        """
        self.__content_lines = f.readlines()
        self.__sections = {}
        self.__to_section()

    def __to_section(self):
        # init `section_name` to `_`
        section_name = '_'
        # Parse the file content line by line.
        for line in self.__content_lines:
            re_result = re.search(r'^(#|\/{2}) \*\*\*\[(\w+)\]\*\*\*', line)
            if re_result:
                # If that line match this pattern, this is the start of a section.
                section_name = re_result.group(2)
                self.__sections[section_name] = []
            elif section_name:
                self.__sections[section_name].append(line)

        # Combine all lines to a string in sections.
        # Ex: ['Hi', '  Hello'] => 'Hi\n  Hello'
        for k in self.__sections:
            self.__sections[k] = ''.join(self.__sections[k])

    def __getitem__(self, value):
        if value in self.__sections:
            return self.__sections[value]
        else:
            return None

    def all_valid_sections(self):
        r = {}
        # Only return the sections in LIB_FUNC_FIELDS
        # ignore the others.
        for k in self.__sections:
            if k in settings.LIB_FUNC_FIELDS:
                r[k] = self.__sections[k]
        return r


class DeviceTalkJsonResponse(JsonResponse):
    def __init__(self, data={}):
        super().__init__({
            'state': 'OK',
            'result': data
        })


class DeviceTalkErrorJsonResponse(JsonResponse):
    def __init__(self, reason, status=404):
        super().__init__(
            {
                'state': 'error',
                'reason': reason
            },
            status=status
        )


def copy_file(file_object, dst):
    # This function copy the file_object's file to the path of `dst`
    if not os.path.exists(os.path.dirname(dst)):
        try:
            os.makedirs(os.path.dirname(dst))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
    shutil.copy(file_object.real_path, dst)


def function_render(device_df):
    """ This function render the SF* code to SF code.
        See the document for more detail.
    """

    # Get the selected SaFunction relation.
    df_function_select_object = DeviceDfHasSaFunction.objects.filter(
        device=device_df,
        selected=True
    ).first()
    df_function_object = df_function_select_object.function

    code = df_function_object.code
    code_list = code.split('\n')
    var_setup_start_line = -1
    # Replace `{*variable_setup*}` to `{*variable_setup|indent(indent_num)*}`
    for i in range(len(code_list)):
        indent_num = code_list[i].find('{*variable_setup*}')
        if indent_num >= 0:
            var_setup_start_line = i
            var_setup_indent_num = indent_num
            code_list[i] = code_list[i].replace(
                '{*variable_setup*}',
                '{*variable_setup|indent(%d)*}' % indent_num
            )
            break
    code = '\n'.join(code_list)
    jinja2_content_render = ContentRender(
        {
            'variable_setup': df_function_select_object.var_setup,
            'df_name': device_df.re_name,
            'new_line': ''
        },
        jinja2.Environment('{%', '%}', '{*', '*}', '{#', '#}', loader=jinja2.BaseLoader)
    )
    final_code = jinja2_content_render.render_string(code)
    return {
        'content': final_code,
        'name': df_function_object.name,
        'type': df_function_object.function_type.df_type,
        'var_setup': df_function_select_object.var_setup,
        'var_setup_start_line': var_setup_start_line,
        'var_setup_indent_num': var_setup_indent_num,
        'lines': len(code_list),
        'ro_lines': df_function_object.readonly_lines
    }


def create_library(language, basic_file_id, file_upload_id, state):
    try:
        upload_batch_object = UploadBatch.objects.get(id=int(file_upload_id))
        basic_file_object = BasicFile.objects.get(id=basic_file_id)
    except:
        return 'Upload Batch ID or Language not found', 404

    if BasicFile.objects.filter(id=basic_file_id, language__name=language).count() == 0:
        return 'Wrong language and basic file mapping.', 400

    # state == 'failed' means the front-end get at least one error response during
    # uploading file. In this case, just delete all the uploaded file and ignore
    # this upload process.
    if state == 'failed':
        remove_file_group(upload_batch_object)
        return '', 200

    if state == 'completed':
        # Get the library name
        first_file_object = upload_batch_object.file_set.first()
        lib_name = first_file_object.file_path.split('/')[0]

        lib_objects = Library.objects.filter(
            basic_file=basic_file_object,
            name=lib_name
        )
        # If the library existed, clear the old record.
        if len(lib_objects) > 0:
            library_object = lib_objects.first()
            library_object.libraryfunction_set.all().delete()
            for f in library_object.file_set.all():
                f.delete()
        else:
            library_object = Library.objects.create(
                name=lib_name,
                dir_path=f'{lib_name}/',
                basic_file=basic_file_object
            )

        file_objects = upload_batch_object.file_set.all()
        # Parse the files in uploaded library
        for file in file_objects:
            # File's path startwith `<lib_name>/<lib_name>/`
            if file.file_path.startswith(f'{lib_name}/{lib_name}/'):
                # Change the file's path from `<lib_name>/<lib_name>/...` to
                # `<lib_name>/...`
                file.file_path = file.file_path.split('/', 1)[1]
                file.library = library_object
                file.save()
            # File's path startwith `<lib_name>/<example_dir>/`
            elif file.file_path.startswith(
                    f'{lib_name}/{basic_file_object.lib_example_dir}'):
                # Parse the example files
                with file.open('r') as f:
                    example_file_name = file.file_path.split('/')[-1].split('.')[0]
                    # Parse the example file
                    ep = ExampleParser(f)

                    # If the filename is LIBRARY_GVS_FILENAME
                    # Set global variable informations.
                    if example_file_name == settings.LIB_GVS_FILENAME:
                        global_var_setup = ep[settings.LIB_GVS_SECTION_NAME]
                        gvs_readonly_lines = json.loads(
                            ep[settings.LIB_GVSRO_SECTION_NAME]
                        )
                        if not global_var_setup:
                            global_var_setup = ""
                        if not gvs_readonly_lines:
                            gvs_readonly_lines = []
                        library_object.global_var_setup = global_var_setup
                        library_object.gvs_readonly_lines = gvs_readonly_lines
                        library_object.save()
                        continue

                    ep_sections = ep.all_valid_sections()
                    if ep_sections:
                        LibraryFunction.objects.create(
                            name=example_file_name,
                            **ep_sections,
                            library=library_object
                        )
            # Delete invalid files
            else:
                file.delete()

        upload_batch_object.delete()
        return '', 200
    return 'Wrong state', 400
