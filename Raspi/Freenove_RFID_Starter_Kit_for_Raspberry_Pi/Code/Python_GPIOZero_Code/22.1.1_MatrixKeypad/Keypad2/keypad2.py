import time
from gpiozero import InputDevice, OutputDevice

output_pins = [10, 22, 27, 17]
input_pins = [18, 23, 24, 25]

inputs = list(map(lambda pin: InputDevice(pin, pull_up=True), input_pins))
outputs = list(map(lambda pin: InputDevice(pin, pull_up=True), output_pins))

mapping = [
    ['1', '2', '3', 'A'],
    ['4', '5', '6', 'B'],
    ['7', '8', '9', 'C'],
    ['*', '0', '#', 'D'],
]

pressed = set([])

while True:
    for o in range(4):
        outputs[o].close()
        tmp = OutputDevice(output_pins[o], active_high=False)
        tmp.on()
        for i in range(4):
            key = mapping[i][o]
            if inputs[i].is_active:
                if key == '':
                    continue
                if key not in pressed:
                    print(key)
                    pressed.add(key)
            else:
                if key in pressed:
                    pressed.remove(key)

        tmp.close()
        outputs[o] = InputDevice(output_pins[o], pull_up=True)
    time.sleep(0.02)
