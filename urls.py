from django.urls import path

from . import views

app_name = 'destiny_emblems'
urlpatterns = [
    path('', views.index, name='index'),
    path('auth', views.auth, name='auth'),
    path('auth_callback', views.auth_callback, name='auth_callback'),
    path('logout', views.logout, name='logout'),
    path('profile', views.profile, name='profile'),
    path('player/<str:player_id>', views.search_player, name='search_player'),
    path('player/<str:platform>/<str:player_id>', views.player, name="player"),
]