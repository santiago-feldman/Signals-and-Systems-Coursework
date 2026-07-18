import numpy as np
from scipy import signal
import matplotlib.pyplot as plt
import fromDigiToPlot as digilent

path = "Mediciones/HP1.csv"

def hideal(n, wc, ws):
    def _hideal(n, wc, ws):
        T = 2*np.pi/ws
        if n == 0:
            return 1-2*wc/ws
        else:
            return -np.sin(n*wc*T)/(n*np.pi)
    result = []
    for i in n:
        result.append(_hideal(i, wc, ws))

    return np.array(result)


def fir(input, h):
    input = np.pad(input, (len(h)-1, 0))
    y = []
    M = len(h)-1
    for i in range((len(input))-len(h)+1):
        yaux = np.sum(input[i:i+M+1]*h)
        y.append(yaux)

    return np.array(y)


Ap = 1
Apmarg = 0
Aa = 40
Aamarg = 0

Fs = 10e3
Fp = 2000
Fa = 1000

# Calculo el ancho de banda de transicion
BWt = np.pi*2*(Fp-Fa)
wc = np.pi*(Fa+Fp)

# Calculo el delta de riple minimo
delta = np.min(
    [10**(-(Aa+Aamarg)/20), (10**((Ap-Apmarg)/20)-1)/(10**((Ap-Apmarg)/20)+1)])

# Calculo la atenuacion de banda atenuada nueva con el delta minimo calculado
Aanew = -20*np.log10(delta)

# Obtengo D y alpha que son parametros del filtro
if Aanew <= 21:
    D = 0.9222
    alpha = 0
elif 21 < Aanew <= 50:
    D = (Aanew-7.95)/14.36
    alpha = 0.5842*(Aanew-21)**0.4+0.07886*(Aanew-21)
elif Aanew > 50:
    D = (Aanew-7.95)/14.36
    alpha = 0.1102*(Aanew-8.7)

# Obtengo el N minimo para cortar la h(n)

N = int(np.ceil(2*np.pi*Fs*D/BWt+1))

# Calculo los puntos de la ventana que necesito
window = signal.windows.kaiser(N, alpha)
print("Orden del filtro:", N-1)

# Genero la h(n) ventaneada
n = np.arange(-int(N/2), int(N/2+0.6), 1, dtype=int)
hreal = hideal(n, wc, np.pi*2*Fs)*window

# Bode de magnitud a manopla, le paso muchos senos de varias frecuencias y voy calculando el modulo de H(z)
den = np.zeros(len(hreal))
den[-1] = 1
w, mag, phs = signal.dbode((hreal, den, 1/Fs), n=5000)

frec, magnitude, phase = digilent.getDataFromDigilent(path=path)

ax1 = plt.subplot(211)
ax1.set_xlabel("f")
ax1.set_ylabel("dB")
plt.plot(w/2/np.pi, mag)
plt.plot(frec, magnitude)

ax2 = plt.subplot(212)
ax2.set_xlabel("f")
ax2.set_ylabel("grados")
plt.plot(w/2/np.pi, phs)
plt.plot(frec, phase)
plt.show()

print(
    f"double h[] = {'{'}{','.join(map(str, hreal))}{'}'};\nconst int M = {N-1};")
