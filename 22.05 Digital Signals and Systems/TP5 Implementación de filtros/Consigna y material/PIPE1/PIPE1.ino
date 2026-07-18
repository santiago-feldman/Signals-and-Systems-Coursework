// This takes the absolute value of input signal (after substracting DC component of signal)
// Use This to calibrate inpus offset (Input signal 3.3v/2 + 1.5V offset)
// Signal is connected to GPIO 34 (Analog ADC1_CH6) 
const int ADCPin = 34;

#define Tsample 100 //in useg
volatile int i=0;
int ADCValue = 0;


hw_timer_t * timer = NULL;

 
void IRAM_ATTR onTimer() {      // Timer interrupt

         ADCValue = analogRead(ADCPin); //3 Nibbles (12 bits ADC)
         ADCValue>>=4;                  //Keep Most significant byte
         ADCValue-=128;                 //Substract DC component

         if (ADCValue <0)               //Absolute Value
              ADCValue=-ADCValue;

         ADCValue+=128;                 //Add DC component
         
         dacWrite(DAC1,(uint8_t)(ADCValue));
  
}
 
void setup() {
 
  Serial.begin(115200);
 
  timer = timerBegin(0, 80, true);
  timerAttachInterrupt(timer, &onTimer, true);
  timerAlarmWrite(timer, Tsample, true);
  timerAlarmEnable(timer);
 
}
 
void loop() {
 

 
  
}
