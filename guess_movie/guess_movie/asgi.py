"""
ASGI config for guess_movie project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/asgi/
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guess_movie.settings')
django.setup()
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
import quizz.routing
import lyrizz.routing


# os.environ.setdefault('DJANGO_ALLOW_ASYNC_UNSAFE', 'true')
#
# application = get_asgi_application()

lyrizz_patterns = lyrizz.routing.websocket_urlpatterns
quizz_patterns = quizz.routing.websocket_urlpatterns
patterns = quizz_patterns + lyrizz_patterns
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            patterns # TODO: how to add lyrizz and quizz ?
        )
    ),
})