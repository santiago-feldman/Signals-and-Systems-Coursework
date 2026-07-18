#ifndef FFT_H
#define FFT_H

#include <complex.h>
#include <stdio.h>

#define complex std::complex<double>

void fft(complex *in, complex *out, int size_n);

#endif