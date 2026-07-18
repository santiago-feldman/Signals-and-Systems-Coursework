import numpy as np
import scipy.signal as sp
import matplotlib.pyplot as plt
from  matplotlib import patches
import fromDigiToPlot as digilent

# Config
FO = 1e3
DELTAFO = 100
FS = 10e3
path = "Mediciones/BPIIR2Zoom.csv"

def main():

    wo = 2 * np.pi * (FO/FS)
    dwo = DELTAFO/FO
    R = (2-dwo)/2

    a1 = -2*R*np.cos(wo)
    a2 = R**2
    win = np.arange(500, 1500, 1)
    sp.freqz(num, den, fs=FS, worN=win)
    num = [1, 0, 1]
    den = [1, a1, a2]
    fre, gain = sp.freqz(num, den, fs=FS, worN=[FO])
    print(gain)
    gain = np.abs(gain[0])
    num = [1/gain, 0, 1/gain]
    print(a1, a2, 1/gain)
    # Frecuency response
    w, h = np.abs(sp.freqz(num, den, fs=FS, worN=10000))

    # Impulse response
    t, y = sp.dimpulse((num, den, 1), n=100)

    # Zeros and Poles
    if np.max(den) > 1:
        kn = np.max(den)
        b = b/float(kn)
    else:
        kn = 1

    if np.max(den) > 1:
        kd = np.max(den)
        den = den/float(kd)
    else:
        kd = 1

    # Get the poles and zeros
    p = np.roots(den)
    z = np.roots(num)
    k = kn/float(kd)

    fig, axs = plt.subplots(1, 3)
    uc = patches.Circle((0, 0), radius=1, fill=False,
                        color='black', ls='dashed')
    axs[2].add_patch(uc)

    # Plot the zeros and set marker properties
    t1 = plt.plot(z.real, z.imag, 'go', ms=10)
    plt.setp(t1, markersize=10.0, markeredgewidth=1.0,
             markeredgecolor='k', markerfacecolor='g')

    # Plot the poles and set marker properties
    t2 = plt.plot(p.real, p.imag, 'rx', ms=10)
    plt.setp(t2, markersize=12.0, markeredgewidth=3.0,
             markeredgecolor='r', markerfacecolor='r')

    axs[2].spines['left'].set_position('center')
    axs[2].spines['bottom'].set_position('center')
    axs[2].spines['right'].set_visible(False)
    axs[2].spines['top'].set_visible(False)
    # set the ticks
    r = 1.5
    plt.axis('scaled')
    plt.axis([-r, r, -r, r])
    ticks = [-1, -.5, .5, 1]
    plt.xticks(ticks)
    plt.yticks(ticks)

    axs[0].plot(w, 20*np.log10(h))
    axs[0].title.set_text('|H(z)|')
    axs[1].plot(t, np.squeeze(y))
    axs[1].title.set_text('h(n)')
    axs[2].title.set_text('Poles and Zeros')
    plt.show()

def paraDani():

    wo = 2 * np.pi * (FO/FS)
    dwo = DELTAFO/FO
    R = (2-dwo)/2

    G = 1
    a1 = -2*R*np.cos(wo)
    a2 = R**2

    num = [G, 0, G]
    den = [1, a1, a2]
    win = np.arange(500, 1500, 1)
    
    fre, gain = sp.freqz(num, den, fs=FS, worN=[FO])
    gain = np.abs(gain[0])
    num = [1/gain, 0, 1/gain]
    
    #Frecuency response
    w, h = sp.freqz(num, den, fs=FS, worN=win)
    phs = np.angle(h, deg=True)
    h = np.abs(h)
    h = 20*np.log10(h)

    #Impulse response
    t, y = sp.dimpulse((num, den, 1), n=100)

    frec, magnitude, phase = digilent.getDataFromDigilent(path=path)
    
    ax1 = plt.subplot(211)
    ax1.set_xlabel("f")
    ax1.set_ylabel("dB")
    plt.plot(w, h)
    plt.plot(frec, magnitude)

    ax2 = plt.subplot(212)
    ax2.set_xlabel("f")
    ax2.set_ylabel("grados")
    plt.plot(w, phs)
    plt.plot(frec, phase)
    plt.show()

if __name__ == "__main__":
    paraDani()