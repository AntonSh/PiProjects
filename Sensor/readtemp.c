#include <pigpio.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#define NUMPINS 32

typedef enum {
    START = 0,
    DOWN18ms = 1,
    UP40us = 2,
    DOWN80us = 3,
    UP80us = 4,
    PREFIX = 5,
    BIT = 6
} State;


struct PinData {
     State state;
     int bitNumber;
     unsigned char data[5]; 
     int lastTick; 
};

struct PinData Pins[NUMPINS];
char activePins[NUMPINS];
int nActive = 0;

//////////////////////////////////////////

void resetPinData(struct PinData* pd) {
    pd->state = START;
    pd->bitNumber = 0;
    pd->lastTick = 0;
    memset(pd->data, 0, 5);
}
//////////////////////////////////////////

void parseArgs() {
     activePins[0] = 4;
     activePins[1] = 18;
     nActive = 2;
}


void gpioAlertFunc (int gpio, int level, uint32_t tick) {
   if (Pins[gpio].state == BIT) {
       if (tick - Pins[gpio].lastTick > 50) {
           int bit = Pins[gpio].bitNumber;
           Pins[gpio].data[bit / 8] |= (0x80 >> (bit % 8)); 
       }
       Pins[gpio].bitNumber++;
       if(Pins[gpio].bitNumber == 40) {
           unsigned char chksum = Pins[gpio].data[0];
           int c;
           for (c =1; c <4; c++) {
               chksum += Pins[gpio].data[c];
           }
           printf("%d.%d,%d.%d,%s\n", Pins[gpio].data[0], Pins[gpio].data[1], Pins[gpio].data[2], Pins[gpio].data[3], chksum == Pins[gpio].data[4] ? "OK" : "CRP");
       }
   }

   switch(Pins[gpio].state) {
       case START: Pins[gpio].state = DOWN18ms; break;
       case DOWN18ms: Pins[gpio].state = UP40us; break;
       case UP40us: Pins[gpio].state = DOWN80us; break;
       case DOWN80us: Pins[gpio].state = UP80us; break;
       case UP80us: Pins[gpio].state = PREFIX; break;
       case PREFIX: Pins[gpio].state = BIT; break;
       case BIT: Pins[gpio].state = PREFIX; break;
   } 
   Pins[gpio].lastTick = tick;
}


void main() {
   int i;
   int ret = gpioCfgClock(10, 1, 1);
   if (gpioInitialise() < 0) {
     printf("Failed to initialize PGPIO\n");
   }
   parseArgs();

   for (i = 0; i < nActive; i++) {
        resetPinData(&Pins[activePins[i]]);
        gpioSetAlertFunc(activePins[i], gpioAlertFunc);
        gpioSetMode(activePins[i], PI_INPUT);
   }

   usleep(50000);

   for (i = 0; i < nActive; i++) {
       ret = gpioWrite(activePins[i], PI_LOW);
   }

   usleep(18000);
   
   for (i = 0; i < nActive; i++) {
       ret = gpioWrite(activePins[i], PI_HIGH);
       ret = gpioSetMode(activePins[i], PI_INPUT);
   }
   
   usleep(100000);
}
