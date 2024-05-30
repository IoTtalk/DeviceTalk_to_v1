"""
WSGI config for _ project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '_.settings')

application = get_wsgi_application()


# ensure only one scheduler of periodic tasks
# this should be after get_wsgi_application()
import devicetalk.tasks  # noqa: E402

devicetalk.tasks.init_periodic_tasks()
