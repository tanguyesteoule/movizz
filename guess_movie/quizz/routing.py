from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/room/play/m/(?P<room_name>\w+)/(?P<game_name>\w+)/(?P<user_id>\w+)/$', consumers.GameMasterConsumer.as_asgi()),
    re_path(r'ws/room/play/(?P<room_name>\w+)/(?P<game_name>\w+)/(?P<user_id>\w+)/$', consumers.UserConsumer.as_asgi()),
    re_path(r'ws/room/play_image/m/(?P<room_name>\w+)/(?P<game_name>\w+)/(?P<user_id>\w+)/$', consumers.GameMasterConsumerImage.as_asgi()),
    re_path(r'ws/room/play_image/(?P<room_name>\w+)/(?P<game_name>\w+)/(?P<user_id>\w+)/$', consumers.UserConsumerImage.as_asgi()),
    re_path(r'ws/room/m/(?P<room_name>\w+)/(?P<user_id>\w+)/$', consumers.GameMasterConsumerHome.as_asgi()),
    re_path(r'ws/room/(?P<room_name>\w+)/(?P<user_id>\w+)/$', consumers.UserConsumerHome.as_asgi()),
    re_path(r'ws/room/results/m/(?P<room_name>\w+)/(?P<user_id>\w+)/$', consumers.GameMasterConsumerResults.as_asgi()),
    re_path(r'ws/room/results/(?P<room_name>\w+)/(?P<user_id>\w+)/$', consumers.UserConsumerResults.as_asgi()),
]