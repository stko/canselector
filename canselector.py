from tkinter import *
import can

root = Tk()

active_bus = IntVar()
active_bus.set(1)  # initializing the choice

busses = [
    {
        "name" : "Main",
        "group": 0, # the hardcoded input pins at the CANSelector
        "channel": 0, # the input that bus is connected to at the CANSelector
        "speed": 2 # see README.md for details
    },
    {
        "name" : "Engine",
        "group": 0,
        "channel": 0, # the input that bus is connected to at the CANSelector
        "speed": 2 # see README.md for details
    },
    {
        "name" : "Battery",
        "group": 0,
        "channel": 3, # the input that bus is connected to at the CANSelector
        "speed": 2 # see README.md for details
    },
]

bus=can.Bus(interface='socketcan', channel='can0', bitrate=250000)
bus.set_filters(
    [
        {"can_id": 0x601, "can_mask": 0x7FF, "extended": False},
    ]
)

class Timer:
    def __init__(self, parent):
        self.label=parent
        self.label.after(5, self.refresh_label)

    def refresh_label(self):
        msg = can.Message(
            arbitration_id=0x7FF,
            data=[
                0x4D,
                0x41,
                0x46,
                0x49, # means 'MAFI' in Hex
                0x06,
                0x00,
                0x00,
                0x00
            ],
            is_extended_id=False
        )

        try:
            bus.send(msg)
            # print(f"Message sent on {bus.channel_info}")
            msg= True # dummy for while loop entry
            while msg:
                msg = bus.recv(0.1)
                if msg:
                    print("feedback",msg)

        except AttributeError:
            print("Nothing received this time")
        except can.CanError:
            print("Message NOT sent")        
        self.label.after(1000, self.refresh_label)

def ShowChoice():
    print (active_bus.get())

timer = Timer(root)
Label(root, 
      text="""Choose your 
CAN Bus:""",
      justify = LEFT,
      padx = 20).pack()

for index,bus_description in enumerate(busses):
    Radiobutton(root, 
                text=bus_description["name"],
                padx = 20, 
                variable=active_bus, 
                command=ShowChoice,
                value=index
                ).pack(anchor=W)

mainloop()
bus.shutdown()