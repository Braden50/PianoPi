import sys, pygame, pygame.midi
import time
from psonic import *
from lights import *
import asyncio

'''
(b'ALSA', b'Midi Through Port-0', 0, 1, 0)
(b'ALSA', b'Midi Through Port-0', 1, 0, 0)
(b'ALSA', b'Launchkey MK2 61 Launchkey MIDI', 0, 1, 0)
(b'ALSA', b'Launchkey MK2 61 Launchkey MIDI', 1, 0, 0)    
(b'ALSA', b'Launchkey MK2 61 Launchkey InCo', 0, 1, 0)
(b'ALSA', b'Launchkey MK2 61 Launchkey InCo', 1, 0, 0)
'''


# idea tempo + lights

class Piano:
    def __init__(self, lights=None):
        self.inputs = {
            'port': None,    # all channels    
            'midi': None,    # classic midi channels
            'inco': None,    # additional channels (e.g. dials)
        }
        self.outputs = {
            'port': None,
            'midi': None,    
            'inco': None,    
        }
        self.lights = lights
        # self.port = False
        # self.midi = False
        # self.inco = False

        self.extended = False       # if keyboard is in extended mode or not

        self.playing = {}        # keeps track of key states
        self.messages = []

        self.curr_output = 'inco'
        self.curr_input = 'midi'        # might not be
        
        self.synth = None

    def setSynth(self, synth)


    def specifyInput(self, name, inp):
        if "Through" in name:
            self.inputs['port'] = inp
        elif "MIDI" in name:
            self.inputs['midi'] = inp
        elif "InCo" in name:
            self.inputs['inco'] = inp
        else:
            print("Unrocognized input:", name)

    
    def specifyOutput(self, name, out):
        if "Through" in name:
            self.outputs['port'] = out
        elif "MIDI" in name:
            self.outputs['midi'] = out
        elif "InCo" in name:
            self.outputs['inco'] = out
        else:
            print("Unrocognized output:", name)


    def getStreams(self):
        for x in range(0, pygame.midi.get_count()):
            info = pygame.midi.get_device_info(x)
            name = info[1].decode()
            is_input = True if info[2] == 1 else False
            print(x, name, is_input)
            if is_input:
                inp = pygame.midi.Input(x)
                self.specifyInput(name, inp)
            else:
                out = pygame.midi.Output(x)
                self.specifyOutput(name, out)

    
    def classifyPad(self, pad, status):
        if pad == 0 and status == 224:
            return 'pitch'
        if pad == 1 and status == 176: 
            return 'modulation'
        if status == 176:
            return self.classifyAnalog(pad)
        else:
            return self.classifyKey(pad)
    
    def classifyAnalog(self, pad):      
        if 41 <= pad <= 48 or pad == 7: # need more
            return 'levers'
        elif 51 <= pad <= 59:
            return 'numButt'
        elif 102 <= pad <= 103:
            return 'midichannel'
        elif 104 <= pad <= 105:
            return 'plays'
        elif 112 <= pad <= 117:
            return 'controls'


    def classifyKey(self, pad):
        if 36 <= pad <= 51:
            return 'pad'
        elif 48 <= pad <= 108:
            return 'key'
    

    def playKey(self, key, velocity, use_lights=True):
        velocity_scale =  1
        on_decay_scale = 1
        off_decay_scale = 1
        self.playing[key] = {
            'velocity': velocity_scale * velocity,
            'on_decay_scale': on_decay_scale,
            'off_decay_scale' = off_decay_scale
        }
    

    def playLights(self):
        for key in self.playing:
            play()

    
    def sendMessages(self):
        ''' Sends all messages in the queue '''
        if len(self.messages) <= 0:
            return
        self.outputs[self.curr_output].write(self.messages)
        self.messages = []


    def addMessage(self, msg, latency=0):
        self.messages.append([msg, latency])  # kinda uneecessary function call


    def enableExtended(self):
        if self.extended:
            return
        self.addMessage([159, 12, 127])


    def disableExtended(self):
        if not self.extended:
            return
        self.addMessage([159, 12, 0])
    

    def lightAllPads(self, color):
        for pad in range(36, 52):
            self.lightPad(pad, color)


    def lightPad(self, pad, color):
        '''
        color: color code from special map (see pg 6)
        pad: pad code. One of ([36:51, 104, 105])
        '''
        if self.extended:   
            print("Attempting to light pads in extended mode") # possible but could lead to errors      
        self.addMessage([159, pad, color])

    
    def eventLoop(self, lights, POOL_TIME=10, MAX_POOL=1000):
        if self.lights is not None:
            await self.lights.connect()
        while True:
            for name in self.inputs:
                inp = self.inputs[name]
                if inp.poll():                          
                    data = inp.read(MAX_POOL)   # [[[status, data1, data2, data3], timestamp], ...]
                    for msg in data:
                        if name == "midi":
                            status = msg[0][0]
                            pressed = True if status == 144 else False   # 144 = pressed; 128 = let go; else, analog change
                            note = msg[0][1]
                            velocity = msg[0][1]
                            timestamp = msg[1]
                            # self.enableExtended()
                            self.playKey(note, velocity, pressed)
                            # if self.classifyPad(note, status) == "key":
                            #     while True:
                            #         self.enableExtended()
                            #         time.sleep(1)
                            #         self.disableExtended()
                        print(name, data)
            self.sendMessages()
            pygame.time.wait(POOL_TIME)
        await lights.disconnect()


working_uuids = [
     "0000ffd9-0000-1000-8000-00805f9b34fb",
     "0000ffd1-0000-1000-8000-00805f9b34fb",
]

my_address = "42:79:00:00:0A:68"
my_uuid = working_uuids[0]

if __name__=="__main__":
    # number_of_pieces = 8

    # for i in range(16):
    #     s = random.randrange(0,number_of_pieces)/number_of_pieces #sample starts at 0.0 and finishes at 1.0
    #     f = s + (1.0/number

    for _ in range(3):
        play(40)
        play(43)
        play(46)
        time.sleep(3)

    pygame.init()
    pygame.midi.init()

    lights = Lights(my_address, my_uuid)
    piano = Piano(lights=lights)
    piano.getStreams()
    working_uuids = [
     "0000ffd9-0000-1000-8000-00805f9b34fb",
     "0000ffd1-0000-1000-8000-00805f9b34fb",
    ]

    my_address = "42:79:00:00:0A:68"
    my_uuid = working_uuids[0]
    

    loop = asyncio.get_event_loop()
    loop.run_until_complete(piano.eventLoop())
    # piano.eventLoop(lights=lights)
    





'''
https://d2xhy469pqj8rc.cloudfront.net/sites/default/files/novation/downloads/10535/launchkey-mk2-programmers-reference-guide.pdf:

Unless otherwise
stated, all computer to Launchkey MIDI communication mentioned in this guide should be sent
on the InControl Port. 
'''