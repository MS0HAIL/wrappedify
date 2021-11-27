from src.setup import setup
import datetime
import os
import shutil
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from scipy.interpolate import pchip
from tzlocal import get_localzone
from src.analysis import SpotifyAPI, ListeningInformation, StreamingHistory, analyse_listening


def write_stats(sAPI: SpotifyAPI, li: ListeningInformation, sh: StreamingHistory) -> None:
    analyse_listening(sAPI, li, sh)

    wrapped_str = f"Here is your Spotify listening information for the year (up to " \
                  f"{sh.data[-1]['endTime'].strftime('%b %-d')})\n\n"
    wrapped_str += f"• You've listened to {sh.minutes_listened:,} minutes of music ({sh.hours_listened:,} hours)\n\n"
    wrapped_str += f"• You listened to {len(li.data):,} different artists this year! Here are some of your favorites\n\n"

    for i, (artist, time) in enumerate(li.top_artists):
        wrapped_str += f"\t{i + 1}.\t{artist}, {round(time / (1000 * 60 * 60)):,} hours\n"

    wrapped_str += f"\n• You jammed to {len([(artist, song) for artist in li.data for song in li.data[artist][1]]):,} " \
                   f"unique tracks this year. We've created a playlist of your favorites\n\n"

    for i, ((artist, song), plays) in enumerate(li.top_songs):
        wrapped_str += f"\t{i + 1}.\t{song} - {artist}, {plays:,} plays\n"

    wrapped_str += f"\n• Of the {li.albums:,} different albums you've come across this year, " \
                   f"here are your own top 10\n\n"

    for i, (album, artists, plays) in enumerate(li.top_albums):
        wrapped_str += f"\t{i + 1}.\t{album} - {', '.join(artists)}, {plays:,} plays\n"

    wrapped_str += f"\n• Nice taste! You explored {li.genres:,} genres this year. " \
                   f"Here are the ones you loved the most\n\n"

    for i, genre in enumerate(li.top_genres):
        wrapped_str += f"\t{i + 1}.\t{genre}\n"

    wrapped_file = open("wrappedifyOut/Wrapped Information.txt", "w", encoding="utf-8")
    wrapped_file.write(wrapped_str)
    wrapped_file.close()


def write_graphics(sh: StreamingHistory) -> None:
    abt = sh.activity_by_time()
    active_hour = datetime.time(max(abt, key=abt.get), 0)

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
    plt.text(0.502 + d[int(active_hour.strftime("%-I")) - 1], 0.15, f"{active_hour.strftime('%-I:%M')}",
             transform=fig.transFigure, color="#1E3264", **{"fontname": "Circular Std Black"}, fontsize=50, ha="right")
    plt.text(0.50 + d[int(active_hour.strftime("%-I")) - 1], 0.15, f"{active_hour.strftime('%p').lower()}",
             transform=fig.transFigure, color="#1E3264", **{"fontname": "Circular Std Bold"}, fontsize=30, ha="left")
    fig.subplots_adjust(right=0.875, left=0.125, bottom=0.395, top=0.86)
    plt.text(0.5, 0.1, f"Most active hour ({str(get_localzone()).replace('_', ' ')})", transform=fig.transFigure,
             color="#1E3264", **{"fontname": "Circular Std Book"}, fontsize=10, ha="center")

    plt.savefig("wrappedifyOut/Activity by Hour.png", transparent=True, dpi=400)
    plt.close()

    abd = sh.activity_by_date()
    x, y = [k for k in abd], [abd[k][0] for k in abd]
    xn = np.linspace(1, 12, 364)
    pch = pchip(x, y)
    lx = [datetime.date(2000, int(i), 1).strftime("%b") if i in x else i for i in xn]

    active_month = datetime.date(2000, max(abd, key=abd.get), 1)

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
    plt.text(0.3, 0.15, f"{active_month.strftime('%B')}", transform=fig.transFigure, color="#1E3264",
             **{"fontname": "Circular Std Bold"}, fontsize=50, ha="center")
    plt.text(0.7, 0.082, f"hours of music streamed during {active_month.strftime('%B')}", transform=fig.transFigure,
             color="#1E3264", **{"fontname": "Circular Std Book"}, fontsize=12, ha="center")
    plt.text(0.7, 0.15, f"{round(abd[max(abd, key=abd.get)][1] / (1000 * 60 * 60)):,}", transform=fig.transFigure,
             color="#1E3264", **{"fontname": "Circular Std Bold"}, fontsize=50, ha="center")

    plt.savefig("wrappedifyOut/Activity by Month.png", transparent=True, dpi=400)

    for image in ["wrappedifyOut/Activity by Hour.png", "wrappedifyOut/Activity by Month.png"]:
        bckg = Image.open("assets/background/Wrapped Background.png")
        img = Image.open(image)
        bckg.paste(img, (0, 0), img)
        bckg.save(image, "PNG")
        img.close()
        bckg.close()


def wrapped() -> None:
    setup()

    path = input("Enter the path to the directory containing your Spotify information: ")
    username = input("Please enter your Spotify username: ")

    try:
        sh = StreamingHistory(path)
    except FileNotFoundError:
        print("Sorry, the folder you specified does not contain any listening information.")
        return

    li = ListeningInformation(sh)
    sAPI = SpotifyAPI(username)

    if not os.path.exists("wrappedifyOut"):
        os.mkdir("wrappedifyOut")
        write_stats(sAPI, li, sh)
        write_graphics(sh)

        print("Analysis complete, view your data in the folder wrappedifyOut.")
    else:
        option = input("WARNING: It seems wrappedify already ran. Would you like to overwrite previous results? "
                       "(y/Y/n/N): ")

        match option:
            case ("y" | "Y"):
                shutil.rmtree("wrappedifyOut")
                os.mkdir("wrappedifyOut")

                write_stats(sAPI, li, sh)
                write_graphics(sh)

                print("Analysis complete, view your data in the folder wrappedifyOut.")

            case _:
                print("Terminating.")
