from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(
        r'^ws/game/team/(?P<team_id>\d+)/round/(?P<round_number>\d+)/$',
        consumers.GameSyncConsumer.as_asgi()
    ),
]
