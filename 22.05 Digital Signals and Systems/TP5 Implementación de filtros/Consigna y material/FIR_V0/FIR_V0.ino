
#define DEBUG_OFF  0
#define DEBUG_ON   1

#define debug DEBUG_ON

#define debug_message(fmt,...)          \
  do {              \
    if (debug)          \
       Serial.printf (fmt, ##__VA_ARGS__);     \
  } while(0)



const int ADCPin = 34;
const byte test_pin = 32;

#define Tsample 100 //in useg

int ADCValue = 0;

hw_timer_t * timer = NULL;

double fir(int M,  double *h, double *w,double  x);

double  *w;
double y;
int i;
#include "coef.h"





void IRAM_ATTR onTimer() {      // Timer interrupt



         dacWrite(DAC1,(uint8_t)(y));
         ADCValue = analogRead(ADCPin); //3 Nibbles (12 bits ADC)
         ADCValue>>=4;                  //Keep Most significant byte
         ADCValue-=128;                 //Substract DC component

         digitalWrite(test_pin, HIGH); 
         y = fir(M, h, w, ADCValue); 
         digitalWrite(test_pin, LOW); 
    
         y+=128;                 //Add DC component
      

  
}







void setup() {

  delay(1000);

  timer = timerBegin(0, 80, true);
  timerAttachInterrupt(timer, &onTimer, true);
  timerAlarmWrite(timer, Tsample, true);
  timerAlarmEnable(timer);
 
  w = (double *) calloc(M+1, sizeof(double));
  pinMode(test_pin, OUTPUT);

 
  
}

void loop() {

 
   
 
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
*/
                  
                       

double fir(int M, double *h, double *w,double  x) 
{   

int i;
double y;                             /* output sample */

       w[0] = x;                             /* read current input sample \(x\) */

       for (y=0, i=0; i<=M; i++)
              y += h[i] * w[i];              /* compute current output sample \(y\) */
       
       for (i=M; i>=1; i--)                  /* update states for next call */
              w[i] = w[i-1];                 /* done in reverse order */

       return y;
}
