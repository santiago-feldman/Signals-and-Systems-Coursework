import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.transforms import Bbox
from matplotlib.widgets import Slider, Button, CheckButtons
from matplotlib.patches import Rectangle

import array
import time
import pyaudio
import threading


def draw_delta(ax: Axes, axPos, height, deltacolor, labelText, style="arrow"):

    if(style == "arrow"):
        ax.arrow(axPos, 0, 0, height, head_width=0.01*22000,
                 head_length=3, length_includes_head=True, color=deltacolor, label=labelText)
    elif(style == "dashed"):
        ax.arrow(axPos, 0, 0, height, head_width=0,
                 head_length=0, length_includes_head=True, color=deltacolor, label=labelText, linestyle=(0, (6, 10)))


def is_there_aliasing(fs, fb):
    if fs/2 < fb:
        return True
    else:
        return False


def get_mod_and_phase(n, w, wc):
    return np.sqrt(1/(1+(w/wc)**(n*2))), -n*np.arctan2(w/wc, 1)

# The parametrized function to be plotted


def get_sin_value(t, frequency, amplitude=1) -> any:
    return amplitude * np.sin(2 * np.pi * frequency * t)


def get_alising_frecuency(fb, fs) -> list:

    aliasFrec = []

    k = 1
    while(-22000 < fb - k*fs):
        aliasFrec.append(fb - k*fs)
        aliasFrec.append(-fb - k*fs)
        k = k + 1

    k = 1
    while(22000 > -fb + k*fs):
        aliasFrec.append(-fb + k*fs)
        aliasFrec.append(+fb + k*fs)
        k = k + 1

    return np.sort(aliasFrec)


# The function to be called anytime a slider's value changes


def update(fig, line_dict, axFreq, axBeatFreq, freq_slider, samp_slider, period_slider, filter_order):

    global output_sound, periods

    periods = period_slider

    deltaH = 20  # height delta in frecuency

    axFreq.clear()

    t = np.arange(0, period_slider * (1/freq_slider),
                  (period_slider * (1/(samp_slider*freq_slider*10))))   # start,stop,step

    y = np.cos(t*freq_slider*2*np.pi)

    # Check for aliasing
    aliasFrec = get_alising_frecuency(freq_slider, samp_slider)

    f_beat = 100000
    for i_freq in aliasFrec:
        temp_mod = np.abs(i_freq - freq_slider)
        if f_beat > temp_mod:
            f_beat = temp_mod

    # Drawing signal
    alias2filter = aliasFrec[int(len(aliasFrec)/2):-1]
    try:
        t_sound = np.arange(0, (1/np.min([freq_slider, alias2filter[0], 1])),
                            (1/44100))   # start,stop,step
    except:
        t_sound = np.arange(0, 1,
                            (1/44100))
    aliasmod, alisphase = get_mod_and_phase(filter_order,
                                            alias2filter*2*np.pi, samp_slider*np.pi)

    basemod, basephase = get_mod_and_phase(filter_order,
                                           freq_slider*2*np.pi, samp_slider*np.pi)

    output = basemod*np.cos(t*2*np.pi*freq_slider+basephase)
    output_sound = basemod*np.cos(t_sound*2*np.pi*freq_slider+basephase)
    for i in range(len(alias2filter)):
        aux = aliasmod[i]*np.cos(t*2*np.pi*alias2filter[i]+alisphase[i])

        aux_sound = aliasmod[i] * \
            np.cos(t_sound*2*np.pi*alias2filter[i]+alisphase[i])

        output = np.add(aux, output)
        output_sound = np.add(aux_sound, output_sound)

    aliasmod, alisphase = get_mod_and_phase(filter_order,
                                            aliasFrec*2*np.pi, samp_slider*np.pi)
    # Drawing spectre
    draw_delta(axFreq, aliasFrec[0], aliasmod[0]
               * deltaH, 'orange', "aliasing frec.")
    for i in range(len(aliasFrec)):
        draw_delta(axFreq, aliasFrec[i], aliasmod[i]*deltaH, 'orange', None)

    t_samples = np.arange(0, period_slider * 1/freq_slider, 1/samp_slider)
    y_samples = np.cos(t_samples*freq_slider*2*np.pi)

    line_dict["In"].set_data(t, y)
    line_dict["Out"].set_data(t, output)
    line_dict["Sample"].set_data(t_samples, y_samples)

    # Drawing nquist frecuency
    draw_delta(axFreq, samp_slider/2, deltaH,
               'black', "nyquist frec.", "dashed")
    draw_delta(axFreq, -samp_slider/2, deltaH, 'black', None, "dashed")
    # Drawing sampling frecuency
    draw_delta(axFreq, samp_slider, deltaH, 'r', "sample frec.", "dashed")
    draw_delta(axFreq, -samp_slider, deltaH, 'r', None, "dashed")
    draw_delta(axFreq, freq_slider, basemod*deltaH, 'm',
               "base frec.")      # Drawing input frecuency
    draw_delta(axFreq, -freq_slider, basemod*deltaH, 'm',
               None)      # Drawing input frecuency
    axFreq.set_xlim([-22000, 22000])
    axFreq.set_ylim([0, 30])
    line_dict["In"].axes.set_xlim([0, t[-1]])
    line_dict["In"].axes.set_ylim([-1.5, 1.5])
    axFreq.add_patch(Rectangle((-samp_slider/2, 26), 2*samp_slider/2, 30,
                               edgecolor='pink',
                               facecolor='pink'))
    axFreq.text(0, 27.5, "LP", horizontalalignment='center',
                verticalalignment='center')
    axBeatFreq.clear()
    axBeatFreq.text(0, 0, f"Beat Freq: {f_beat}")
    fig.canvas.draw_idle()


def changeSound(p):

    global output_sound, closeThread, volume, periods
    # for paFloat32 sample values must be in range [-1.0, 1.0]
    stream = p.open(format=pyaudio.paFloat32,
                    channels=1,
                    rate=44100,
                    output=True)

    while(closeThread == False):
        if len(output_sound) != 0:

            # generate samples, note conversion to float32 array
            samplesOnScreenNormalized = output_sound/max(output_sound)*volume

            # per @yahweh comment explicitly convert to bytes sequence
            output_bytes = array.array(
                'f', samplesOnScreenNormalized).tobytes()

            # play. May repeat with different volume values (if done interactively)
            stream.write(output_bytes)
        else:
            time.sleep(0.5)

    stream.stop_stream()
    stream.close()

    p.terminate()


def soundControl(event):

    global volume

    if volume > 0:
        volume = 0.0
    else:
        volume = 0.1


if __name__ == "__main__":

    global closeThread 
    global volume  # range [0.0, 1.0]
    # Define initial parameters
    fb = 1000  # frec base
    fs = 5000  # frec sampling
    volume = 0.0

    closeThread = False

    p = pyaudio.PyAudio()

    # Make grid and add axes
    fig: Figure = plt.figure(num="Instantaneous sampling")
    axSine = fig.add_subplot(3, 5, (1, 4))
    axCheckBox = fig.add_subplot(3, 5, 5)
    axFreq = fig.add_subplot(3, 1, 2)
    axFreqSlider = fig.add_axes([0.3, 0.27, 0.5, 0.03])
    axSampSlider = fig.add_axes([0.3, 0.22, 0.5, 0.03])
    axPeriodSlider = fig.add_axes([0.3, 0.17, 0.5, 0.03])
    axFilterSlider = fig.add_axes([0.3, 0.12, 0.5, 0.03])
    axSound = fig.add_axes([0.3, 0.02, 0.3, 0.075])
    axBeatFreq = fig.add_axes([0.7, 0.05, 0.3, 0.025])

    axBeatFreq.get_xaxis().set_visible(False)
    axBeatFreq.get_yaxis().set_visible(False)
    axBeatFreq.set_frame_on(False)

    axFreq.set_xlabel("f")
    axFreq.set_ylabel("AU")
    axSine.set_xlabel("t")
    axSine.set_ylabel("AU")
    axFreq.legend()
    fig.tight_layout(pad=2.0)

    baseLine, = axSine.plot([1], [1], color='m', label="In")
    outLine, = axSine.plot([1], [1], '-.', color='c', label="Out")
    markLine, = axSine.plot([1], [1], label="Sample", ls='', marker='o')

    line_dict = {"In": baseLine, "Out": outLine, "Sample": markLine}

    # Generate sliders
    freq_slider = Slider(ax=axFreqSlider,
                         label="Base Signal Frecuency",
                         valmin=100,
                         valmax=5000,
                         valinit=fb,
                         orientation="horizontal",
                         valstep=1,
                         valfmt="%d [Hz]"
                         )
    freq_slider.vline._linewidth = 0

    samp_slider = Slider(ax=axSampSlider,
                         label="Sampling Frecuency",
                         valmin=1000,
                         valmax=10000,
                         valinit=fs,
                         orientation="horizontal",
                         valstep=1,
                         valfmt="%d [Hz]"
                         )
    samp_slider.vline._linewidth = 0

    period_slider = Slider(ax=axPeriodSlider,
                           label="Periods Quantity",
                           valmin=1,
                           valmax=100,
                           valinit=4,
                           orientation="horizontal",
                           valstep=1,
                           valfmt="%d"
                           )
    period_slider.vline._linewidth = 0

    filter_slider = Slider(ax=axFilterSlider,
                           label="Filter Order",
                           valmin=1,
                           valmax=30,
                           valinit=4,
                           orientation="horizontal",
                           valstep=1,
                           valfmt="%d"
                           )
    filter_slider.vline._linewidth = 0

    line_colors = [l.get_color() for l in line_dict.values()]

    check = CheckButtons(
        ax=axCheckBox,
        labels=line_dict.keys(),
        actives=[l.get_visible() for l in line_dict.values()],
        label_props={'color': line_colors, 'fontsize': [12]*3},
        frame_props={'edgecolor': line_colors},
        check_props={'facecolor': line_colors},
    )

    bSound = Button(axSound, 'Play/Mute')

    def lambCheck(label):
        ln = line_dict[label]
        ln.set_visible(not ln.get_visible())
        ln.figure.canvas.draw_idle()

    # # register the update function with each slider
    def lambFrec(x): return update(fig, line_dict, axFreq, axBeatFreq,
                                   x, samp_slider.val, period_slider.val, filter_slider.val)

    def lambSample(x): return update(
        fig, line_dict, axFreq, axBeatFreq, freq_slider.val, x, period_slider.val, filter_slider.val)

    def lambPeriod(x): return update(
        fig, line_dict, axFreq, axBeatFreq, freq_slider.val, samp_slider.val, x, filter_slider.val)

    def lambFilter(x): return update(
        fig, line_dict, axFreq, axBeatFreq, freq_slider.val, samp_slider.val, period_slider.val, x)

    # Plot base and sampled senoid

    update(fig, line_dict, axFreq, axBeatFreq, freq_slider.val,
           samp_slider.val, period_slider.val, filter_slider.val)

    freq_slider.on_changed(lambFrec)
    samp_slider.on_changed(lambSample)
    period_slider.on_changed(lambPeriod)
    filter_slider.on_changed(lambFilter)
    check.on_clicked(lambCheck)
    bSound.on_clicked(soundControl)

    # NO BORRAR - PROBAR A DISCRECION
    # NO SE CIERRA EL THREAD, PUEDE SATURAR EL MIC y VARIA LO QUE SE ESCUCHA CON LA CANT DE PERIODOS
    x = threading.Thread(target=changeSound, args=(p,))
    x.start()
    plt.show()
    closeThread = True
