import pathlib
import shutil

from django.conf import settings

from .models import (
    File,
    UploadBatch
)


def create_upload_batch(upload_files: list):
    """
    Crete new upload batch, and generate the files uuid for upload.
    :param upload_files: list of file path and name
    :return: {
        'upload_info': {
            '<file_path_and_name>': <uuid>,
            'RPi_library/examples/foo.py': 'abc123...',
            ...
        },
        'file_upload_id': <id>
    }
    """
    upload_batch_object = UploadBatch.objects.create()
    upload_info_dict = {}

    for file_path in upload_files:
        uuid = File.uuid_generate()
        extension = pathlib.Path(file_path).suffix
        real_path = f'{settings.FILE_UPLOAD_DIR}{uuid}{extension}'

        # Create record for upload file
        new_file_object = File.objects.create(
            file_path=file_path,
            real_path=real_path,
            uuid=uuid,
            upload_batch=upload_batch_object
        )
        upload_info_dict[file_path] = new_file_object.uuid
    upload_batch_object.save()

    return {
        'upload_info': upload_info_dict,
        'file_upload_id': upload_batch_object.id
    }


def save_file(uuid: str, file):
    try:
        # Get the file item from File table.
        file_object = File.objects.get(uuid=uuid)
    except:
        return 'File not found.', 404

    if file_object.is_upload:
        # File has been uploaded
        return 'File already uploaded.', 400

    # Save the file in server
    # TOFIX: filetype is string, used for copying files only as a workaround
    if type(file) is str:
        # File from cli by file path, use copy file
        shutil.copy(file, file_object.real_path)
    else:
        # File from django request, save the chunks
        with file_object.open('wb') as fp:
            # Read uploaded file's chunk and write it to the file open from server.
            for chunk in file.chunks():
                fp.write(chunk)

    # Set the `is_upload` flag of the file object.
    file_object.is_upload = True
    file_object.save()

    return '', 200
