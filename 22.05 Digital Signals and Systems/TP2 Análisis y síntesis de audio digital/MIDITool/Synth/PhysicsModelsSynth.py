from collections import deque
import logging
import numpy as np
from scipy.io import wavfile
import matplotlib.pyplot as plt
import sounddevice as sd
import mido
from scipy import signal
from MIDI.Midi import midinote2freq, parse_midi_file

''' 
Implements synth physics models based on Karplus-Strong model. Where:
# decay = RL = note decay constant
# samples = L = low pass length
# sound = track to apply synth
'''


def physicsModelSynth(note, velocity, duration, decay, b):

    out = []
    fs = 44100
    L = noteToFilterDelay(fs, note)
    n = np.random.uniform(-1, 1, size=L)
    padding_dur = int(duration*fs)-len(n) if int(duration*fs)-len(n) > 0 else 0
    sound = np.concatenate((n, np.zeros(padding_dur)))

    # Creating and initilizing delay lines
    dl1 = deque(maxlen=1)
    dl1.append(0)
    dl2 = deque(maxlen=L)
    for i in range(L):
        dl2.append(0)
    dl3 = deque(maxlen=L+1)
    for i in range(L+1):
        dl3.append(0)

    # Compute output
    for i in range(len(sound)):

        x = sound[i]
        xr1 = dl1.popleft()
        ydl = dl2.popleft()
        ydl1 = dl3.popleft()

        y = (x + xr1 + decay*(ydl1 + ydl))/2
        if np.random.uniform(0, 1) > b:
            y = -y
        out.append(y)

        dl1.append(x)
        dl2.append(y)
        dl3.append(y)
    out = np.array(out)
    logging.debug(f"Physics max: {out.max()}")
    return out*(velocity/127)


def noteToFilterDelay(fs, note):
    fn = midinote2freq(note)
    return (int)(fs/fn-1/2)


def synthetizeInstrumentPM(track, instrument, vol):

    if instrument == "Guitarra electrica":
        sound = synthTrack(track=track, vol=vol, decay=1, b=1)
    elif instrument == "Tambor":
        sound = synthTrack(track=track, vol=vol, decay=0.6, b=0.5)
    elif instrument == "Arpa":
        sound = synthTrack(track=track, vol=vol, decay=0.99, b=0)

    return sound


def synthTrack(track, vol, decay, b):
    # Set sample rate and duration
    fs = 44100
    duration = np.ceil(track[-1]["time"]+track[-1]["duration"])
    y = np.zeros(int(fs*duration))

    for curr in track:
        note = curr["note"]
        velocity = curr["velocity"]
        time = curr["time"]
        duration = curr["duration"]
        y_note = physicsModelSynth(note, velocity, duration, decay, b)
        start = int(time*fs)
        end = start + len(y_note)
        y[start:end] += y_note
    y = y * vol

    return y


def testSynth():
    # Read MIDI track using mido
    parsed_tracks = parse_midi_file('./Res/Foo Fighters - Everlong.mid')
    mid = mido.MidiFile('./Res/Foo Fighters - Everlong.mid')

    y = synthetizeInstrumentPM(
        parsed_tracks[1][:50], "electric_guitar", vol=0.05)

    sd.play(y, 44100)
    sd.wait()
    # wavfile.write("test.wav", data=y/y.max(), rate=44100)


def plotZerosAndPoles(orderFilter, decay):
    # Define the transfer function
    num = np.zeros(orderFilter+1)
    den = np.zeros(orderFilter+1)

    num[0] = 1
    num[1] = 1

    den[0] = 2
    den[-2] = -decay
    den[-1] = -decay

    sys = signal.TransferFunction(num, den)

    # Get the poles and zeros of the transfer function
    zeros = sys.zeros
    poles = sys.poles

    # Create a figure to plot on
    fig, ax = plt.subplots()

    # Plot the zeros as blue 'o' markers
    ax.plot(zeros.real, zeros.imag, 'bo', label='Ceros')

    # Plot the poles as red 'x' markers
    ax.plot(poles.real, poles.imag, 'rx', label='Polos')

    # Add a unit circle for reference
    unit_circle = plt.Circle((0, 0), 1, fill=False, color='black')
    ax.add_artist(unit_circle)

    # Set the axis limits and add a title and legend
    ax.set_xlim([-2, 2])
    ax.set_ylim([-2, 2])
    ax.set_aspect('equal')
    ax.set_title(f'Parmetros L = {orderFilter}, Rl = {decay}')
    ax.legend()

    # Display the plot
    plt.show()


def plotPhaseVSb(orderFilter, decay):

    b = 0.5
    N = 100
    fig = plt.figure()
    ax = fig.add_subplot(111)

    # Define the transfer function
    num = np.zeros(orderFilter+1)
    den = np.zeros(orderFilter+1)

    num[0] = 1
    num[1] = 1
    den[0] = 2
    den[-2] = -decay
    den[-1] = -decay

    for i in range(N):

        if np.random.uniform(0, 1.00000001) >= b:
            den = -den

        sys = signal.TransferFunction(num, den)

        # Compute the frequency response of the transfer function
        w, mag, phase = sys.bode()

        # Compute the magnitude and phase response
        mag = 20*np.log10(abs(mag))

        ax.semilogx(w/(2*np.pi), phase)

    # Plot the phase response on the second subplot
    ax.set_xlabel('Frecuencia (Hz)')
    ax.set_ylabel('Fase (grados)')

    # Set the axis limits and add gridlines
    ax.grid(True, which='both')
    ax.grid(True, which='both')

    # Display the plot
    plt.show()


def plotBodeNormi(orderFilter, decay):

    b = 0
    N = 100

    # Define the transfer function
    num = np.zeros(orderFilter+1)
    den = np.zeros(orderFilter+1)

    num[0] = 1
    num[1] = 1
    den[0] = 2
    den[-2] = -decay
    den[-1] = -decay

    if np.random.uniform(0, 1) > b:
        den = -den

    sys = signal.TransferFunction(num, den)

    # Compute the frequency response of the transfer function
    w, mag, phase = sys.bode()

    # Compute the magnitude and phase response
    mag = 20*np.log10(abs(mag))

    # Create a figure with two subplots for the magnitude and phase response
    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)

    # Plot the magnitude response on the first subplot
    ax1.semilogx(w/(2*np.pi), mag)
    ax1.set_ylabel('Magnitud (dB)')
    ax1.set_title('Bode')

    # Plot the phase response on the second subplot
    ax2.semilogx(w/(2*np.pi), phase)
    ax2.set_xlabel('Frecuencia (Hz)')
    ax2.set_ylabel('Fase (grados)')

    # Set the axis limits and add gridlines
    ax1.grid(True, which='both')
    ax2.grid(True, which='both')

    # Display the plot
    plt.show()


if __name__ == "__main__":

    L = 40
    # plotZerosAndPoles(L, 0.99)
    plotPhaseVSb(L, 0.99)
    pass
