#!/usr/bin/env python

import sys
import spotipy
import spotipy.util as util
import random
import tkinter as tk
import json
from subprocess import Popen, call
import time
import numpy as np
import matplotlib.pyplot as plt
from operator import itemgetter

# Helper functions
def get_sorted_indices():
    return sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True
    )

## Open Spotify so the songs can play
# if len(sys.argv) == 1:
#     spotify = Popen("/usr/bin/spotify")

# Set the environment variables through my alias
# call(['/bin/bash', '-i', '-c', 'spotify_song_poll_env'])

# My personal Spotify info
scope = 'user-library-read streaming playlist-modify-public'
username = '1295552060'
playlist = '0UGlsRHlwdrsnYcgty9dCR'
results_playlist = '1cgMS7J9sCxKQ5vcvms4RM'

# Authorization to use the Spotify SDK
token = util.prompt_for_user_token(username, scope)
if not token:
    sys.exit()
sp = spotipy.Spotify(auth=token)

# Set up the Poll mode and start position
poll_mode = "least_viewed"   # default
sort_position = 0            # used for sort mode
STATE_FILE = "poll_state.json"

#
#****************************************************
# Data retreival - list of tracks
#****************************************************
#

# Initialize lists of information to be used
tracks = []
artists = []
track_ids = []
votes = [] # how many times thesong has been chosen
at_bat = [] # how many times the song has been available to vote on
scores = []
ratings = []

# Extract the track info from the playlist. Each item is in a very specific position of ...
# the data structure returned by the sp.user_playlist_tracks() function
# Only run this if there is not already a results file available
try:
    # If there is already a score file, grab the data
    read_file = open('poll_results.json', 'r')
    data = json.load(read_file)
    for row in data:
        tracks.append(row[0])
        artists.append(row[1])
        track_ids.append(row[2])
        votes.append(row[3])
        at_bat.append(row[4])
        scores.append(row[5])
        ratings.append(row[6])
    print('file found')
except IOError:
    print('file not found')

# Load the start position
try:
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
        sort_position = state.get("sort_position", 0)
except:
    sort_position = 0

# Select the poll mode
# least voted vs random
# OR
# sorting method
mode_window = tk.Tk()
mode_window.title("Select Poll Mode")

selected_mode = tk.StringVar(value="least_viewed")

tk.Label(
    mode_window,
    text="Choose voting mode:"
).pack(padx=20, pady=10)

tk.Radiobutton(
    mode_window,
    text="Least Viewed vs Random",
    variable=selected_mode,
    value="least_viewed"
).pack(anchor="w")

tk.Radiobutton(
    mode_window,
    text="Sequential Score Sort",
    variable=selected_mode,
    value="score_sort"
).pack(anchor="w")

def launch_poll():
    global poll_mode
    poll_mode = selected_mode.get()
    mode_window.destroy()

tk.Button(
    mode_window,
    text="Start",
    command=launch_poll
).pack(pady=10)

mode_window.mainloop()


# Take the tracks from the playlist, check them agains the results file
i = 0
track_check = []
artist_check = []
id_check = []
while(True):
    results = sp.user_playlist_tracks(username, playlist, offset=i, limit=100)
    results = results['items']

    for track in results:
        track = track['track']
        track_check.append(track['name'])
        artist_check.append(track['artists'][0]['name'])
        id_check.append(track['uri'])

    # The function can only return 100 tracks at a time.
    i+=100
    if len(results) < 100:
        break

# Find the tracks in the playlist, then check if they are located in the results
for i,id in enumerate(id_check):
    # if track.upper() in (name.upper() for name in tracks):
    #     pass
    if id in track_ids or track_check[i] in tracks:
        pass
    else:
        tracks.append(track_check[i])
        artists.append(artist_check[i])
        track_ids.append(id)
        votes.append(0)
        at_bat.append(0)
        scores.append(0)
        ratings.append(1500)
        print(track_check[i] + ' added')

# Remove songs that no longer exist in the Spotify playlist

playlist_ids = set(id_check)

keep_indices = [
    i for i, song_id in enumerate(track_ids)
    if song_id in playlist_ids
]

removed_count = len(track_ids) - len(keep_indices)

tracks    = [tracks[i]    for i in keep_indices]
artists   = [artists[i]   for i in keep_indices]
track_ids = [track_ids[i] for i in keep_indices]
votes     = [votes[i]     for i in keep_indices]
at_bat    = [at_bat[i]    for i in keep_indices]
scores    = [scores[i]    for i in keep_indices]
ratings   = [ratings[i]   for i in keep_indices]

print(f"{removed_count} songs removed from poll_results.json")

# Clear unused variables
del i, track_check, artist_check, id_check




#
#****************************************************
# Voting loop and GUI
#****************************************************
#

# Run the voting on default script
if len(sys.argv) == 1:

    ## Set up the ui
    root = tk.Tk()
    root.title('Song Poll')
    label = tk.Label(root, text="Choose one: ", padx=100)
    label.grid(row=0, column=1)

    ## Start the voting loop
    def voting_loop(button1, button2):
        global sort_position
        # Pick one song from the list of least viewed songs, the other from the whole list
        if poll_mode == "least_viewed":

            while True:
                minimum_votes = min(at_bat)

                less_viewed_songs = [
                    i for i, x in enumerate(at_bat)
                    if x == minimum_votes
                ]

                if len(less_viewed_songs) > 1:
                    ind1 = random.choice(less_viewed_songs)
                    ind2 = random.choice(range(len(tracks)))
                else:
                    ind1 = less_viewed_songs[0]
                    ind2 = random.choice(range(len(tracks)))

                if ind1 != ind2:
                    break
        # Pick one song from the ranked list and the next one sequentially
        else:

            ranked = get_sorted_indices()

            if len(ranked) < 2:
                return

            if sort_position >= len(ranked) - 1:
                sort_position = 0

            ind1 = ranked[sort_position]
            ind2 = ranked[sort_position + 1]

            print(
                f"Sequential comparison {sort_position}: "
                f"{tracks[ind1]} vs {tracks[ind2]}"
            )

        # Collect the info about the tracks
        song1 = tracks[ind1]
        song2 = tracks[ind2]
        artist1 = artists[ind1]
        artist2 = artists[ind2]
        entry1 = song1 + ' --- ' + artist1
        entry2 = song2 + ' --- ' + artist2
        id1 = track_ids[ind1]
        id2 = track_ids[ind2]

        print(song1, ratings[ind1])
        print(song2, ratings[ind2])
        # Change the button text and pass the track info into the button_command
        button1.config(text=entry1, command=lambda: button_command(ind1,ind2))
        button2.config(text=entry2, command=lambda: button_command(ind2,ind1))
        play_button1.config(command=lambda: play_command(id1))
        play_button2.config(command=lambda: play_command(id2))

    # When the button is pressed, the score for the winning song increments
    def button_command(indWin,indLose):
        global votes
        # Update the at_bat list to show these two songs have been selected
        at_bat[indWin] += 1
        at_bat[indLose] += 1
        # Increment the winning song
        votes[indWin] += 1
        update_elo(indWin,indLose)
        if poll_mode == "score_sort":
            global sort_position
            sort_position += 1

            ranked = get_sorted_indices()

            if sort_position >= len(ranked) - 1:
                sort_position = 0
        voting_loop(button1, button2)

    def update_elo(winner, loser, k=32):
        global ratings
        rw = ratings[winner]
        rl = ratings[loser]
        expected_winner = 1.0 / (1.0 + 10 ** ((rl - rw) / 400.0))
        expected_loser = 1.0 / (1.0 + 10 ** ((rw - rl) / 400.0))
        ratings[winner] = rw + k * (1 - expected_winner)
        ratings[loser] = rl + k * (0 - expected_loser)
        print(tracks[winner], ratings[winner])
        print(tracks[loser], ratings[loser])


    # Define the function to play the songs using the play buttons
    def play_command(song_id):
        new_id_list = [song_id]
        sp.start_playback(uris=new_id_list)

    def skip_command():
        global sort_position
        if poll_mode == "score_sort":
            ranked = get_sorted_indices()
            sort_position += 1
            if sort_position >= len(ranked) - 1:
                sort_position = 0
        voting_loop(button1,button2)

    def pause_command():
        sp.pause_playback()

    # Define the function to quit the voting and save the results
    def quit_command():
        global tracks, artists, track_ids, votes, at_bat
        poll = []
        for i in range(len(tracks)):
            # if at_bat[i] == 0 or votes[i] == 0:
            #     score = 1400
            # elif at_bat[i] > 0:
            #     # score = float(votes[i])*(1.0 + 10/float(at_bat[i]))
            score = ratings[i]
            # score = ratings[i] + float(votes[i])*(1.0 + 10/float(at_bat[i]))
            scores[i] = score
            poll.append([tracks[i], artists[i], track_ids[i], votes[i], at_bat[i], score, ratings[i]])

        # Write the sort position
        with open(STATE_FILE, "w") as f:
            json.dump(
                {
                    "sort_position": sort_position
                },
                f,
                indent=4
            )

        # Write the poll results to a JSON file
        with open('poll_results.json', 'w') as write_file:
                json.dump(poll, write_file, indent=4)
        # spotify.kill()
        root.quit()

    # Initialize the two song buttons
    button1 = tk.Button(root, width=50, command=button_command)
    button1.grid(row=1, column=0)
    button2 = tk.Button(root, width=50, command=button_command)
    button2.grid(row=2, column=0)

    # Initialize the two play buttons
    play_button1 = tk.Button(root, width=5, text='>')
    play_button1.grid(row=1, column=1)
    play_button2 = tk.Button(root, width=5, text='>')
    play_button2.grid(row=2, column=1)

    # Begin the voting
    voting_loop(button1, button2)

    # Create a button for quitting the program
    tk.Button(root, text='Skip', command=skip_command).grid(row=3, column=0)
    tk.Button(root, text='||', command=pause_command).grid(row=3, column=1)
    tk.Button(root, text='Quit', command=quit_command).grid(row=4, column=1)
    tk.mainloop()

    

#
#****************************************************
# Results
#****************************************************
#
# Save the results to a playlist
score_ind = sorted(range(len(scores)), key = lambda k: scores[k])
results = list(reversed(score_ind))

# Plot some of the results
# Bar Graph of top 25 songs
song_results = []
score_results = []
y_pos = np.arange(25)

for i,ind in enumerate(results):
    # save results to the playlist
    if i == 0:
        sp.user_playlist_replace_tracks(username,results_playlist,[track_ids[ind]])
    else:
        sp.user_playlist_add_tracks(username,results_playlist,[track_ids[ind]]) 
    if i <= 24:
        # Save results to the plotting lists
        song_results.append(tracks[ind])
        score_results.append(round(scores[ind],1))
    


fig = plt.figure(figsize=(20,10))
ax = fig.add_subplot(1,1,1)
ax.grid()
plt.bar(y_pos, score_results, align='center', alpha=0.5)
for i,v in enumerate(score_results):
    ax.text(i-.4, v+.1 , str(v), color='blue', fontweight='bold')
plt.xticks(y_pos,song_results, rotation='vertical')
plt.ylabel('Score')
plt.title('Top 25 Songs')
fig.tight_layout()
plt.show()


# Top10 artists
# Create a dict of all the artists and their scores
Nartists = list(set(artists))
artist_scores = {}
for i in range(len(Nartists)):
    artist_scores[Nartists[i]] = 0

# Find the score of each song by an artist
for artist, score in artist_scores.items():
    Nsongs = 0
    indices = [i for i, x in enumerate(artists) if x == artist]
    for i,ind in enumerate(indices):
        Nsongs = Nsongs + 1
        score = score + scores[ind]
    if Nsongs == 0: # Catch the exception where the score is 0
        Nsongs = 1
    score = Nsongs + score / Nsongs   
    artist_scores[artist] = round(score,1)
    print(artist,artist_scores[artist])

sorted_artists = sorted(artist_scores.items(), key=itemgetter(1))
sorted_artists = reversed(sorted_artists)
top_25_artist_scores = []
top_25_artists = []
for i,pair in enumerate(sorted_artists):
    top_25_artists.append(pair[0])
    top_25_artist_scores.append(pair[1])
    if i >= 24:
        break

fig = plt.figure(figsize=(20,10))
ax = fig.add_subplot(1,1,1)
ax.grid()
plt.bar(y_pos, top_25_artist_scores, align='center', alpha=0.5)
for i,v in enumerate(top_25_artist_scores):
    ax.text(i-.4, v+.1 , str(v), color='blue', fontweight='bold')
plt.xticks(y_pos,top_25_artists, rotation='vertical')
plt.ylabel('Score')
plt.title('Top 25 Artists')
fig.tight_layout()
plt.show()




