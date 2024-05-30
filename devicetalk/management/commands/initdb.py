import os

from django.conf import settings
from django.core.management.base import BaseCommand

from api.models import (
    BasicFile,
    Language,
    Library
)
from api.utils import create_library
from file_handle.utils import (
    create_upload_batch,
    save_file
)
from my_admin.utils import update_basicfile


class Command(BaseCommand):
    help = 'Initialize the DB'

    def handle(self, *args, **kwargs):
        self.stdout.write("Start initializing the default database data.")

        self._init_language()
        self._init_basic_file()
        self._init_library_file()

        self.stdout.write("Initialization finished.")

    def _init_language(self, *args, **kwargs):
        # Create all the default Languages.
        self.stdout.write("Initializing Languages...")
        for language in settings.DEFAULT_LANGUAGE_LIST:
            language_object, is_created = Language.objects.update_or_create(
                name=language
            )

            if is_created:
                self.stdout.write(f"\tLanguage: {language} created.")
            else:
                self.stdout.write(f"\tLanguage: {language} already exists, ignore.")

    def _init_basic_file(self, *args, **kwargs):
        # Create all the default Basic Files.
        self.stdout.write("Initializing Basic Files...")

        basicfile_root = 'DeviceTalk-Basic-file'
        # Read files
        for language in os.listdir(basicfile_root):
            # language_dir sample: 'DeviceTalk-Basic-file/Python'
            language_dir = os.path.join(basicfile_root, language)
            if not os.path.isdir(language_dir):
                continue

            self.stdout.write(f"\t{language}:")
            # Check if the directory name is an existing language.
            if Language.objects.filter(name=language).count() == 0:
                self.stdout.write('\t\tNot found in DB, ignore.')
                continue

            for basicfile_name in os.listdir(language_dir):
                # Check if the directory name is an existing basic file.
                if BasicFile.objects.filter(
                    name=basicfile_name,
                    language__name=language
                ).count() > 0:
                    self.stdout.write(f"\t\t<{basicfile_name}> already exists, skip.")
                    continue

                self.stdout.write(f"\t\t<{basicfile_name}> start importing...")
                # 1. Get all files
                # basicfile_dir sample: 'DeviceTalk-Basic-file/Python/default'
                basicfile_dir = os.path.join(language_dir, basicfile_name)
                """
                files = {
                    <short_path>: {
                        'full_path': <full_path>,
                        'uuid': None
                    },
                    ...
                }
                :full_path: the relative path from app root for copy file
                :short_path: the required path for file_handler
                :uuid: store uuid from upload file batch step
                """
                files = {
                    os.path.join(dp, f).replace(f'{basicfile_dir}/', ''): {
                        'full_path': os.path.join(dp, f),
                        'uuid': None,
                    } for dp, dn, filenames in os.walk(basicfile_dir) for f in filenames
                }

                # 2. Create upload file batch
                """
                batch_info = {
                    'upload_info': {
                        <short_path>: <uuid>,
                        ...
                    },
                    'file_upload_id': <upload_batch_object.id>
                }
                """
                batch_info = create_upload_batch(files.keys())
                for p, uuid in batch_info.get('upload_info', {}).items():
                    files[p].update({'uuid': uuid})

                # 3. Save files
                err_msg = '\n\t\t'.join(filter(None, [
                    save_file(f['uuid'], f['full_path'])[0]
                    for f in files.values()
                ]))

                # 4. Set upload file to basic file
                if err_msg:
                    self.stdout.write(f'\t\t{err_msg}')
                state = 'failed' if err_msg else 'completed'
                file_upload_id = batch_info.get('file_upload_id')
                err_msg, code = update_basicfile(
                    file_upload_id,
                    state,
                    language,
                    basicfile_name,
                    is_create=True
                )
                if err_msg:
                    self.stdout.write(f'\t\t{err_msg}')

    def _init_library_file(self, *args, **kwargs):
        # Create all the default Library Files.
        self.stdout.write("Initializing Library Files...")

        libraryfile_root = 'DeviceTalk-Library-file'
        # Read files
        for language in os.listdir(libraryfile_root):
            # language_dir sample: 'DeviceTalk-Library-file/Python'
            language_dir = os.path.join(libraryfile_root, language)
            if not os.path.isdir(language_dir):
                continue

            self.stdout.write(f"\t{language}:")
            # Check if the directory name is an existing language.
            if Language.objects.filter(name=language).count() == 0:
                self.stdout.write('\t\tNot found in DB, ignore.')
                continue

            # Check <language>/<basicfile>
            for basicfile_name in os.listdir(language_dir):
                # Check if the directory name is an existing basic file.
                basicfile_objects = BasicFile.objects.filter(
                    name=basicfile_name,
                    language__name=language
                )
                if basicfile_objects.count() == 0:
                    self.stdout.write(f"\t\tbasic <{basicfile_name}> not found, skip.")
                    continue
                basicfile_object = basicfile_objects.first()

                self.stdout.write(f"\t\t<{basicfile_name}> start importing...")
                # basicfile_dir sample: 'DeviceTalk-Basic-file/Python/default'
                basicfile_dir = os.path.join(language_dir, basicfile_name)

                # Check <language>/<basicfile>/<library>
                for library_name in os.listdir(basicfile_dir):
                    if Library.objects.filter(
                        basic_file=basicfile_object,
                        name=library_name
                    ).count() != 0:
                        self.stdout.write(
                            f"\t\t\t<{basicfile_name}.{library_name}> already exists, skip"
                        )
                        continue
                    else:
                        self.stdout.write(
                            f"\t\t\t<{basicfile_name}.{library_name}> start importing..."
                        )
                    # 1. Get all files
                    library_dir = os.path.join(basicfile_dir, library_name)
                    """
                    files = {
                        <short_path>: {
                            'full_path': <full_path>,
                            'uuid': None
                        },
                        ...
                    }
                    :full_path: the relative path from app root for copy file
                    :short_path: the required path for file_handler
                    :uuid: store uuid from upload file batch step
                    """
                    files = {
                        os.path.join(dp, f).replace(f'{basicfile_dir}/', ''): {
                            'full_path': os.path.join(dp, f),
                            'uuid': None,
                        } for dp, dn, filenames in os.walk(library_dir) for f in filenames
                    }

                    # 2. Create upload file batch
                    """
                    batch_info = {
                        'upload_info': {
                            <short_path>: <uuid>,
                            ...
                        },
                        'file_upload_id': <upload_batch_object.id>
                    }
                    """
                    batch_info = create_upload_batch(files.keys())
                    for p, uuid in batch_info.get('upload_info', {}).items():
                        files[p].update({'uuid': uuid})

                    # 3. Save files
                    err_msg = '\n\t\t'.join(filter(None, [
                        save_file(f['uuid'], f['full_path'])[0]
                        for f in files.values()
                    ]))

                    # 4. Set upload file to basic file
                    if err_msg:
                        self.stdout.write(f'\t\t{err_msg}')
                    state = 'failed' if err_msg else 'completed'
                    file_upload_id = batch_info.get('file_upload_id')
                    err_msg, code = create_library(
                        language,
                        basicfile_object.id,
                        file_upload_id,
                        state,
                    )
                    if err_msg:
                        self.stdout.write(f'\t\t{err_msg}')
