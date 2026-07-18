import mido
from mido import MidiFile, MidiTrack
import numpy as np


def midinote2freq(note):
    A4 = 440       # Middle note
    A4_midi = 69   # Valor correspondiente a A4 en midi
    distance = note - A4_midi
    return A4 * 2 ** (distance / 12)


def ticks_to_seconds(ticks, ticks_per_beat, tempo):
    seconds_per_tick = tempo / ticks_per_beat / 1000000
    return ticks * seconds_per_tick


def parse_midi_file(file_path):
    midi = mido.MidiFile(file_path)

    ticks_per_beat = midi.ticks_per_beat
    tempo = 500000  # Valor predeterminado para el tempo en caso de que no se encuentre un evento de cambio de tempo
    duration = midi.length
    tracks = []
    tracks_names = []
    for i, track in enumerate(midi.tracks):
        current_track = []
        current_track_name = len(tracks)
        time = 0
        for message in track:
            time += message.time
            if message.type == 'set_tempo':
                tempo = message.tempo if message.time == 0 else 500000
            elif message.type == 'track_name':
                current_track_name = message.name
            elif message.type == 'note_on':
                if message.velocity == 0:
                    for note in reversed(current_track):
                        if note['note'] == message.note and note['duration'] == 0:
                            note['duration'] = ticks_to_seconds(
                                time, ticks_per_beat, tempo) - note['time']
                            break
                else:
                    current_track.append({
                        'note': message.note,
                        'velocity': message.velocity,
                        'time': ticks_to_seconds(time, ticks_per_beat, tempo),
                        'duration': 0
                    })
            elif message.type == 'note_off':
                for note in reversed(current_track):
                    if note['note'] == message.note and note['duration'] == 0:
                        note['duration'] = ticks_to_seconds(
                            time, ticks_per_beat, tempo) - note['time']
                        break
        if len(current_track) != 0:
            tracks.append(current_track)
            tracks_names.append(current_track_name)
            if current_track[-1]["time"]+current_track[-1]["duration"] > duration:
                duration = current_track[-1]["time"] + \
                    current_track[-1]["duration"]
    return tracks, tracks_names, duration


def print_parsed_data(tracks):
    for i, track in enumerate(tracks):
        print(f"Track {i + 1}:")
        for note in track:
            print(
                f"Note: {note['note']}, Velocity: {note['velocity']}, Time (s): {note['time']}, Duration (s): {note['duration']}")
        print()
