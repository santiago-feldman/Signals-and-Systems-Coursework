#include <stdio.h>
#include <iostream>
#include "fft.hpp"
#include <fftw3.h>

#include <chrono>
using namespace std::chrono;

#define N 4096

void working_fft(fftw_complex *in, fftw_complex *out)
{
    auto start = high_resolution_clock::now();
    // create a DFT plan
    fftw_plan plan = fftw_plan_dft_1d(N, in, out, FFTW_FORWARD, FFTW_ESTIMATE);
    // execute the plan
    fftw_execute(plan);
    auto stop = high_resolution_clock::now();
    auto duration1 = duration_cast<microseconds>(stop - start);
    std::cout << "La FFTW tarda: " << duration1.count() << std::endl;
    // do some cleaning
    fftw_destroy_plan(plan);
    fftw_cleanup();
}

int main(void)
{
    complex x[N];
    // output array
    complex y1[N];
    complex y2[N];
    // fill the first array with some numbers
    for (int i = 0; i < N; ++i)
    {
        x[i].real(sin(M_PI / 4 * i) + cos(M_PI / 2 * i)); // i.e., { 1, 2, 3, 4, 5, 6, 7, 8 }
        x[i].imag(0);
    }
    working_fft(reinterpret_cast<fftw_complex *>(x), reinterpret_cast<fftw_complex *>(y1));
    auto start = high_resolution_clock::now();
    fft(x, y2, N);
    auto stop = high_resolution_clock::now();
    auto duration2 = duration_cast<microseconds>(stop - start);
    std::cout << "El algoritmo papucho que hicimos tarda: " << duration2.count() << std::endl;
    return 0;
}