from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from api.models import SaFunction
from file_handle.models import UploadBatch

timestrf_string = "%m/%d/%Y, %H:%M:%S"


def get_timeout_objects(model):
    """ This function returns all objects in `model` produced before
        `filter_time`.
    """
    # Set the `filter_time` to one day.
    filter_time = timezone.now() - timedelta(days=1)
    filtered_objects = model.objects.filter(
        updated_at__lte=filter_time
    )
    return filtered_objects


def upload_batch_cleanup():
    """ This function clean all timeout UploadBatch and the file under it
    """
    upload_batch_objects = get_timeout_objects(UploadBatch)
    cleaned_list = []
    for batch in upload_batch_objects:
        cleaned_list.append(
            "UploadBatch(%d) @ [%s]" %
            (batch.id, batch.updated_at.strftime(timestrf_string))
        )
        for file in batch.file_set.all():
            file.delete()
        batch.delete()
    return cleaned_list


def sa_function_cleanup():
    """ This function clean all timeout SaFunction which didn't used by any
        Device or DeviceLibrary.
    """
    function_objects = get_timeout_objects(SaFunction)
    cleaned_list = []
    for func in function_objects:
        if func.used_count() == 0:
            cleaned_list.append(
                '%s @ [%s]' %
                (str(func), func.updated_at.strftime(timestrf_string))
            )
            func.delete()
    return cleaned_list


def cleanup_routine():
    """ This function is the entry of scheduler routine.
        All the `print` content will be write in `datas/log/scheduler.log`
    """
    t = timezone.localtime()
    sa_cleanup_result = sa_function_cleanup()
    upload_batch_cleanup_result = upload_batch_cleanup()
    log_string = '[%s]\nClean SA function: %s\nClean Upload Batch: %s\n' % (
        t.strftime(timestrf_string),
        str(sa_cleanup_result),
        str(upload_batch_cleanup_result)
    )
    c = open(f'{settings.LOG_DIR}/scheduler.log', 'a')
    c.write(log_string)
    c.close()
