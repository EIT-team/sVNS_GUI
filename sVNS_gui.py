import tkinter
import tkinter.messagebox
import customtkinter
import serial
import time
import serial.tools.list_ports

#Set default UI appearance parameters
customtkinter.set_appearance_mode("Light")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"
# Define serial port object
ports = serial.tools.list_ports.comports()
serialObj = serial.Serial()
#serialObj = serial.Serial(port='COM4',baudrate=115200, timeout=0.1) # example of non-blocking serial object 

# Define default programming message and an empty message array
deft_command_msg = [0,1,3,230,0,1,0,1,63,3,0,1]
command_msg = []
i = 0
for i in range(12):
    command_msg.append(0)
command_msg = deft_command_msg.copy()

# Define global state bits
PW_state_bit = 0
PF_state_bit = 0
T_on_state_bit = 0
curampl_state_bit = 0
onoff_state_bit = 0
stim_mode_state_bit = 0
channel_nr_state_bit = 0
command_sent = 0
chksum_python = 0

# Empty serial buffer for the serial monitor
serBuffer = ""

# Class - customtkinter app
class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # configure window
        self.title("sVNS_GUI.py")
        self.geometry(f"{1300}x{680}")

        # Create frame for the serial monitor
        self.sermon_frame = customtkinter.CTkFrame(self,fg_color="transparent")
        self.sermon_frame.grid(row=0,column=0,padx=(10, 10),pady=(10, 10))

        # create textbox and string entry for the serial monitor
        self.textbox = customtkinter.CTkTextbox(self.sermon_frame,width=550)
        self.textbox.grid(row=0,column=0,padx=(10, 10), pady=(10, 10),sticky="nsew")
        self.textbox.insert("0.0","\n")
        self.stringEntry = customtkinter.CTkEntry(self.sermon_frame,width=550,placeholder_text="Serial entry")
        self.stringEntry.grid(row=1,column=0,padx=(10, 10), pady=(10, 10),sticky="nsew")
        self.stringEntry_accept = customtkinter.CTkButton(self.sermon_frame,text="Send custom command",
                                                          command=self.customMessageSend)
        self.stringEntry_accept.grid(row=2,column=0,padx=(10, 10), pady=(10, 10),sticky="nsew")
        
        #Predefined operations/communications (read, write, trigger, stop) frame
        self.preDefinedBtns = customtkinter.CTkFrame(self,fg_color="transparent")
        self.preDefinedBtns.grid(row=0,column=1,rowspan=4,padx=(10, 10), pady=(10, 10),sticky="nsew")
        self.memReadOnce_button = customtkinter.CTkButton(self.preDefinedBtns,text="Read all memory once",
                                                          command=self.memReadOnce)
        self.memReadOnce_button.grid(row=0,column=0, padx=(10,10), pady=(10, 10))
        self.memWrite_button = customtkinter.CTkButton(self.preDefinedBtns,text="Write stimulation parameters",
                                                          command=self.memWrite)
        self.memWrite_button.grid(row=1,column=0, padx=(10,10), pady=(10, 10))
        self.memRead_button = customtkinter.CTkButton(self.preDefinedBtns,text="START STIMULATION\n(Raw memory readout)",
                                                          command=self.memRead)
        self.memRead_button.grid(row=2,column=0, padx=(10,0), pady=(10, 10))
        self.readStim_button = customtkinter.CTkButton(self.preDefinedBtns,text="START STIMULATION Trigger mode\n(Stim channel readout)",
                                                          command=self.readStim)
        self.readStim_button.grid(row=3,column=0, padx=(10,10), pady=(10, 10))
        self.stimStop_button = customtkinter.CTkButton(self.preDefinedBtns,text="STOP STIMULATION",
                                                          command=self.stimStop)
        self.stimStop_button.grid(row=4,column=0, padx=(10,10), pady=(10, 10))

        # Create options frame
        self.options_frame = customtkinter.CTkFrame(self,fg_color="transparent")
        self.options_frame.grid(row=0, column = 2, padx=(10, 10), pady=(10, 10), sticky="nsew")
        
        # Com port option selection combobox
        self.com_selection = customtkinter.CTkComboBox(self.options_frame,values=[str(comport) for comport in ports])
        self.com_selection.grid(row=1,column=0,padx=(10, 10), pady=(10, 10), sticky="nsew")
        self.com_confirmation = customtkinter.CTkButton(self.options_frame,text='Get COM port', command=self.initComPort)
        self.com_confirmation.grid(row=2,column=0,padx=(10, 10), pady=(10, 10), sticky="nsew")

        # UI scaling option selection
        self.scaling_label = customtkinter.CTkLabel(self.options_frame, text="UI Scaling:", anchor="w")
        self.scaling_label.grid(row=3, column=0, padx=(10,10), pady=(10, 10))
        self.scaling_optionemenu = customtkinter.CTkOptionMenu(self.options_frame, values=["80%", "90%", "100%", "110%", "120%"],
                                                               command=self.change_scaling_event)
        self.scaling_optionemenu.grid(row=4, column=0, padx=(10,10), pady=(10, 10))

        # Create stimulation parameters frame
        self.parameter_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.parameter_frame.grid(row=1, column=0, padx=(10, 0), sticky="nsew")

        # Create Mode and Current amplitude slider
        self.slider_mode_label = customtkinter.CTkLabel(self.parameter_frame, text="Mode", anchor="w")
        self.slider_mode_label.grid(row=0, column=0, padx=(10, 0),)
        self.slider_mode = customtkinter.CTkSlider(self.parameter_frame, command = self.Stim_Mode_get, from_=1, to=3, number_of_steps=2)
        self.slider_mode.grid(row=1, column=0, padx=(10, 0), sticky="ew")
        self.slider_mode.set(3)
        self.slider_amplitude_label = customtkinter.CTkLabel(self.parameter_frame, text="Amplitude (uA)", anchor="w")
        self.slider_amplitude_label.grid(row=4, column=0, padx=(10, 0))
        self.slider_amplitude = customtkinter.CTkSlider(self.parameter_frame, command = self.amplitude_get, from_=0, to=63, number_of_steps=63)
        self.slider_amplitude.grid(row=5, column=0, padx=(10, 0), sticky="ew")
        self.slider_amplitude.set(0)
        self.slider_dutycycle_label = customtkinter.CTkLabel(self.parameter_frame, text="Stim time per channel (s)", anchor="w")
        self.slider_dutycycle_label.grid(row=0, column=2, padx=(10, 0))
        self.slider_dutycycle = customtkinter.CTkSlider(self.parameter_frame, command = self.Stim_On_times_get, from_=1,to=120,number_of_steps=119)
        self.slider_dutycycle.grid(row=1, column=2, padx=(10, 0))
        self.slider_dutycycle.set(1)

        # Create PW, PF and channel numbers dropdowns
        # Initialise pulse width range and strings
        PWs = range(50,4050,50)
        PWs_str = []
        for PW in PWs:
            PWs_str.append(str(PW))
            # Initialise pulse frequencies range and strings
        PFs = [10, 20]
        PFs_str = []
        for PF in PFs:
            PFs_str.append(str(PF))
            # Initialise "stimulation on" times
        Stim_On_times = [5,10,20,30,60,120]
        Stim_On_times_str = []
        for Stim_On_time in Stim_On_times:
            Stim_On_times_str.append(str(Stim_On_time))
            # Initialise channel list
        Channels = range(0,14)
        Channels_str = []
        for Channel in Channels:
            Channels_str.append(str(Channel))
        self.ChanNumDropdown_label = customtkinter.CTkLabel(self.parameter_frame, text="Channel Number", anchor="w")
        self.ChanNumDropdown_label.grid(row=0, column = 1,padx=(10, 0))
        self.ChanNumDropdown = customtkinter.CTkComboBox(self.parameter_frame,
                                                        values=Channels_str, command = self.Channel_get)
        self.ChanNumDropdown.grid(row=1, column = 1,padx=(10, 0))
        self.ChanNumDropdown.set(0)
        self.PWdropdown_label = customtkinter.CTkLabel(self.parameter_frame, text="Pulse Width (us)", anchor="w")
        self.PWdropdown_label.grid(row=2, column = 0,padx=(10, 0))
        self.PWdropdown = customtkinter.CTkComboBox(self.parameter_frame,
                                                    values=PWs_str, command = self.PW_get)
        self.PWdropdown.grid(row=3, column=0, padx=(10, 0))
        self.PWdropdown.set(50)
        self.PFdropdown_label = customtkinter.CTkLabel(self.parameter_frame, text="Pulse Frequency (Hz)", anchor="w")
        self.PFdropdown_label.grid(row=2, column = 1,padx=(10, 0))
        self.PFdropdown = customtkinter.CTkComboBox(self.parameter_frame,
                                                    values=PFs_str, command = self.PF_get)
        self.PFdropdown.grid(row=3, column=1, padx=(10, 0))
        self.PFdropdown.set(20)
        
        # Create telemetry and on/off switches 
        self.On_Off_state = customtkinter.StringVar(value="1")
        self.Telemetry_state = customtkinter.StringVar(value="1")
        self.telemetry_switch = customtkinter.CTkSwitch(master=self.parameter_frame, text="Telemetry On/Off", command=self.Telemetry_state_get, variable=self.Telemetry_state, onvalue="1", offvalue="0")
        self.telemetry_switch.grid(row=2,column=2,padx=(10, 0))
        self.on_off_switch = customtkinter.CTkSwitch(master=self.parameter_frame, text="Stimulation out On/Off", command=self.On_Off_get, variable=self.On_Off_state, onvalue="1", offvalue="0")
        self.on_off_switch.grid(row=3,column=2,padx=(10, 0))
        
        # Create program / reset frame
        self.program_frame = customtkinter.CTkFrame(self.parameter_frame)
        self.program_frame.grid(row=8,column=1,padx=(10, 0))

        # Reset button and command_msg label 
        self.command_msg_label_1 = customtkinter.CTkLabel(self.parameter_frame, text = "Command word:")
        self.command_msg_label_1.grid(row=6,column=1)
        self.command_msg_label_2 = customtkinter.CTkLabel(self.parameter_frame, text = "", width=200)
        self.command_msg_label_2.configure(text = f"{command_msg}")
        self.command_msg_label_2.grid(row=7,column=1,sticky='nsew')
        self.reset_btn = customtkinter.CTkButton(self.program_frame,command=self.reset,text="Reset")
        self.reset_btn.grid(row=0,column=0)

    # Interactivity functions
    # Use "global" keyword to change the command message and its parts from within the class functions

    def PW_get(self, PW_number):
        global PW_state_bit
        global command_msg
        global PW_byte
        PW_byte = round(int(PW_number)/50)
        # if PW_byte <= 255:
        #     command_msg[0] = 0
        #     command_msg[1] = PW_byte
        # else:
        command_msg[0] = PW_byte >> 8
        command_msg[1] = PW_byte & 0xFF
        app.command_msg_label_2.configure(text = f"{command_msg}")
        app.PWdropdown_label.configure(text=f"Pulse Width (us): {PW_number}")

    def PF_get(self, PF_number):
        # Pulse width will influence the frequency/period -> PW must be set first
        global PF_state_bit
        global command_msg
        global PW_byte
        Period = 1/int(PF_number)
        PF_byte = round(Period/0.00005 - 2*PW_byte)
        #if PF_byte <= 255:
        command_msg[2] = PF_byte >> 8
        command_msg[3] = PF_byte & 0xFF 
        app.command_msg_label_2.configure(text = f"{command_msg}") 
        app.PFdropdown_label.configure(text=f"Pulse Frequency (Hz):  {PF_number}")

    def Stim_On_times_get(self, stim_on_time):
        global T_on_state_bit
        global command_msg
        command_msg[4] = int(stim_on_time) >> 8
        command_msg[5] = int(stim_on_time) & 0xFF
        app.command_msg_label_2.configure(text = f"{command_msg}")
        app.slider_dutycycle_label.configure(text= f"Stim time per channel (s): {stim_on_time}")

    def Channel_get(self, Chan_nr):
        global channel_nr_state_bit
        global command_msg
        command_msg[10] = int(Chan_nr)
        app.command_msg_label_2.configure(text = f"{command_msg}")

    def Stim_Mode_get(self, stim_mode):
        global stim_mode_state_bit
        global command_msg
        command_msg[9] = int(stim_mode)
        stim_modes = {
            1: "Single-channel stimulation",
            2: "Channel scanning (non-loop)",
            3: "Channel scanning (loop, triggers)"
        }
        app.command_msg_label_2.configure(text = f"{command_msg}")
        app.slider_mode_label.configure(text=f"Stimulation mode:\n{stim_modes[stim_mode]}")

    def amplitude_get(self, Iset):
        global curampl_state_bit
        global command_msg
        command_msg[8] = int(Iset)
        I_real = round((Iset * 32 * 1.005), 2)
            # curampl_state_bit = 1
        app.command_msg_label_2.configure(text = f"{command_msg}")
        app.slider_amplitude_label.configure(text = f"Amplitude = {I_real} uA")

    def On_Off_get(self):
        global command_msg
        # global On_Off_state
        # global switch_var
        #print("switch toggled, current value:", self.switch_var.get())
        command_msg[7] = int(self.On_Off_state.get())
        app.command_msg_label_2.configure(text=f"{command_msg}")
        
    def Telemetry_state_get(self):
        global command_msg
        # global Telemetry_state
        command_msg[11] = int(self.Telemetry_state.get())
        app.command_msg_label_2.configure(text=f"{command_msg}")

    def customMessageSend(self):
        customMessage = app.stringEntry.get()
        print(customMessage)
        serialObj.write(bytes(customMessage, encoding = 'utf-8'))

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        customtkinter.set_widget_scaling(new_scaling_float)

    def program_send(self):
        """
        Programmes the device with set stimulation parameters
        """
        global command_sent
        global command_msg

        chksum_python = ((chksum_python + x) for x in command_msg) # checksum to check against after writing to the serial interface
        command_word_str = ','.join(str(x) for x in command_msg)
        command_word_str = '<' + command_word_str
        command_word_str = command_word_str + '>'
        serialObj.write(bytes(command_word_str, encoding = 'utf-8'))
        #time.sleep(1)
        print(command_word_str)
        print(f"Checksum (sent): {chksum_python}")

    def reset(self):
        global PW_state_bit
        global PF_state_bit
        global T_on_state_bit
        global curampl_state_bit
        global onoff_state_bit
        global stim_mode_state_bit
        global channel_nr_state_bit
        global command_sent
        global command_msg
        global deft_command_msg
        print(deft_command_msg)
        PW_state_bit = 0
        PF_state_bit = 0
        T_on_state_bit = 0
        curampl_state_bit = 0
        onoff_state_bit = 0
        stim_mode_state_bit = 0
        channel_nr_state_bit = 0
        command_sent = 0
        command_msg = []
        i = 0
        for i in range(12):
            command_msg.append(0)
        #command_msg = deft_command_msg.copy() # reset the command message to the default one
        #print(deft_command_msg)
        #self.command_msg_label_2.configure(text = f"{command_msg}") # update the label of the command word
        self.slider_mode.set(3) # reset the slider to the default position
        self.Stim_Mode_get(3) # reset the command_msg value byte to default
        self.slider_amplitude.set(0)
        self.amplitude_get(0)
        self.slider_dutycycle.set(1)
        self.Stim_On_times_get(1)
        self.ChanNumDropdown.set(0)
        self.Channel_get(0)
        self.PWdropdown.set(50)
        self.PW_get("50")
        self.PFdropdown.set(20)
        self.PF_get("20")
        self.telemetry_switch.select()
        self.Telemetry_state_get()
        self.on_off_switch.select()
        self.On_Off_get()

  
    def initComPort(self):
        currentPort = self.com_selection.get()
        #print(currentPort) 
        portNumber = currentPort.split(' ')[0]
        print(portNumber)
        serialObj.port = portNumber
        serialObj.baudrate = 115200
        serialObj.timeout = 0 # mandatory to ensure non-locking interface
        serialObj.writeTimeout = 0.1
        serialObj.open()
        #print(serialObj.in_waiting)
        app.readSerial()        

    def readSerial(self):
        #while True:
        #if serialObj.isOpen() and serialObj.in_waiting:
        while serialObj.isOpen():
            c = serialObj.read().decode('latin1') # attempt to read a character from Serial
            #was anything read?
            if len(c) == 0:
                break 
            # get the buffer from outside of this function
            global serBuffer
            # check if character is a delimeter
            if c == '\r':
                c = '' # don't want returns. chuck it
            if c == '\n':
                serBuffer += "\n" # add the newline to the buffer
                #add the line to the TOP of the log
                self.textbox.insert('0.0', serBuffer)
                serBuffer = "" # empty the buffer
            else:
                serBuffer += c # add to the buffer
        self.textbox.after(10, self.readSerial)
        
    def memReadOnce(self):
        print("memReadOnce")
        custom_command_word = '<0>'
        print(custom_command_word)
        serialObj.write(bytes(custom_command_word,encoding='utf-8'))

    def memWrite(self):
        print("memWrite")
        custom_command_word = '<1>'
        print(custom_command_word)
        serialObj.write(bytes(custom_command_word,encoding='utf-8'))

        self.program_send()

    def memRead(self):
        print("memRead")
        custom_command_word = '<2>'
        print(custom_command_word)
        serialObj.write(bytes(custom_command_word,encoding='utf-8'))

    def readStim(self):
        print("ReadStim")
        custom_command_word = '<3>'
        print(custom_command_word)
        serialObj.write(bytes(custom_command_word,encoding='utf-8'))

    def stimStop(self):
        serialObj.write(bytes(' ',encoding='utf-8'))


if __name__ == "__main__":
    app = App()
    #app.readSerial()
    #app.update()
    app.mainloop()