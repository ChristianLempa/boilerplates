#!/usr/bin/env python3
########################################################################
# Filename    : Keypad.py
# Description : The module of matrix keypad 
# Author      : freenove
# modification: 2023/05/15
########################################################################
from gpiozero import InputDevice, OutputDevice
import time
#class Key:Define some of the properties of Key
class Key(object):
    NO_KEY = '\0'
    #Defines the four states of Key
    IDLE = 0
    PRESSED = 1
    HOLD = 2
    RELEASED = 3
    #define OPEN and CLOSED
    OPEN = 0
    CLOSED =1
    #constructor
    def __init__(self):
        self.kchar = self.NO_KEY
        self.kstate = self.IDLE
        self.kcode = -1
        self.stateChanged = False

class Keypad(object):
    NULL = '\0'
    LIST_MAX = 10   #Max number of keys on the active list.
    MAPSIZE = 10    #MAPSIZE is the number of rows (times 16 columns)
    bitMap = [0]*MAPSIZE
    key = [Key()]*LIST_MAX
    holdTime = 500      #key hold time
    holdTimer = 0
    startTime = 0
    #Allows custom keymap, pin configuration, and keypad sizes.
    def __init__(self,usrKeyMap,row_Pins,col_Pins,num_Rows,num_Cols):
        self.rowPins = row_Pins
        self.colPins = col_Pins
        self.numRows = num_Rows
        self.numCols = num_Cols
        
        self.keymap = usrKeyMap
        self.setDebounceTime(10)
    #Returns a single key only. Retained for backwards compatibility.   
    def getKey(self):
        single_key = True
        if(self.getKeys() and self.key[0].stateChanged and (self.key[0].kstate == self.key[0].PRESSED)):
            return self.key[0].kchar
        single_key = False
        return self.key[0].NO_KEY
    #Populate the key list. 
    def getKeys(self):
        keyActivity = False
        #Limit how often the keypad is scanned.
        if((time.time() - self.startTime) > self.debounceTime*0.001):
            self.scanKeys()
            keyActivity = self.updateList()
            self.startTime = time.time()
        return keyActivity
    #Hardware scan ,the result store in bitMap  
    def scanKeys(self):
        #Re-intialize the row pins. Allows sharing these pins with other hardware.
        inputs = list(map(lambda pin: InputDevice(pin, pull_up=True), self.rowPins))
        #bitMap stores ALL the keys that are being pressed.   outputs = OutputDevice(pin_c,active_high=False)
        for pin_c in self.colPins:
            outputs = OutputDevice(pin_c)
            outputs.off()
            i=0
            for r in self.rowPins: #keypress is active low so invert to high.   inputs[i].is_active inputs[i].value
                self.bitMap[self.rowPins.index(r)] = self.bitWrite(self.bitMap[self.rowPins.index(r)],self.colPins.index(pin_c), inputs[i].value)
                i =i+1
            #Set pin to high impedance input. Effectively ends column pulse.
            outputs.on()
            outputs.close()
            outputs = InputDevice(pin_c,pull_up=True)
    #Manage the list without rearranging the keys. Returns true if any keys on the list changed state.      
    def updateList(self):
        anyActivity = False
        kk = Key()
        #Delete any IDLE keys
        for i in range(self.LIST_MAX):
            if(self.key[i].kstate == kk.IDLE):
                self.key[i].kchar = kk.NO_KEY
                self.key[i].kcode = -1
                self.key[i].stateChanged = False
        # Add new keys to empty slots in the key list.
        for r in range(self.numRows):
            for c in range(self.numCols):
                button = self.bitRead(self.bitMap[r],c)
                keyChar = self.keymap[r * self.numCols +c]
                keyCode = r * self.numCols +c
                idx = self.findInList(keyCode)
                #Key is already on the list so set its next state.
                if(idx > -1):
                    self.nextKeyState(idx,button)
                #Key is NOT on the list so add it.
                if((idx == -1) and button):
                    for i in range(self.LIST_MAX):
                        if(self.key[i].kchar == kk.NO_KEY): #Find an empty slot or don't add key to list.
                            self.key[i].kchar = keyChar
                            self.key[i].kcode = keyCode
                            self.key[i].kstate = kk.IDLE    #Keys NOT on the list have an initial state of IDLE.
                            self.nextKeyState(i,button)
                            break   #Don't fill all the empty slots with the same key.
        #Report if the user changed the state of any key.
        for i in range(self.LIST_MAX):
            if(self.key[i].stateChanged):
                anyActivity = True
        return anyActivity      
    #This function is a state machine but is also used for debouncing the keys. 
    def nextKeyState(self,idx, button):
        self.key[idx].stateChanged = False
        kk = Key()
        if(self.key[idx].kstate == kk.IDLE):
            if(button == kk.CLOSED):
                self.transitionTo(idx,kk.PRESSED)
                self.holdTimer = time.time()    #Get ready for next HOLD state.
        elif(self.key[idx].kstate == kk.PRESSED):
            if((time.time() - self.holdTimer) > self.holdTime*0.001):   #Waiting for a key HOLD...  
                self.transitionTo(idx,kk.HOLD)
            elif(button == kk.OPEN):        # or for a key to be RELEASED.
                self.transitionTo(idx,kk.RELEASED)
        elif(self.key[idx].kstate == kk.HOLD):
            if(button == kk.OPEN):
                self.transitionTo(idx,kk.RELEASED)
        elif(self.key[idx].kstate == kk.RELEASED):
            self.transitionTo(idx,kk.IDLE)
            
    def transitionTo(self,idx,nextState):
        self.key[idx].kstate = nextState
        self.key[idx].stateChanged = True
    #Search by code for a key in the list of active keys.
    #Returns -1 if not found or the index into the list of active keys.
    def findInList(self,keyCode):
        for i in range(self.LIST_MAX):
            if(self.key[i].kcode == keyCode):
                return i
        return -1
    #set Debounce Time, The default is 50ms                 
    def setDebounceTime(self,ms):
        self.debounceTime = ms
    #set HoldTime,The default is 500ms
    def setHoldTime(self,ms):
        self.holdTime = ms
    #   
    def isPressed(keyChar):
        for i in range(self.LIST_MAX):
            if(self.key[i].kchar == keyChar):
                if(self.key[i].kstate == self.self.key[i].PRESSED and self.key[i].stateChanged):
                    return True
        return False
    #           
    def waitForKey():
        kk = Key()
        waitKey = kk.NO_KEY
        while(waitKey == kk.NO_KEY):
            waitKey = getKey()
        return waitKey
    
    def getState():
        return self.key[0].kstate
    #   
    def keyStateChanged():
        return self.key[0].stateChanged
    
    def bitWrite(self,x,n,b):
        if(b):
            x |= (1<<n)
        else:
            x &=(~(1<<n))
        return x
    def bitRead(self,x,n):
        if((x>>n)&1 == 1):
            return True
        else:
            return False

#######################EXAMPLE##################################        
ROWS = 4
COLS = 4
keys =  [   '1','2','3','A',
            '4','5','6','B',
            '7','8','9','C',
            '*','0','#','D'     ]
rowsPins = [18, 23, 24, 25]
colsPins = [10, 22, 27, 17]    

def loop():
    keypad = Keypad(keys,rowsPins,colsPins,ROWS,COLS)
    keypad.setDebounceTime(50)
    while(True):
        key = keypad.getKey()
        if(key != keypad.NULL):
            print ("You Pressed Key : %c "%(key) )
        
if __name__ == '__main__':     # Program start from here
    print ("Program is starting ... ")
    try:
        loop()
    except KeyboardInterrupt:  # When 'Ctrl+C' is pressed, the child program destroy() will be  executed.
        print("Ending program")