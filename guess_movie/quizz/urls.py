from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


app_name = 'quizz'

urlpatterns = [
    path('room/results/<str:room_name>/<str:game_name>/', views.room_results, name='room_results'),
    path('room/results_image/<str:room_name>/<str:game_name>/', views.room_results_image, name='room_results_image'),
    path('room/play/<str:room_name>/<str:game_name>/', views.room_play, name='room_play'),
    path('room/play_image/<str:room_name>/<str:game_name>/', views.room_play_image, name='room_play_image'),
    path('room/<str:room_name>/', views.room, name='room'),
    path('room/', views.room_index, name='room_index'),
    path('editor/', views.editor, name='editor'),
    path('save_preset/', views.save_preset, name='save_preset'),
    # path('exploration/', views.exploration, name='exploration'),
    path('history/<str:game_name>/', views.history, name='history'),
    path('history_image/<str:game_name>/', views.history_image, name='history_image'),
    path('history/', views.history_index, name='history_index'),
    path('game_image/', views.game_image, name='game_image'),
    path('guess_image/', views.guess_image, name='guess_image'),
    path('reveal_image/', views.reveal_image, name='reveal_image'),
    path('create_room/', views.create_room, name='create_room'),
    path('create_game/', views.create_game, name='create_game'),
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('change_user_name/', views.change_user_name, name='change_user_name'),
    # path('get_movie_info/', views.get_movie_info, name='get_movie_info'),
    path('save_info_game/', views.save_info_game, name='save_info_game'),
    path('update_session_interruption/', views.update_session_interruption, name='update_session_interruption'),
    path('guess_room/', views.guess_room, name='guess_room'),
    path('update_selection/', views.update_selection, name='update_selection'),
    # path('selection/', views.selection, name='selection'),
    path('game/', views.game, name='game'),
    # path('guess/', views.guess, name='guess'),
    # path('reset_score/', views.reset_score, name='reset_score'),
    # path('profile/', views.profile, name='profile'),
    # path('<int:pk>/results/', views.ResultsView.as_view(), name='results'),
    # path('<int:question_id>/vote/', views.vote, name='vote'),
]
# ]
# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)