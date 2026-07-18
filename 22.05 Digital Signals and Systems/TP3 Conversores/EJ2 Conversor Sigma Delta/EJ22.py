import numpy as np
import scipy.signal as sp
import matplotlib.pyplot as plt
from scipy.fft import rfft, rfftfreq


def sigmaDelta(xPrima, len, Vref):

    # Los nombres modelan el diagrama visto
    xRaya = np.zeros(len)
    y_t_ = np.zeros(len)
    y_n_ = np.zeros(len)
    xi = np.zeros(len)

    # Implemento la transferencia de un sigma-delta de primer orden, como el visto en el apunte

    for i in range(0, len):

        # Suma de xRaya = xPrima - y(t)
        xRaya[i] = xPrima[i]-y_t_[i-1]  # if i >0 else xRaya[i]

        # Realizo la integración, que es la suma entre el valor nuevo y el anterior guardado
        xi[i] = xRaya[i] + xi[i-1]     # if i >0 else diferencia[i]

        # Etapa de cuantizacion
        if (xi[i] > 0):
            y_n_[i] = 1
        else:
            y_n_[i] = 0

        # Vuelvo al comienzo del lazo pasando por el DAC
        if y_n_[i] == 1:
            y_t_[i] = Vref
        else:
            y_t_[i] = -Vref

    return y_n_, xi, xRaya


def SDSystem():

    # Variable initialization
    Vref = 0.5
    maxt = 10
    fs = 1000000
    bits = 8

    t = np.linspace(0, maxt, int(maxt * fs))
    tbits = np.linspace(0, maxt, int(maxt * fs/2**(bits)))
    # +  Vref * np.sin(2 * np.pi * 5 * t) +  Vref/2 * np.sin(2 * np.pi * 20 * t)
    x = 0.2 * np.sin(2 * np.pi * 0.5 * t)
    xbits = 0.2 * np.sin(2 * np.pi * 0.5 * tbits)

    # No hace falta el FAA si no te pasas de la fs/2
    y_n, xi, xRaya = sigmaDelta(x, int(maxt * fs), Vref)

    decimated = []

    for i in range(len(y_n)//2**(bits)):
        decimated.append(
            np.sum(y_n[i*2**(bits):(i+1)*2**(bits)])/2**(bits)-Vref)
    plt.subplot(121)

    plt.plot(tbits, xbits)
    plt.plot(tbits, decimated)

    plt.subplot(122)

    error = decimated-xbits
    print(np.mean(error))
    ffterror = rfft(error)
    freqs = rfftfreq(len(error), 1/(fs/2**(bits)))
    plt.plot(freqs, 20*np.log10(np.abs(ffterror)))

    plt.show()


def main():

    SDSystem()


if __name__ == "__main__":
    main()
