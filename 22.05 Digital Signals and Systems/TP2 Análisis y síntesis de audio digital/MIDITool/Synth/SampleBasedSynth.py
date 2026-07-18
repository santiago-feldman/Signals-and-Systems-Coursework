import logging
import numpy as np
from scipy.io import wavfile
import librosa as lr
import mido

import matplotlib.pyplot as plt

inst_dict = {"Grito de Agus": ["./Utils/Instruments/gritoC4.wav", 60],
             "Fu": ["./Utils/Instruments/fuD3.wav", 50],
             "Piano": ["./Utils/Instruments/piano_samples/samples/", 60]}


def SampleSynth(track, inst, vol):
    # Set sample rate and duration
    fs = 44100
    duration = np.ceil(track[-1]["time"]+track[-1]["duration"])
    y = np.zeros(int(fs*duration))

    for curr in track:
        note = curr["note"]
        velocity = curr["velocity"]
        time = curr["time"]
        duration = curr["duration"]
        y_note = _samplesynth(note, velocity, duration, inst)
        start = int(time*fs)
        end = start + len(y_note)
        y[start:end] += y_note

    return y * vol


def _samplesynth(note, velocity, duration, inst):
    org_pitch = inst_dict[inst][1]
    wave_file = inst_dict[inst][0]
    if inst == "Piano":
        org_pitch = (note+6) - (note+6) % 12
        wave_file += f"C{org_pitch//12}vL.flac"

    data, sample_rate = lr.load(wave_file, sr=44100, mono=True)
    stretch = (len(data)/sample_rate)/duration

    stretch_data = lr.effects.time_stretch(
        data, rate=stretch)
    shift_data = lr.effects.pitch_shift(
        stretch_data, sr=sample_rate, n_steps=note-org_pitch, bins_per_octave=12)
    stretched_shifted_data = shift_data
    vel = velocity/127
    audio = np.array(stretched_shifted_data*vel /
                     stretched_shifted_data.max(), dtype=float)
    logging.debug(f"Sample max: {audio.max()}")
    return audio


if __name__ == "__main__":
    # Load the audio sample for the note
    data, sample_rate = lr.load(
        "./Utils/Instruments/gritoC4.wav", sr=44100, mono=True)
    y = _samplesynth(48, 127, 1, "Grito de Agus")
    fig = plt.figure()
    ax2 = fig.add_subplot(212)
    ax1 = fig.add_subplot(211)
    ax1.specgram(data.tolist(), 1024, 44100, noverlap=512)
    ax2.specgram(y.tolist(), 1024, 44100, noverlap=512)
    ax1.set_xlim(0, 0.5)
    ax2.set_xlim(0, 0.5)
    ax1.set_ylim(0, 5000)
    ax2.set_ylim(0, 2500)
    ax2.set_xlabel("Tiempo [s]")
    ax2.set_ylabel("Frecuencia [Hz]")
    ax1.set_ylabel("Frecuencia [Hz]")
    plt.show()
