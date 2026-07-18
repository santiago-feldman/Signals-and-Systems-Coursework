#include "Arduino.h"
#define DEBUG_OFF 0
#define DEBUG_ON 1

#define debug DEBUG_ON

#define debug_message(fmt, ...)          \
  do                                     \
  {                                      \
    if (debug)                           \
      Serial.printf(fmt, ##__VA_ARGS__); \
  } while (0)

#define DAC1 25
#define ADCPin 34
#define test_pin 12

#define Tsample 100 // tiempo de muestreo en useg
#include "coef.h"

int ADCValue = 0; // Variable auxiliar para leer el ADC

hw_timer_t *timer = NULL;
void IRAM_ATTR onTimer();
double input[M + 1]; // Vector para guardar la entrada
double y;            // valor para cada Salida
double in_buf[2] = {0, 0};
double out_buf[2] = {0, 0};
// Respuesta impulsiva del filtro, la cambie a un pasatodo.

double fir(const int M, const double *h, double *input_buff, double x);
double iir(double *input_buff, double *output_buff, double x);

void setup()
{
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(test_pin, OUTPUT);
  digitalWrite(LED_BUILTIN, 1);
  // https://espressif-docs.readthedocs-hosted.com/projects/arduino-esp32/en/latest/api/timer.html
  timer = timerBegin(0, 80, true);             // Genera el timer con un divisor de 80 tiempo por cada tick = 80/fclk=80/240MHz
  timerAttachInterrupt(timer, &onTimer, true); // Le pegamos al timer la interrupcion
  // Programamos el disparo de la interrupcion para que se dispare cada Tsample ticks (Tsample esta en useg en este caso)
  timerAlarmWrite(timer, Tsample, true);
  timerAlarmEnable(timer); // Habilitamos la alarma

  delay(1000);
}

void loop()
{
}

void IRAM_ATTR onTimer()
{ // Timer interrupt

  dacWrite(DAC1, (uint8_t)(y));
  ADCValue = analogRead(ADCPin); // 3 Nibbles (12 bits ADC)
  ADCValue >>= 4;                // Keep Most significant byte para que sea de 8 bits porq pinto (asi esta el ejemplo)
  ADCValue -= 128;               // Substract DC component

  // y = fir(M, h, input, ADCValue); // Recordar modificar esto
  y = iir(in_buf, out_buf, ADCValue); // Recordar modificar esto

  y += 128; // Add DC component
}

/*=====================================
* fir.c - FIR filter in direct form
*=====================================
* Usage: y = fir(M, h, w, x);
*
* h = filter impulse response
* w = state
* x = input sample
* M = filter order
* y = Output Sample

* Basicamente esta funcion agarra y va haciendo la convolucion entre la entrada y la h(n)
* Toma la entrada nueva x y la agrega al buffer w, convoluciona con la h para tener la salida y
* despues corre el buffer un lugar para tenerlo listo para la otra iteracion.
* Se puede usar para implementar nuestros filtros FIR, pero por ahi seria mejor hacerlo por taps(me parece mas divertido)
*/

double fir(const int M, const double *h, double *w, double x)
{

  int i;
  double y; /* output sample */
  w[0] = x; /* read current input sample \(x\) */

  for (y = 0, i = 0; i <= M; i++)
    y += h[i] * w[i]; /* compute current output sample \(y\) */

  for (i = M; i >= 1; i--) /* update states for next call */
    w[i] = w[i - 1];       /* done in reverse order */

  return y;
}

double iir(double *input_buff, double *output_buff, double x)
{
  double y; /* output sample */
  double a1 = -1.5371322893124;
  double a2 = 0.9025;
  double G = 0.0354409987789045;

  y = (x - input_buff[1]) * G - a1 * output_buff[0] - a2 * output_buff[1];

  input_buff[1] = input_buff[0];
  input_buff[0] = x;
  output_buff[1] = output_buff[0];
  output_buff[0] = y;

  return y;
}