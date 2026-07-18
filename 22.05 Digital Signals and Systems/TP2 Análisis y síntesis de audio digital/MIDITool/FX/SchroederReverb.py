import numpy as np
from scipy.signal import lfilter
import soundfile as sf
import matplotlib.pyplot as plt
import resampy


class SchroederReverb():
    def __init__(
        self,
        sr,
        gain_direct=1.0,
        gain_reverb=1.0,
        stage_flg={
            "comb": True,
            "ap":   True,
        },
        comb_delay_list=[39.85, 36.10, 33.27, 30.15],  # msec
        comb_gain_list=[0.871, 0.883, 0.891, 0.901],
        cap_delay_list=[21.1,   5.02,  1.72],  # msec
        cap_gain_list=[0.70,   0.70,  0.70],
    ):

        self.sr = sr

        self.gain_direct = gain_direct
        self.gain_reverb = gain_reverb
        self.stage_flg = stage_flg

        self.comb_gain_list = comb_gain_list
        self.generate_parallel_comb(comb_delay_list)

        self.cap_gain_list = cap_gain_list
        self.generate_cascaded_ap(cap_delay_list)

    def round(self, f):
        return int((f * 2.0 + 1.0) // 2)

    def generate_parallel_comb(self, comb_delay_list):
        self.comb_tau_list = [
            self.round(self.sr*d*0.001) for d in comb_delay_list
        ]

        self.parallel_comb_coefs = []
        for k, tau in enumerate(self.comb_tau_list):
            b, a = np.zeros(tau+1), np.zeros(tau+1)
            a[0] = 1.0
            a[tau] = -self.comb_gain_list[k]
            b[tau] = 1.0

            self.parallel_comb_coefs.append([b, a])

    def generate_cascaded_ap(self, cap_delay_list):
        self.cap_tau_list = [
            self.round(self.sr*d*0.001) for d in cap_delay_list
        ]

        self.cascaded_ap_coefs = []
        for k, tau in enumerate(self.cap_tau_list):
            b, a = np.zeros(tau+1), np.zeros(tau+1)

            b[0] = -self.cap_gain_list[k]
            a[0] = 1.0
            b[tau] = 1.0
            a[tau] = -self.cap_gain_list[k]

            self.cascaded_ap_coefs.append([b, a])

    def filt(self, x):
        # x is limited to mono signal (1d numpy array)
        y = np.zeros(x.shape)

        if self.stage_flg["comb"]:
            n_comb = len(self.parallel_comb_coefs)
            for k, (comb_b, comb_a) in enumerate(self.parallel_comb_coefs):
                y[:] += lfilter(comb_b, comb_a, x)
        else:
            y[:] = x

        if self.stage_flg["ap"]:
            for k, (ap_b, ap_a) in enumerate(self.cascaded_ap_coefs):
                y[:] = lfilter(ap_b, ap_a, y)
        else:
            y[:] = y

        # Final stage: mix
        y[:] = x*self.gain_direct + y*self.gain_reverb

        return y
