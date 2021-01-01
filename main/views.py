from django.shortcuts import render
from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.contrib.auth import authenticate, login
import django.contrib.auth
import urllib
import requests
import base64
import math

from .models import User
from friendship.models import Friend, FriendshipRequest


@login_required(login_url='/login')
def index(request):
    friends = Friend.objects.friends(request.user)
    context = {
        'me': request.user
    }
    friends_and_requests = _get_friends_and_requests(request.user)
    context.update(friends_and_requests)

    print(context['requests_from'])
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
    access_token = _refresh_token(username)
    return JsonResponse({"access_token": access_token})


def _refresh_token(username):
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

    spotify_response = requests.post(url, headers=headers, data=data)
    if spotify_response.status_code != 200:
        return HttpResponse('Error.', status=401)

    access_token = spotify_response.json()['access_token']
    user.spotify_access_token = access_token
    user.save()
    return access_token


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
            return HttpResponseBadRequest('Error.')

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


@login_required
def friend_request(request, username):
    lookup_url = 'https://api.spotify.com/v1/users/%s' % (username)
    if _spotify_get_request(request.user, lookup_url).status_code != 200:
        return HttpResponseNotFound('Spotify user does not exist.')

    other_user, _ = User.objects.get_or_create(username = username)
    try:
        Friend.objects.add_friend(request.user, other_user)
        return HttpResponse('Success.')
    except:
        return HttpResponseBadRequest('Error.')


@login_required
def spotify_user_lookup(request, username):
    url = 'https://api.spotify.com/v1/users/%s' % (username)
    response = _spotify_get_request(request.user, url)
    if response.status_code == 200:
        return HttpResponse('Found.')
    else:
        return HttpResponseNotFound('Not found.')


def _spotify_get_request(user, url):
    response = requests.get(url, headers = {'Authorization': 'Bearer ' + user.spotify_access_token})
    if response.status_code == 401:
        _refresh_token(user.username)
        user.refresh_from_db()
        response = requests.get(url, headers={'Authorization': 'Bearer ' + user.spotify_access_token})

    if response.status_code == 502:
        response = requests.get(url, headers = {'Authorization': 'Bearer ' + user.spotify_access_token})

    return response

@login_required
def get_friends_and_requests(request):
    friends_and_requests = _get_friends_and_requests(request.user)
    friends_and_requests['friends'] = [{'username': x.username} for x in friends_and_requests['friends']]
    friends_and_requests['requests_to'] = [{'from_user': x.from_user.username} for x in friends_and_requests['requests_to']]
    friends_and_requests['requests_from'] = [{'to_user': x.to_user.username} for x in friends_and_requests['requests_from']]
    return JsonResponse(friends_and_requests)

def _get_friends_and_requests(user):
    friends = Friend.objects.friends(user)
    requests_to = Friend.objects.unrejected_requests(user = user)
    requests_from = Friend.objects.sent_requests(user = user)

    return {
        'friends': friends,
        'requests_to': requests_to,
        'requests_from': requests_from
    }


@login_required
def accept_request(request, username):
    from_user = User.objects.get(pk = username)
    request = FriendshipRequest.objects.get(from_user = from_user, to_user = request.user)
    request.accept()
    return HttpResponse()


@login_required
def reject_request(request, username):
    from_user = User.objects.get(pk = username)
    request = FriendshipRequest.objects.get(from_user = from_user, to_user = request.user)
    request.delete()
    return HttpResponse()


@login_required
def get_tracks(request, username, page):
    other_user = User.objects.get(pk=username)
    if username != request.user.username and not Friend.objects.are_friends(request.user, other_user):
        return HttpResponseBadRequest('Not friends.')

    per_page = 50
    offset = (page - 1)*per_page
    url = 'https://api.spotify.com/v1/me/tracks?offset=%s&limit=%s' % (offset, per_page)
    response = _spotify_get_request(other_user, url)
    response_json = response.json()
    num_pages = math.ceil(response_json['total'] / per_page)
    return JsonResponse({'items': response_json['items'], 'pages': num_pages, 'total': response_json['total']})

def logout(request):
    django.contrib.auth.logout(request)
    return redirect('/')
