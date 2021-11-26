import datetime
import json
import os
import spotipy
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from scipy.interpolate import pchip
from tzlocal import get_localzone

class StreamingHistory():

    def __init__(self, path="."):

        self.current_year = datetime.date.today().year

        files = {file for file in os.listdir(path) if file[:16] + file[-5:] == "StreamingHistory.json"}

        if not files:
            print("Error: No streaming history found")
            return

        streaming_history = ()

        for file in files:
            streaming_file = open(os.path.join(path, file), "r", encoding="utf-8")
            streaming_json = streaming_file.read()
            streaming_file.close()
            streaming_history += tuple(json.loads(streaming_json))

        for song in streaming_history:
            time_i = datetime.datetime.strptime(song["endTime"] + " +00:00", "%Y-%m-%d %H:%M %z").astimezone(
                get_localzone())
            time = datetime.datetime(time_i.year, time_i.month, time_i.day, time_i.hour, time_i.minute)

            song["endTime"] = time

        streaming_history = tuple(song for song in streaming_history if
                                  song["endTime"].year == current_year and song["msPlayed"] > 30000)

        return streaming_history

def retrieve_streaming_history(path="."):
    current_year = datetime.date.today().year
    path = path if path[-1] == "/" else path + "/"

    files = {file for file in os.listdir(path) if file[:16] + file[-5:] == "StreamingHistory.json"}

    if not files:
        print("Error: No streaming history found")
        return

    streaming_history = ()

    for file in files:
        streaming_file = open(path + file, "r", encoding="utf-8")
        streaming_json = streaming_file.read()
        streaming_file.close()
        streaming_history += tuple(json.loads(streaming_json))

    for song in streaming_history:
        time_i = datetime.datetime.strptime(song["endTime"] + " +00:00", "%Y-%m-%d %H:%M %z").astimezone(
            get_localzone())
        time = datetime.datetime(time_i.year, time_i.month, time_i.day, time_i.hour, time_i.minute)

        song["endTime"] = time

    streaming_history = tuple(song for song in streaming_history if
                              song["endTime"].year == current_year and song["msPlayed"] > 30000)

    return streaming_history


def most_listened_song(listening_info):
    most_listens = max(
        {listening_info[artist][1][song] for artist in listening_info for song in listening_info[artist][1]})

    top_song = {(artist, song, most_listens) for artist in listening_info for song in listening_info[artist][1] if
                listening_info[artist][1][song] == most_listens}

    return top_song


def listening_information(streaming_history):
    listening_info_by_artist = {}

    for song in streaming_history:

        artist, time, duration, track = song["artistName"], song["endTime"], song["msPlayed"], song["trackName"]

        if artist not in listening_info_by_artist:
            listening_info_by_artist[artist] = [0, {}]

        if track not in listening_info_by_artist[artist][1]:
            listening_info_by_artist[artist][1][track] = 0

        listening_info_by_artist[artist][1][track] += 1
        listening_info_by_artist[artist][0] += duration

    return listening_info_by_artist


def get_token(username):
    client_id = "ecc3ee32f1254bd3b0f405cfc120f40f"
    client_secret = "843c797b4a534deeaa1d6274e6697dca"
    redirect_uri = "http://localhost:7777/callback"
    scope = "user-read-recently-played"

    token = spotipy.SpotifyOAuth(username=username, scope=scope, client_id=client_id,
                                 client_secret=client_secret, redirect_uri=redirect_uri).get_access_token()[
        'access_token']

    return token


def get_track(track_name, artist_name, token):
    sp = spotipy.Spotify(auth=token)

    while True:
        try:
            return sp.track(
                sp.search(q=f'artist:{artist_name} track:{track_name}', type='track')['tracks']['items'][0]['id'])
        except IndexError:
            return None
        except:
            continue


def get_artist(artist_name, token):
    sp = spotipy.Spotify(auth=token)

    while True:
        try:
            return sp.artist(sp.search(q=f'artist:{artist_name}', type='artist')['artists']['items'][0]['id'])
        except IndexError:
            return None
        except:
            continue


def get_features(track_id, token):
    sp = spotipy.Spotify(auth=token)

    while True:
        try:
            features = sp.audio_features([track_id])[0]
            return features
        except:
            continue


def top_artists(listening_info):
    return tuple((artist, listening_info[artist][0]) for artist in
                 sorted(listening_info, key=lambda a: listening_info[a][0], reverse=True)[:20])


def top_songs(listening_info):
    all_songs = {(artist, song): listening_info[artist][1][song] for artist in listening_info for song in
                 listening_info[artist][1]}

    return tuple((artist, all_songs[artist]) for artist in sorted(all_songs, key=all_songs.get, reverse=True)[:100])


def top_albums(listening_info, token):
    all_songs = {(artist, song) for artist in listening_info for song in listening_info[artist][1]}

    albums = {}

    c = 0

    for artist, song in all_songs:

        track = get_track(song, artist, token)

        if not track:
            c += 1
            print(c, "out of", len(all_songs), "completed", end="\r")
            continue

        album = track["album"]["name"]
        key = tuple(artist["name"] for artist in track["album"]["artists"]) + (album,)

        if key not in albums:
            albums[key] = 0

        albums[key] += listening_info[artist][1][song]

        c += 1
        print(c, "out of", len(all_songs), "completed", end="\r")

    print()
    return (
        len(albums),
        tuple((key[-1], key[:-1], albums[key]) for key in sorted(albums, key=albums.get, reverse=True)[:10]))


def top_genres(listening_info, token):
    all_artists = {artist: sum(tuple(listening_info[artist][1][song] for song in listening_info[artist][1])) for artist in
                   listening_info}

    genres = {}

    c = 0

    for artist in all_artists:

        try:
            a_genres = get_artist(artist, token)["genres"]
        except TypeError:
            c += 1
            print(c, "out of", len(all_artists), "completed", end="\r")
            continue

        for genre in a_genres:
            if genre not in genres:
                genres[genre] = 0

            genres[genre] += all_artists[artist]

        c += 1
        print(c, "out of", len(all_artists), "completed", end="\r")

    print()
    return len(genres), tuple(genre for genre in sorted(genres, key=genres.get, reverse=True)[:10])


def activity_by_time(streaming_history):
    times = {hour: 0 for hour in range(24)}

    for song in streaming_history:
        times[song["endTime"].hour] += 1

    return times


def activity_by_date(streaming_history):
    dates = {month: [0, 0] for month in range(1, 13)}

    for song in streaming_history:
        dates[song["endTime"].month][0] += 1
        dates[song["endTime"].month][1] += song["msPlayed"]

    return dates


def overall(path, username):
    str_his = retrieve_streaming_history(path)
    l_info = listening_information(str_his)

    wrapped_str = "Here is your Spotify listening information for the year (up to " + str_his[-1]["endTime"].strftime(
        "%b %-d") + ")\n\n"

    listening_min = round(sum([s["msPlayed"] for s in str_his]) / (1000 * 60))
    listening_hr = round(listening_min / 60)

    wrapped_str += f"• You've listened to {listening_min:,} minutes of music ({listening_hr:,} hours)\n\n"
    wrapped_str += f"• You listened to {len(l_info):,} different artists this year! Here are some of your favorites\n\n"

    tar = top_artists(l_info)

    for i, (artist, time) in enumerate(tar):
        wrapped_str += f"\t{i + 1}.\t{artist}, {round(time / (1000 * 60 * 60)):,} hours\n"

    wrapped_str += f"\n• You jammed to {len([(artist, song) for artist in l_info for song in l_info[artist][1]]):,} unique tracks this year. We've created a playlist of your favorites\n\n"

    ts = top_songs(l_info)

    for i, ((artist, song), plays) in enumerate(ts):
        wrapped_str += f"\t{i + 1}.\t{song} - {artist}, {plays:,} plays\n"

    tal = top_albums(l_info, get_token(username))

    wrapped_str += f"\n• Of the {tal[0]:,} different albums you've come across this year, here are your own top 10\n\n"

    for i, (album, artists, plays) in enumerate(tal[1]):
        wrapped_str += f"\t{i + 1}.\t{album} - {', '.join(artists)}, {plays:,} plays\n"

    tg = top_genres(l_info, get_token(username))

    wrapped_str += f"\n• Nice taste! You explored {tg[0]:,} genres this year. Here are the ones you loved the most\n\n"

    for i, genre in enumerate(tg[1]):
        wrapped_str += f"\t{i + 1}.\t{genre}\n"

    wrapped_file = open("../out/Wrapped Information.txt", "w", encoding="utf-8")
    wrapped_file.write(wrapped_str)
    wrapped_file.close()

    abt = activity_by_time(str_his)
    active_h = datetime.time(max(abt, key=abt.get), 0)

    x, y = [k for k in abt], [abt[k] for k in abt]
    pch = pchip(x, y)
    xn = np.linspace(0, 23, 369)
    lx = [datetime.time(int(i), 0).strftime("%-I%p") if i in x else i for i in xn]
    d = [0.04494726562500001, 0.030005859375, 0.03366796875, 0.033570312500000005, 0.03523046875000002,
         0.033814453125000005, 0.034595703125000016, 0.03269140625, 0.034302734375000005, 0.034595703125000016,
         0.047095703125, 0.04128515625000001]

    fig, ax = plt.subplots(figsize=(12.8, 12.8 / 1.95))
    ax.plot(lx, pch(xn), "w")
    ax.set_xticks(lx[::16])
    ax.set_xticklabels(lx[::16], fontsize=8, color="w", fontname="Circular Std Black")
    plt.grid(axis="x", color="w", linewidth=0.4)
    plt.title("Your Spotify Activity by the Hour\n", color="w", **{"fontname": "Circular Std Bold"})
    ax.get_yaxis().set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis='x', colors='w', width=0.4, pad=10)
    plt.text(0.502 + d[int(active_h.strftime("%-I")) - 1], 0.15, f"{active_h.strftime('%-I:%M')}",
             transform=fig.transFigure, color="#1E3264", **{"fontname": "Circular Std Black"}, fontsize=50, ha="right")
    plt.text(0.50 + d[int(active_h.strftime("%-I")) - 1], 0.15, f"{active_h.strftime('%p').lower()}",
             transform=fig.transFigure, color="#1E3264", **{"fontname": "Circular Std Bold"}, fontsize=30, ha="left")
    fig.subplots_adjust(right=0.875, left=0.125, bottom=0.395, top=0.86)
    plt.text(0.5, 0.1, f"Most active hour ({str(get_localzone()).replace('_', ' ')})", transform=fig.transFigure,
             color="#1E3264", **{"fontname": "Circular Std Book"}, fontsize=10, ha="center")

    plt.savefig("../out/Activity by Hour.png", transparent=True, dpi=400)
    plt.close()

    abd = activity_by_date(str_his)
    x, y = [k for k in abd], [abd[k][0] for k in abd]
    xn = np.linspace(1, 12, 364)
    pch = pchip(x, y)
    lx = [datetime.date(2000, int(i), 1).strftime("%b") if i in x else i for i in xn]

    active_m = datetime.date(2000, max(abd, key=abd.get), 1)

    fig, ax = plt.subplots(figsize=(12.8, 12.8 / 1.95))
    ax.plot(lx, pch(xn), "w")
    ax.set_xticks(lx[::33])
    ax.set_xticklabels(lx[::33], fontsize=10, color="w", fontname="Circular Std Black")
    plt.grid(axis="x", color="w", linewidth=0.4)
    plt.title(f"Your Spotify Activity for {datetime.date.today().year}\n", color="w",
              **{"fontname": "Circular Std Bold"})
    ax.get_yaxis().set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis='x', colors='w', width=0.4, pad=10)
    fig.subplots_adjust(right=0.875, left=0.125, bottom=0.395, top=0.86)
    trans = ax.get_xaxis_transform()
    ax.plot([182, 182], [-0.36, -0.78], "w", transform=trans, clip_on=False, linewidth=1)
    plt.text(0.3, 0.082, "Most active month", transform=fig.transFigure, color="#1E3264",
             **{"fontname": "Circular Std Book"}, fontsize=12, ha="center")
    plt.text(0.3, 0.15, f"{active_m.strftime('%B')}", transform=fig.transFigure, color="#1E3264",
             **{"fontname": "Circular Std Bold"}, fontsize=50, ha="center")
    plt.text(0.7, 0.082, f"hours of music streamed during {active_m.strftime('%B')}", transform=fig.transFigure,
             color="#1E3264", **{"fontname": "Circular Std Book"}, fontsize=12, ha="center")
    plt.text(0.7, 0.15, f"{round(abd[max(abd, key=abd.get)][1] / (1000 * 60 * 60)):,}", transform=fig.transFigure,
             color="#1E3264", **{"fontname": "Circular Std Bold"}, fontsize=50, ha="center")

    plt.savefig("out/Activity by Month.png", transparent=True, dpi=400)

    for image in ["out/Activity by Hour.png", "out/Activity by Month.png"]:
        bckg = Image.open("src/background/Wrapped Background.png")
        img = Image.open(image)
        bckg.paste(img, (0, 0), img)
        bckg.save(image, "PNG")
        img.close()
        bckg.close()
