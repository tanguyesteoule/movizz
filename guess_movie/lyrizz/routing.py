from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/lyrizz/room/play/m/(?P<room_name>\w+)/(?P<game_name>\w+)/(?P<user_id>\w+)/$', consumers.GameMasterConsumerLyrizz.as_asgi()),
    re_path(r'ws/lyrizz/room/play/(?P<room_name>\w+)/(?P<game_name>\w+)/(?P<user_id>\w+)/$', consumers.UserConsumerLyrizz.as_asgi()),
    # re_path(r'ws/room/play_image/m/(?P<room_name>\w+)/(?P<game_name>\w+)/(?P<user_id>\w+)/$', consumers.GameMasterConsumerImage.as_asgi()),
    # re_path(r'ws/room/play_image/(?P<room_name>\w+)/(?P<game_name>\w+)/(?P<user_id>\w+)/$', consumers.UserConsumerImage.as_asgi()),
    re_path(r'ws/lyrizz/room/m/(?P<room_name>\w+)/(?P<user_id>\w+)/$', consumers.GameMasterConsumerHomeLyrizz.as_asgi()),
    re_path(r'ws/lyrizz/room/(?P<room_name>\w+)/(?P<user_id>\w+)/$', consumers.UserConsumerHomeLyrizz.as_asgi()),
    re_path(r'ws/lyrizz/room/results/m/(?P<room_name>\w+)/(?P<user_id>\w+)/$', consumers.GameMasterConsumerResultsLyrizz.as_asgi()),
    re_path(r'ws/lyrizz/room/results/(?P<room_name>\w+)/(?P<user_id>\w+)/$', consumers.UserConsumerResultsLyrizz.as_asgi()),
]