#include "fft.hpp"
#include <stdio.h>
#include <cmath>

using namespace std::complex_literals;

complex w(int n, int N);
uint R(const uint n, const uint k);
uint pow2(uint exp);

void fft(complex *in, complex *out, int size_n)
{
    if ((size_n != 0) && !((size_n & (size_n - 1)) == 0))
    { // If the size is different from a power of 2 (2^n), exit the function
        return;
    }

    uint gamma = (uint)log2f64(size_n);
    uint N_2 = size_n / 2;
    // Calculo los pesos que se necesitan para el algoritmo
    complex weight[gamma + 1];
    for (int i = 0; i <= gamma; i++)
    {
        weight[i] = w(i, size_n);
    }
    // Bucle de calculo
    /*
    i/aux2power es la cantidad de veces que entra 2^(gamma-r) en la cuenta. Como 2^(gamma-r) es
    la cantidad de entradas (N) dividido la cantidad de grupos de mariposas (2^r), esa division entera
    representa el grupo actual en el que se encuentra computando el algoritmo.

    i + aux2power * (i / aux2power) = indice inferior para la mariposa:
    i recorre de 0 a N/2-1, y el segundo sumando representa el dezplazamiento de indice dentre de cada grupo.
    para la primera iteracion i/aux2power siempre vale 0, entonces esto es un dezplazamiento de 0.
    En otras iteraciones se actualiza esta informacion para el salto correcto de indices entre los grupos

    i + aux2power * (i / aux2power) + aux2power = indice superior para la mariposa:
    Mismo concepto que antes pero desplazado por aux2power que representa el espacio entre alas
    de la mariposa de un grupo.

    R(2 * (i / aux2power), gamma) = orden del W:
    Dado el grupo i/aux2power, calculo es indice del peso correspondiente de esta manera.
    */
    complex aux1, aux2;
    uint aux2power;
    for (uint r = 1; r <= gamma; r++)
    {
        aux2power = pow2(gamma - r);
        if (r == 1)
        {
            // Primera pasada para poblar out. Se saca elementos redundantes que para la primera iteracion
            // siempre son constantes como el i/aux2power que siempre vale 0.
            for (uint i = 0; i < N_2; i++)
            {
                aux1 = in[i] + weight[0] * in[i + aux2power];
                aux2 = in[i + aux2power] - weight[0] * in[i];
                out[i] = aux1;
                out[i + aux2power] = aux2;
            }
        }
        else
        {
            for (uint i = 0; i < N_2; i++)
            {
                aux1 = out[i + aux2power * (i / aux2power)] + weight[R(2 * (i / aux2power), gamma)] * out[i + aux2power * (i / aux2power) + aux2power];
                aux2 = out[i + aux2power * (i / aux2power) + aux2power] - weight[R(2 * (i / aux2power), gamma)] * out[i + aux2power * (i / aux2power)];
                out[i + aux2power * (i / aux2power)] = aux1;
                out[i + aux2power * (i / aux2power) + aux2power] = aux2;
            }
        }
    }

    // Reordeno el arreglo de salida
    for (uint i = 1; i < size_n; i++)
    {
        uint irev = R(i, gamma); // Calculo el indice reverso.
        if (irev >= i)           // Para no swappear porque si.
        {
            // Por algun motivo que no comprendemos la salida tiene que ser conjugada y multiplicada por -1
            // para los indices distintos de 0. Bizarro cuanto menos.
            aux1 = out[i];
            out[i] = -std::conj(out[irev]);
            out[irev] = -std::conj(aux1);
        }
    }
    return;
}

complex w(int n, int N)
{
    return exp(M_PI * 2i * (double)n / (double)N);
}

/*
Funcion de bit reverse eficiente tomada de una respuesta de StackOverflow:
https://stackoverflow.com/questions/746171/efficient-algorithm-for-bit-reversal-from-msb-lsb-to-lsb-msb-in-c
*/
uint R(const uint n, const uint k)
{
    uint r, i;
    for (r = 0, i = 0; i < k; ++i)
        r |= ((n >> i) & 1) << (k - i - 1);
    return r;
}

/*
Potencias de 2 eficientes.
*/
uint pow2(uint exp)
{
    return 1 << exp;
}
