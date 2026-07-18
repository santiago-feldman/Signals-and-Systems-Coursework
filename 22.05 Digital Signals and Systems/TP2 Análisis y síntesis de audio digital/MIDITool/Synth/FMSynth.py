import logging
import mido
import numpy as np
import math as math
import sounddevice as sd
import matplotlib.pyplot as plt
from scipy.io import wavfile
import soundfile as sf
from MIDI.Midi import parse_midi_file


def midinote2freq(note):
    A4 = 440       # Middle note
    A4_midi = 69   # Valor correspondiente a A4 en midi
    distance = note - A4_midi
    return A4 * 2 ** (distance / 12)


# Synth for clarinet
# @Value frecuency: Is in Hertz
# @value duration: In seconds (>0.6sec)
def synthClarinete(note, duration, vol):
    fi_m = fi_c = -np.pi/2  # Makes np.cos -> np.sin

    sample_rate = 44100  # Tasa de muestreo en Hz
    ArrLength = np.max([int(duration * sample_rate), int(0.1*sample_rate)])
    t = np.linspace(0, duration, ArrLength, endpoint=False)

    fo = midinote2freq(note)  # Fundamental Frecuency [fo = mcm(n,m)]
    fm = 2*fo       # Esta configuración es para lograr un sonido de clarinete
    fc = 3*fo
    Imax = int(fc/fm)  # Modilation Index
    Amax = vol        # Amplitud maxima

    A = np.full(ArrLength, Amax, dtype=float)
    I = np.full(ArrLength, Imax, dtype=float)
    for i in range(int(0.05 * sample_rate)):
        A[i] = (Amax * 400) * math.pow(i / sample_rate, 2)
        I[i] = (Imax * 400) * math.pow(i / sample_rate, 2)
        A[(ArrLength-1) - i] = (Amax * 20) * (i / sample_rate)

    x = np.empty(ArrLength, dtype=float)
    for k in range(ArrLength):
        x[k] = A[k] * np.cos(2 * np.pi * fc * t[k] + I[k]
                             * np.cos(2*np.pi * fm * t[k] + fi_m) + fi_c)
    x = x
    logging.debug(f"clarinete max: {x.max()}")
    return x


def FMSynth(track, inst, vol):
    # Set sample rate and duration
    fs = 44100
    duration = np.ceil(track[-1]["time"]+track[-1]["duration"])
    y = np.zeros(int(fs*duration))

    for curr in track:
        note = curr["note"]
        duration = curr["duration"]
        y_note = synthClarinete(note, duration, vol)

        time = curr["time"]
        start = int(time*fs)
        end = start + len(y_note)

        y[start:end] += y_note

    return y


if __name__ == "__main__":
    # Para plotear la señal de salida de una nota sola
    duration = 1
    vol = 1.0
    sample_rate = 44100  # Tasa de muestreo en Hz (ni idea porque)
    y = FMSynth(61, duration, vol)  # Db4 = 61 in Midi
    t = np.linspace(0, duration, int(duration * sample_rate), endpoint=False)
    plt.plot(t, y)
    plt.show()

    # Para generar un .wav (Amax >=50 sino no se escucha)
    parsed_tracks = parse_midi_file('Res\ClarinetSonata.mid')
    mid = mido.MidiFile('Res\ClarinetSonata.mid')
    y2 = synthClarinete(parsed_tracks[1][:50], vol=0.5)
    sf.write("FMSynth_Clarinet.wav", y2/y2.max(), sample_rate)

    # Para escuchar el sonido (Y <= 1!)
    # sd.play(y2, sample_rate)
    # sd.wait()

'''
Notas:
Tanto la amplitud como el indice de modulación se modifican en función del tiempo.
El clarinete tiene un indice de modulación de 3 mientras que el Fagot o Bassoon tiene un indice de 5
El clarinete va desde D3(147Hz) a Bb6(1865Hz)

Links importantes:
https://web.eecs.umich.edu/~fessler/course/100/misc/chowning-73-tso.pdf
https://www.cs.cmu.edu/~music/icm-online/readings/fm-synthesis/fm_synthesis.pdf
http://hyperphysics.phy-astr.gsu.edu/hbase/Music/orchins.html
'''
