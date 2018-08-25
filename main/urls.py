from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login', views.login_, name = 'login'),
    path('spotifylogin', views.spotifylogin),
    path('spotifycallback', views.spotifycallback),
    path('tracks', views.tracks),
    path('commontracks/<str:friend_username>', views.commontracks),
    path('logout', views.logout),
    path('refresh_token/<str:username>', views.refresh_token),
    path('spotify_user_lookup/<str:username>', views.spotify_user_lookup),
    path('friend_request/<str:username>', views.friend_request),
    path('get_friends_and_requests', views.get_friends_and_requests),
    path('accept_request/<str:username>', views.accept_request),
    path('reject_request/<str:username>', views.reject_request),
    path('get_tracks/<str:username>/page/<int:page>', views.get_tracks)
]