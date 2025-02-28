from gpiozero import OutputDevice
from time import sleep

class Stepper:
    CW = -1
    CCW = 1
    """Constructor"""
    def __init__(self, motor_pins, number_of_steps = 32, step_sequence = [[1,0,0,0], [0,1,0,0], [0,0,1,0], [0,0,0,1]]):
        self.motor_pins = [OutputDevice(pin) for pin in motor_pins]  # Control pins
        self.pin_count = len(motor_pins)                             # Number of control pins 
        self.step_sequence = step_sequence                           # Sequence of control signals   
        self.step_number = 0                                         # Which step the motor is on
        self.number_of_steps = number_of_steps                       # Total number of steps per internal motor revolution
        self.direction = self.CW                                     # Rotation direction
        self.step_delay = 60 / self.number_of_steps / 240            # Rotation delay (240rpm == 7.81ms delay)
  
    """Sets speed in revolutions per minute"""
    def set_speed(self, what_speed):
        self.step_delay = 60 / self.number_of_steps / what_speed     # Step delay in seconds
        print("Step Delay: {:.2f}ms".format(self.step_delay * 1000)) 
    """Moves the motor steps_to_move steps.  If the number is negative, the motor moves in the reverse direction."""
    def step(self, steps_to_move):
        # Determine how many steps to left to take
        steps_left = int(abs(steps_to_move))
        # Determine direction
        self.direction = self.CW if steps_to_move > 0 else self.CCW
        # Decrement the number of steps, moving one step each time
        while steps_left > 0:
            if self.direction == self.CCW:
                self.step_number = (self.step_number + 1) % self.number_of_steps
            else:
                self.step_number = (self.step_number - 1) % self.number_of_steps    
            steps_left -= 1
            self.step_motor()

    """Moves the motor forward or backwards"""
    def step_motor(self):
        # Select the correct control signal sequence
        this_step = self.step_number % len(self.step_sequence)
        seq = self.step_sequence[this_step]
        # Set pin state accordingly
        for pin in range(self.pin_count):
            if seq[pin] == 1:
                self.motor_pins[pin].on()
            else:
                self.motor_pins[pin].off()
        sleep(self.step_delay)
        
    """Rotates the motor clockwise indefinitely"""
    def forward(self):
        for i in range(0,1024,1):
            self.step_number = (self.step_number - 1) % self.number_of_steps
            self.step_motor()

    """Rotates the motor counter-clockwise indefinitely"""
    def backward(self):
        for i in range(0,1024,1):
            self.step_number = (self.step_number + 1) % self.number_of_steps
            self.step_motor()
    """Number of motor revolutions"""
    def movearound(self, step_around):
        if step_around >= 0:
            while step_around:
                self.step(32*64)
                step_around -= 1
        elif step_around < 0:
            while step_around:
                self.step(-32*64)
                step_around += 1
    """Motor rotation Angle"""
    def moveangle(self, step_angle):
        self.step((step_angle*32*64)/360)
    