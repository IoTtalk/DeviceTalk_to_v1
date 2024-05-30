import configparser
import traceback

from django.conf import settings

from api.models import (
    BasicFile,
    Language
)
from file_handle.models import UploadBatch


def update_basicfile(file_upload_id, state, language, basicfile_name, is_create=True):
    upload_batch_objects = UploadBatch.objects.filter(id=int(file_upload_id))
    if upload_batch_objects.count() == 0:
        return 'Upload Batch ID not found', 404
    upload_batch_object = upload_batch_objects.first()

    # state == 'failed' means the front-end get at least one error response during
    # uploading file. In this case, just delete all the uploaded file and ignore
    # this upload process.
    if state == 'failed':
        remove_file_group(upload_batch_object)
        return '', 200

    # state == 'completed' means that the front end gets all successful uploading
    # file responses.
    if state == 'completed':
        # Check language is existed.
        if Language.objects.filter(name=language).count() == 0:
            remove_file_group(upload_batch_object)
            return 'Language not found.', 404

        exist_basicfile_objects = BasicFile.objects.filter(
            name=basicfile_name,
            language__name=language
        )
        if is_create:
            # PUT for create new basic_file. IF name is exist, raise an error.
            # TODO: Let the user enter the name again.
            if exist_basicfile_objects.count() > 0:
                remove_file_group(upload_batch_object)
                return 'BasicFile name already exist.', 400

            # Create a new basic file object.
            basic_file_object = BasicFile.objects.create(
                language=Language.objects.get(name=language),
                name=basicfile_name,
                dir_path='.'
            )
        else:
            if exist_basicfile_objects.count() == 0:
                remove_file_group(upload_batch_object)
                return 'BasicFile name not found.', 404

            # Get the exist basic file object
            basic_file_object = exist_basicfile_objects.first()

        # Check that all required files are provided
        err_msg, code = check_format(upload_batch_object)
        if err_msg:
            # Return error if basic file format is invalid.
            remove_file_group(upload_batch_object)
            basic_file_object.delete()
            return err_msg, code

        # All pass, move uploaded files to available basic files.
        move_file_to_basicfile(upload_batch_object, basic_file_object)
        return '', 200
    return 'Wrong state', 400


def remove_file_group(file_group_object):
    # delete file group, it may be upload_batch or basic file
    for file in file_group_object.file_set.all():
        file.delete()
    file_group_object.delete()


def move_file_to_basicfile(upload_batch_object, basic_file_object):
    # Delete all the old basic_file files
    for file in basic_file_object.file_set.all():
        file.delete()

    # Insert all the files to basic_file
    for file in upload_batch_object.file_set.all():
        file.basic_file = basic_file_object
        file.save()
    upload_batch_object.delete()


def check_format(basicfile_object):
    '''This function check the format of config file
    Agrs:
        basicfile_object (file_handle.models.File).
    Return:
        bool. valid format or not::
        str. the error reason::
        str. more infomation of the error::
    '''
    # Check the basic file have config file
    config_file_objects = basicfile_object.file_set.filter(
        file_path=settings.BASICFILE_CONF_FILENAME)
    if config_file_objects.count() == 0:
        return 'Config file not found.', 404

    # Read configuration from config file
    config_file_object = config_file_objects.first()
    config = configparser.ConfigParser()
    try:
        config.read(config_file_object.real_path)
    except:
        tb = traceback.format_exc()
        # Return the traceback message, if ini format is invalid.
        return f'Invalid ini file format.\n{tb}', 400

    # Check all the required sections, options in config file
    miss_config_option = '\n'.join(
        f"[{section}] {option}"
        for section, option in settings.BASICFILE_CONF_SESSIONS
        if not config.has_option(section, option)
    )
    if miss_config_option:
        return f'Missing option.\n{miss_config_option}', 400

    # Return True, if all the result are valid
    return None, 200
