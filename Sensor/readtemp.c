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
    memset(pd->data, 0, sizeof(pd->data));
}
//////////////////////////////////////////

int parseArgs(int argc, const char** args) {
     
     if (argc < 3) {
         return -1;
     }
     if(strcmp(args[1], "-pins") != 0) {
         return -1;
     }

     int i =2;
     for (i =2; i< argc; i++) {
         int gpio = PIN2IO(atoi(args[i]));
         if (gpio == 0) {
             fprintf(stderr,"Invalid pin number - %s\n", args[i]);
             exit(1);
         }
         activePins[nActive++] = gpio; 
     }
     return 0;
}


void gpioAlertFunc (int gpio, int level, uint32_t tick) {
   if (Pins[gpio].state == BIT) {
       if (tick - Pins[gpio].lastTick > 50) {
           int bit = Pins[gpio].bitNumber;
           Pins[gpio].data[bit / 8] |= (0x80 >> (bit % 8)); 
       }
       Pins[gpio].bitNumber++;
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

char PINS[] = { 0,  0,  2,  0,  3,  0,  4, 14,  0, 15,
              17, 18, 27,  0, 22, 23,  0, 24, 10,  0,
               9, 25, 11,  8,  0,  7,  0,  0,  5,  0,
               6, 12, 13,  0, 19, 16, 26, 20,  0, 21};
               

int IO2PIN(int gpio) {
    int i;
    for (i=0; i<sizeof(PINS); i++) {
       if (PINS[i] == gpio) {
           return i+1;
       }
    }
    fprintf(stderr, "Fatal: cannot map GPIO #%i to pin\n", gpio); 
    exit(1);
}

int PIN2IO(int pin) {
    if (pin < 1 || pin > sizeof(PINS)+1 ) {
        return 0;
    }
    return PINS[pin-1];
}

int main(int argc, const char** argv) {
   int i;
   gpioCfgClock(10, 1, 1);
   if (gpioCfgClock(10, 1, 1) < 0 || gpioInitialise() < 0) {
     fprintf(stderr, "Failed to initialize PGPIO\n");
     return 1;
   }

    //ensure cleanup
    atexit(gpioTerminate);

   if (parseArgs(argc, argv) < 0) {
      fprintf(stderr, "Usage: %s -pins <pin> [<pin>] ...\n", argv[0]);
      return 1;
   }

   /// initialize alert fn for pins
   for (i = 0; i < nActive; i++) {
        resetPinData(&Pins[activePins[i]]);
        int ret = gpioSetAlertFunc(activePins[i], gpioAlertFunc);
        ret  = ret < 0 ? ret : gpioSetMode(activePins[i], PI_INPUT);
        if (ret < 0) {
            fprintf(stderr,"Failed to set up alerts on pin #%i\n", IO2PIN(activePins[i]));
            return 1;
        } 
   }

   usleep(50000);
   // send signal
   for (i = 0; i < nActive; i++) {
        if (gpioWrite(activePins[i], PI_LOW) < 0) {
            fprintf(stderr,"Failed to write to pin #%i\n", IO2PIN(activePins[i]));
            return 1;
        } 
   }

   usleep(18000);
   // tell the sensors that we are waiting for response 
   for (i = 0; i < nActive; i++) {
        int ret = gpioWrite(activePins[i], PI_HIGH);
        ret = ret < 0 ? ret : gpioSetMode(activePins[i], PI_INPUT);
        if (ret < 0) {
            fprintf(stderr,"Failed to write to pin #%i\n", IO2PIN(activePins[i]));
            return 1;
        } 
   }
   
   usleep(100000);

   int ret = 0;

   for (i = 0; i < nActive; i++) {
       int gpio = activePins[i];
       if(Pins[gpio].bitNumber == 40) {
           unsigned char chksum = Pins[gpio].data[0];
           int c;
           for (c =1; c <4; c++) {
               chksum += Pins[gpio].data[c];
           }
           if (chksum == Pins[gpio].data[4]) {
               printf("{\"temp\":%i.%i,\"humidity\":%i.%i,\"pin\":%i}\n", Pins[gpio].data[2], Pins[gpio].data[3], Pins[gpio].data[0], Pins[gpio].data[1], IO2PIN(gpio));
           } else {
               fprintf(stderr, "Checksum mismatch for data read from pin #%i\n", IO2PIN(gpio));
               ret = 1;
           }
       } else {
           ret = 1;
           if(Pins[gpio].bitNumber == 0) {
               fprintf(stderr, "No reply from pin #%i\n", IO2PIN(gpio));
           } else {
               fprintf(stderr, "Incorrect number of bits read from pin #%i\n", IO2PIN(gpio));
           }
       }
   }

   return 0;
}
