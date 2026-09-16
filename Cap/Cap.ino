#define READ_PIN A1
#define POWER_PIN 40
#define MARGIN 50
#define CAPACITOR_VALUE() analogRead(READ_PIN)
#define CHARGE() digitalWrite(POWER_PIN, HIGH)
#define DISCHARGE() digitalWrite(POWER_PIN, LOW)
#define SEP() "$"
#define PRINT_CAP_VALUE() Serial.print(CAPACITOR_VALUE()); Serial.print(SEP());
#define PRINT(msg) Serial.print(msg);Serial.print(SEP());

enum State{
  CHARGING,
  CHARGED,
  DISCHARGING,
  DISCHARGED 
};
enum State state = DISCHARGED;
const int dischargeThreshold = 0 + MARGIN;
const int chargeThreshold = 1023 - MARGIN;
long int time = 0;

void printState(enum State state){
  if(state == CHARGING){
    PRINT("CHARGING");
    return;
  }
  if(state == CHARGED){
    PRINT("CHARGED");
    return;
  }
  if(state == DISCHARGING){
    PRINT("DISCHARGING");
    return;
  }
  if(state == DISCHARGED){
    PRINT("DISCHARGED");
    return;
  }
}

void setup(){
  Serial.begin(9600);
  pinMode(READ_PIN, INPUT);
  pinMode(POWER_PIN, OUTPUT);
  // Ensure the capacitor must be discharged initialy.
  DISCHARGE();
}


void loop(){
  if(Serial.available() > 0){
    String cmd = Serial.readString();
    cmd.trim();
    if(cmd.equals("CHARGE")){
      state = DISCHARGING;
      printState(state);
      CHARGE();
      time = millis();
      while(CAPACITOR_VALUE() < chargeThreshold){PRINT_CAP_VALUE();}
      state = CHARGED;
      PRINT("ELAPSED_TIME:");
      PRINT(millis() - time);
    }else if(cmd.equals("DISCHARGE")){
      state = DISCHARGING;
      printState(state);
      DISCHARGE();
      time = millis();
      while(CAPACITOR_VALUE() > dischargeThreshold){PRINT_CAP_VALUE();}
      state = DISCHARGED;
      PRINT("ELAPSED_TIME:");
      PRINT(millis() - time);
    }
  }
  printState(state);
}

//    }else if(cmd.equals("DISCHARGE")){
//      state = DISCHARGING;
//      printState(state);
//      DISCHARGE();
//      time = millis();
//      while(CAPACITOR_VALUE() > dischargeThreshold){PRINT_CAP_VALUE();}
//      state = DISCHARGED;
//      PRINT("ELAPSED_TIME:");
//      PRINT(millis() - time);
//    }
