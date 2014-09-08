#include <pigpio.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#define PIN 18

typedef enum {
    START = 0,
    DOWN18ms = 1,
    UP40us = 2,
    DOWN80us = 3,
    UP80us = 4,
    PREFIX = 5,
    BIT = 6
} State;

State state = START;
int bitNumber =0;
unsigned char data[5];

int z = 0;
int last =0;
void gpioAlertFunc (int gpio, int level, uint32_t tick) {
   //printf("SIG %i %i %u\n", level, state,  tick - last);
   if (state == START) {
       bitNumber = 0;
       memset(data,0,5);
       //printf("\n");
   }   
   if (state == BIT) {
//       printf("%i", tick - last > 50 ? 1:0); 
       if (tick - last > 50) {
           data[bitNumber / 8] |= (0x80 >> (bitNumber % 8)); 
       }
       bitNumber++;
       if(bitNumber == 40) {
///           printf("\n");
///           printf("%02x%02x%02x%02x%02x,", data[0], data[1], data[2], data[3], data[4]);
           unsigned char chksum = data[0];
           int c;
           for (c =1; c <4; c++) {
               chksum += data[c];
           }
           printf("%d.%d,%d.%d,%s\n", data[0], data[1], data[2], data[3], chksum == data[4] ? "OK" : "CRP");
       }
   }

   switch(state) {
       case START: state = DOWN18ms; break;
       case DOWN18ms: state = UP40us; break;
       case UP40us: state = DOWN80us; break;
       case DOWN80us: state = UP80us; break;
       case UP80us: state = PREFIX; break;
       case PREFIX: state = BIT; break;
       case BIT: state = PREFIX; break;
   } 
   last = tick;
   z++;
}


void main() {
   int ret = gpioCfgClock(10, 1, 1);
   if (gpioInitialise() < 0) {
     printf("Failed to initialize PGPIO\n");
   }
   ret = gpioSetAlertFunc(PIN, gpioAlertFunc);

   //printf("ret = %i\n", ret);
   int i;
   //for (i =0; i<30; i++) {
   {
   state = START;
   ret = gpioSetMode(PIN, PI_INPUT);
   sleep(1);
//   ret = gpioSetMode(PIN, PI_OUTPUT);
   ret = gpioWrite(PIN, PI_LOW);
   ///printf("%u, OK\n", gpioTick());
   usleep(10000);
   ret = gpioWrite(PIN, PI_HIGH);
   //printf("%u, OK\n", gpioTick());
   ret = gpioSetMode(PIN, PI_INPUT);
   
   ret= gpioTick();
   int ret2= gpioTick();
   ///gpioSleep(PI_TIME_RELATIVE, 10 ,0);
   usleep(10000);
   ///printf("%u %u %i, --\n", ret, ret2, z);
   z=0;
   }
}
