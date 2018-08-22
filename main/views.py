from django.shortcuts import render
from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login
import django.contrib.auth
import urllib
import requests
import base64

from .models import User
from friendship.models import Friend


@login_required(login_url='/login')
def index(request):
    friends = Friend.objects.friends(request.user)
    print(friends)
    context = {
        'friends': friends,
        'me': request.user
    }
    return render(request, 'main/index.html', context)


def login_(request):
    context = {}
    return render(request, 'main/cover.html', context)


def spotifylogin(request):
    url = 'https://accounts.spotify.com/authorize'
    params = {
        'response_type': 'code',
        'client_id': settings.SPOTIFY_CLIENT_ID,
        'scope': settings.SPOTIFY_SCOPE,
        'redirect_uri': settings.SPOTIFY_REDIRECT_URI,
    }

    return redirect('%s?%s' % (url, urllib.parse.urlencode(params)))


def spotifycallback(request):
    url = 'https://accounts.spotify.com/api/token'
    authorization = base64.standard_b64encode(
        (settings.SPOTIFY_CLIENT_ID + ':' + settings.SPOTIFY_CLIENT_SECRET).encode())
    headers = {
        'Authorization': 'Basic ' + authorization.decode("utf-8")
    }
    data = {
        'code': request.GET['code'],
        'redirect_uri': settings.SPOTIFY_REDIRECT_URI,
        'grant_type': 'authorization_code'
    }

    spotify_response = requests.post(url, headers=headers, data=data)

    if spotify_response.status_code != 200:
        return HttpResponse('Error retrieving Spotify access token.')

    # Success
    json = spotify_response.json()
    access_token = json['access_token']
    refresh_token = json['refresh_token']

    # Get user id
    user_response = requests.get(
        'https://api.spotify.com/v1/me',
        headers={
            'Authorization': 'Bearer ' + access_token,
        }
    )
    if user_response.status_code != 200:
        return HttpResponse('Error retrieving user information')

    user_id = user_response.json()['id']
    user, _ = User.objects.get_or_create(username=user_id)
    user.spotify_access_token = access_token
    user.spotify_refresh_token = refresh_token
    user.save()

    login(request, user)
    return redirect('/')


def refresh_token(request, username):
    user = User.objects.get(pk=username)
    url = 'https://accounts.spotify.com/api/token'
    authorization = base64.standard_b64encode(
        (settings.SPOTIFY_CLIENT_ID + ':' + settings.SPOTIFY_CLIENT_SECRET).encode())
    headers = {
        'Authorization': 'Basic ' + authorization.decode("utf-8")
    }
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': user.spotify_refresh_token
    }

    spotify_response = requests.post(url, headers = headers, data = data)
    if spotify_response.status_code != 200:
        return HttpResponse('Error.', status = 401)

    access_token = spotify_response.json()['access_token']
    user.spotify_access_token = access_token
    user.save()

    return JsonResponse({"access_token": access_token})


def _get_tracks(access_token):
    request_url = 'https://api.spotify.com/v1/me/tracks'
    track_items = []

    while request_url:
        response = requests.get(
            request_url,
            headers={
                'Authorization': 'Bearer ' + access_token
            }
        )

        if response.status_code != 200:
            return HttpResponse('Error.')

        track_items.extend(response.json()['items'])
        request_url = response.json()['next']

    return track_items


def _find_common_track_items(user_track_items, friend_track_items):
    user_track_ids = set([t['track']['id'] for t in user_track_items])
    friend_track_ids = set([t['track']['id'] for t in friend_track_items])
    common_track_ids = user_track_ids.intersection(friend_track_ids)

    common_track_items = [t for t in user_track_items if t['track']['id'] in common_track_ids]
    return common_track_items


@login_required
def tracks(request):
    track_items = _get_tracks(request.user.spotify_access_token)

    return render(request, 'main/tracks.html', {'track_items': track_items})


@login_required
def commontracks(request, friend_username):
    print(request.user.spotify_access_token)
    user_track_items = _get_tracks(request.user.spotify_access_token)

    friend = User.objects.get(pk=friend_username)
    friend_track_items = _get_tracks(friend.spotify_access_token)

    common_track_items = _find_common_track_items(user_track_items, friend_track_items)
    return render(request, 'main/tracks.html', {'track_items': common_track_items})


def logout(request):
    django.contrib.auth.logout(request)
    return redirect('/')
