from scipy.io import wavfile
from scipy import signal
import numpy as np
import math
import soundfile as sf
import sounddevice as sd
from FX.SchroederReverb import SchroederReverb

# chat GPT + algunas modificaciones
# delay: In ms
# decay: [0,1]


def FXecho(data, params, samplerate=44100):  # delay in ms, decay in (0,1)
    # Generar el eco aplicando el retraso y el decaimiento
    delay = params[0]
    decay = params[1]
    output_audio = np.zeros(len(data))
    output_delay = int((delay/1000) * samplerate)

    for count, e in enumerate(data):
        output_audio[count] = e + decay * data[count - output_delay]

    return output_audio


def FXFlanger(x, params, rate=44100):

    Mo = 0.15*rate
    y = np.zeros(len(x))

    for i in range(len(x)):

        Mn = int(np.floor(Mo*(.5+.5*np.sin(2*np.pi*i*params[0]))))

        if ((i-Mn) > 0 and (i-Mn) < len(x)):
            delayoutput = (params[1])*x[i-Mn]
        else:
            delayoutput = 0

        y[i] = (x[i] + delayoutput)

    return y


def FXReverb(data, params, samplerate=44100):
    decay = params
    schroeder_reverb = SchroederReverb(
        sr=samplerate,
        gain_direct=params[0],
        gain_reverb=params[1],
        stage_flg={
            "comb": True,
            "ap":   True,
        })

    y = schroeder_reverb.filt(data)

    return y


# Lista de efectos
fx_dict = {"Reverb": (FXReverb, ("Direct", 1.0), ("Reverb", 1.0)),
           "Echo": (FXecho, ("Delay", 300), ("Decay", 0.8)),
           "Flanger": (FXFlanger, ("Speed", 20), ("Depth", 0.8))}


class FXInterface:
    def applyFX(audio, fx2apply) -> np.ndarray:
        for fx in fx2apply:
            audio = np.array(fx_dict[fx[0]][0](audio, fx[1]))
        return audio


if __name__ == "__main__":
    mysamplerate, data = wavfile.read('FX\\Clarinet.wav')

    # Prueba del Echo FX
    dealay = 300
    y1 = FXecho(data, [dealay, 0.8], mysamplerate)
    sd.play(y1/y1.max(), mysamplerate)
    sd.wait()
    sf.write("FXecho.wav", y1/y1.max(), mysamplerate)

    # Prueba del Reverb FX
    y2 = FXReverb(data, [1.0, 1.0], mysamplerate)
    sd.play(y2/y2.max(), mysamplerate)
    sd.wait()
    sf.write("FXReverb.wav", y2/y2.max(), mysamplerate)

    # Prueba del Flanger
    y3 = FXFlanger(data, [20, 0.8], mysamplerate)
    sd.play(y3/y3.max(), mysamplerate)
    sd.wait()
    sf.write("FXFlanger.wav", y3/y3.max(), mysamplerate)
