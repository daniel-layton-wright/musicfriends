from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login', views.login_, name = 'login'),
    path('spotifylogin', views.spotifylogin),
    path('spotifycallback', views.spotifycallback),
    path('tracks', views.tracks),
    path('commontracks/<str:friend_username>', views.commontracks)
]