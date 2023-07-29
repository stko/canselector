from tkinter import *
from tkinter import messagebox
import can

send_id=0x600

root = Tk()

active_bus = IntVar()
active_bus.set(1)  # initializing the choice

busses = [
    {
        "name" : "listen",
        "group": 0, # the hardcoded input pins at the CANSelector
        "channel": 15, # the input that bus is connected to at the CANSelector
        "speed": 0 # see README.md for details
    },
    {
        "name" : "Main",
        "group": 0, # the hardcoded input pins at the CANSelector
        "channel": 0, # the input that bus is connected to at the CANSelector
        "speed": 2 # see README.md for details
    },
    {
        "name" : "Engine",
        "group": 0,
        "channel": 1, # the input that bus is connected to at the CANSelector
        "speed": 2 # see README.md for details
    },
    {
        "name" : "Battery",
        "group": 0,
        "channel": 3, # the input that bus is connected to at the CANSelector
        "speed": 2 # see README.md for details
    },
    {
        "name" : "Alien",
        "group": 1,
        "channel": 3, # the input that bus is connected to at the CANSelector
        "speed": 2 # see README.md for details
    },
    {
        "name" : "wrong Speed",
        "group": 0,
        "channel": 3, # the input that bus is connected to at the CANSelector
        "speed": 1 # see README.md for details
    },
]

group_ids={}
last_selected_group=0
can.util.set_logging_level("warning")
bus=can.Bus(interface='socketcan', channel='can0', bitrate=250000)
bus.set_filters(
    [
        {"can_id": send_id | 1, "can_mask": 0x7FF, "extended": False},
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
                if msg and msg.dlc == 8:
                    # get status data
                    status_can_bus=msg.data[4] / 16
                    status_group_id=msg.data[4] % 16
                    status_bitrate_index=msg.data[5]
                    group_ids[status_group_id]=msg.data[:4] # store the id of that group
                    # look if channel and group do match to one of the buttons
                    for index,bus_description in enumerate(busses):
                        if status_can_bus ==bus_description["channel"] and status_group_id==bus_description["group"]:
                            active_bus.set(index) # set that bus as active
                            break
                    state_bits=msg.data[6] * 256 + msg.data[7]
                    for index,bus_description in enumerate(busses):
                        if status_group_id==bus_description["group"]:
                            if bus_description["channel"]< 8 : # state is only available for the first 8 channels
                                actual_bus_state=(state_bits >> ((7-bus_description["channel"])*2))% 4 # one liner to get bus state
                                if actual_bus_state==3:
                                    bus_buttons[index].configure(bg="grey", fg="black")
                                if actual_bus_state==3:
                                    bus_buttons[index].configure(bg="green", fg="black")
                                if actual_bus_state==2:
                                    bus_buttons[index].configure(bg="orange", fg="black")
                                if actual_bus_state==3:
                                    bus_buttons[index].configure(bg="red", fg="yellow")

        except AttributeError:
            print("Nothing received this time")
        except can.CanError:
            print("Message NOT sent")        
        self.label.after(1000, self.refresh_label)

def set_device_parameters(group,channel,bitrate_index):
    if group in group_ids:
        msg = can.Message(
            arbitration_id=send_id,
            data=[ 
                group_ids[group][0],
                group_ids[group][1],
                group_ids[group][2],
                group_ids[group][3],
                channel * 16 + bitrate_index,
                0x00,
                0x00,
                0x00
            ],
            is_extended_id=False
        )

        try:
            bus.send(msg)
        except can.CanError:
            print("set_device_parameters NOT sent")  

def ShowChoice():
    global last_selected_group, bus_buttons
    selection=active_bus.get()

    if busses[selection]["group"]  not in group_ids:
        messagebox.showerror("Error", "The CAN group you want to connect to has not announced itself yet")
        #return

    for group in group_ids: # goes through all known devices
        if busses[selection]["group"] != group:
            set_device_parameters(group,0,0) # deactivate that device
        else:
            set_device_parameters(group,busses[selection]["channel"],busses[selection]["speed"]) # deactivate that device
    print (selection)

timer = Timer(root)
Label(root, 
      text="""Choose your 
CAN Bus:""",
      justify = LEFT,
      padx = 20).pack()

bus_buttons = {}

for index,bus_description in enumerate(busses):
    radio_button=Radiobutton(root, 
                text=bus_description["name"],
                padx = 20, 
                variable=active_bus, 
                command=ShowChoice,
                value=index
                )
    bus_buttons[index]=radio_button
    radio_button.pack(anchor=W)

mainloop()
bus.shutdown()