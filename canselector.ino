/*
 * made out of the Teensy 4.0 Triple CAN Demo https://github.com/skpang/Teensy40_triple_CAN_demo
 * 
 * For use with:
 * http://skpang.co.uk/catalog/teensy-40-triple-can-board-include-teensy-40-p-1575.html
 * 
 * can1 and can2 are CAN2.0B
 * can3 can be used as  CAN FD, but it's unused here
 * 
 * Ensure FlexCAN_T4 is installed first
 * https://github.com/tonton81/FlexCAN_T4
 * 
 * 
 */
#include <FlexCAN_T4.h>

#define DEFAULTBAUDRATE 500000

FlexCAN_T4<CAN1, RX_SIZE_256, TX_SIZE_16> can1;  // can1 port 
FlexCAN_T4<CAN2, RX_SIZE_256, TX_SIZE_16> can2;  // can2 port

IntervalTimer timer;
uint8_t d=0;
uint8_t tick=0;
uint8_t bus_states[8]= {0,0,0,0,0,0,0,0};
uint8_t bus_errors[8]= {0,0,0,0,0,0,0,0};
uint32_t bit_rates[5]= {
  0,
  125000,
  250000,
  500000,
  1000000
};
uint8_t actual_channel=0;
uint8_t bitrate_index=0; // the actual bus speed. See README.md for details
uint32_t actual_bit_rate=0; // the actual bitrate
uint32_t actual_listen_msgID=0; // the actual sent_id msg ID. See README.md for details
CAN_message_t msg;

// get a unique manufactor number (https://forum.pjrc.com/threads/60034-Teensy-4-0-Serial-Number)

#define OCOTP_CFG0 (*(uint32_t *)0x401F4410)
#define OCOTP_CFG1 (*(uint32_t *)0x401F4420)


void ticker(){
  switch (tick)
  {
  case 0:
    Serial.print("\r-");
    break;
  case 1:
    Serial.print("\r\\");
    break;
  case 2:
    Serial.print("\r|");
    break;
  case 3:
    Serial.print("\r/");
    break;
  }
  tick = (++tick) % 4 ;
}


void setup(void) {
  pinMode(LED_BUILTIN, OUTPUT);   
  digitalWrite(LED_BUILTIN,HIGH);
  Serial.begin(115200);
  Serial.println("CAN Selector");
  digitalWrite(LED_BUILTIN,LOW);

  CANFD_timings_t config;
  config.clock = CLK_24MHz;
  config.baudrate =    DEFAULTBAUDRATE;       // 500kbps arbitration rate
  config.baudrateFD = 2000000;      // 2000kbps data rate
  config.propdelay = 190;
  config.bus_length = 1;
  config.sample = 75;
   
  can1.begin();
  can1.setBaudRate(DEFAULTBAUDRATE,TX);     // 500kbps data rate
  //can1.enableFIFO();
  //can1.enableFIFOInterrupt();
  //can1.onReceive(FIFO, canSniff20);
  //can1.mailboxStatus();
 
  can2.begin();
  can2.setBaudRate(DEFAULTBAUDRATE,LISTEN_ONLY);       // 500kbps data rate
  //can2.enableFIFO();
  //can2.enableFIFOInterrupt();
  //can2.onReceive(FIFO, canSniff20);
  //can2.mailboxStatus();

  //timer.begin(send_status, 500000); // Send frame every 500ms 
}

void send_status()
{
  uint8_t group_id = 0; //TODO: This needs to be calculated out of the config pins
  CAN_message_t msg;
  msg.id = actual_listen_msgID | 1;
  
  msg.buf[0] = OCOTP_CFG1 >> 24;
  msg.buf[1] = (OCOTP_CFG1 >> 16) % 256;
  msg.buf[2] = (OCOTP_CFG1 >> 8) % 256;
  msg.buf[3] = OCOTP_CFG1  % 256;
  msg.buf[4] = (actual_channel % 16) *16 + (group_id % 16);
  msg.buf[5] = (bitrate_index % 16) *16 ;
  msg.buf[6] = bus_states[0]*64 + bus_states[1]*16 +bus_states[2]*4 +bus_states[3];
  msg.buf[7] = bus_states[4]*64 + bus_states[5]*16 +bus_states[6]*4 +bus_states[7];

  msg.seq = 1;
  can1.write(MB15, msg); // write to can1
  //Serial.println("send config");
}

/* 
  Serial.print("T4: ");
  Serial.print("MB "); Serial.print(msg.mb);
  Serial.print(" OVERRUN: "); Serial.print(msg.flags.overrun);
  Serial.print(" BUS "); Serial.print(msg.bus);
  Serial.print(" LEN: "); Serial.print(msg.len);
  Serial.print(" EXT: "); Serial.print(msg.flags.extended);
  Serial.print(" REMOTE: "); Serial.print(msg.flags.remote);
  Serial.print(" TS: "); Serial.print(msg.timestamp);
  Serial.print(" ID: "); Serial.print(msg.id, HEX);
  Serial.print(" IDHIT: "); Serial.print(msg.idhit);
  Serial.print(" Buffer: ");
  for ( uint8_t i = 0; i < msg.len; i++ ) {
    Serial.print(msg.buf[i], HEX); Serial.print(" ");
  } Serial.println();
  */
  //ticker();


void loop() {
  if ( can1.read(msg) ) {
    if (msg.id == 0x7FF &&  // the magic message with 0x7FF and 'MAFI' as content
        msg.buf[0] == 0x4D &&
        msg.buf[1] == 0x41 &&
        msg.buf[2] == 0x46 &&
        msg.buf[3] == 0x49
    ){
      actual_listen_msgID = msg.buf[4]*256 + msg.buf[5] ;
      send_status();
    } else {
        if (msg.id == actual_listen_msgID) {// its a config message to the own device id
         if(msg.buf[0] == OCOTP_CFG1 >> 24 &&
            msg.buf[1] == (OCOTP_CFG1 >> 16) % 256 &&
            msg.buf[2] == (OCOTP_CFG1 >> 8) % 256 &&
            msg.buf[3] == OCOTP_CFG1  % 256)
          {
            actual_channel=msg.buf[4] / 16;
            bitrate_index=msg.buf[4] % 16;
            if (bitrate_index){
              actual_bit_rate=bit_rates[bitrate_index];
              can2.setBaudRate(actual_bit_rate,TX);
            }else{
              can2.setBaudRate(actual_bit_rate,LISTEN_ONLY);
            }
            //TODO: Switch the channel here
            Serial.printf("Actual Channel: %d Actual Bitrate: %d\n", actual_channel, bitrate_index);
            send_status();
          }
          }else{
            can2.write(msg);
          }
    }

  }
  else if ( can2.read(msg) ) {
    can1.write(msg);
  }
}