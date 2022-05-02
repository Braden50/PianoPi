import asyncio
from bleak import BleakClient, BleakScanner, BleakError
import time
import math
import os, signal
from getImage import getWaveInfo
#from LEDStripController/LEDStripController import *


not_working_uuids = [
    "0000ffda-0000-1000-8000-00805f9b34fb",
    "0000ffd0-0000-1000-8000-00805f9b34fb",
    '00001800-0000-1000-8000-00805f9b34fb',
    '0000ffd0-0000-1000-8000-00805f9b34fb',
    '0000ffd5-0000-1000-8000-00805f9b34fb'
]

working_uuids = [
     "0000ffd9-0000-1000-8000-00805f9b34fb",
     "0000ffd1-0000-1000-8000-00805f9b34fb",
]

my_address = "42:79:00:00:0A:68"
my_uuid = working_uuids[0]

class Lights:
    def __init__(self, address, uuid):
        self.address = address
        self.uuid = uuid
        self.client = None
        self.connected = False
        self.rgb = [0,0,0]
        self.child = None
    
    async def getClient(self, timeout=1000):
        device = await BleakScanner.find_device_by_address(self.address, timeout=timeout)
        if not device:
            raise BleakError(f"A device with address {self.address} could not be found.")
        print("Device found:", device.address)
        self.client = BleakClient(device.address)
    
    async def connect(self, num_attempts=100, delay=0.2):
        if self.client is None:
            await self.getClient()
        print("Connecting...")
        for _ in range(num_attempts):
            try:
                await self.client.connect()
                connected=True
                print("Connected")
                break
            except Exception as e:
                time.sleep(delay)
        if not connected:
            raise Exception("Connection failed")
    
    
    async def disconnect(self):
        if self.client is not None:
            await self.client.disconnect()

    
    async def updateRGB(self, red, green, blue):
        if self.rgb == [red, green, blue]:
            return
        red = 0 if red < 0 else red
        red = 255 if red > 255 else red
        green = 0 if green < 0 else green
        green = 255 if green > 255 else green
        blue = 0 if blue < 0 else blue
        blue = 255 if blue > 255 else blue
        
        lista = [86, red, green, blue, (int(10 * 255 / 100) & 0xFF), 256-16, 256-86]
        values = bytearray(lista)
        try:
            await self.client.write_gatt_char(self.uuid, values, False)
            self.rgb = [red, green, blue]
        except Exception as e:
            if "Not connected" in e:
                self.connect()
            print("Error:", e)
    
    
    async def waves(self, total_time=600, config=None):
        ''' Assumes if config is provided then it is well formed '''
        print("waves")
        if self.child:
            os.kill(self.child, signal.SIGSTOP)
        child_id = os.fork()
        if child_id: # parent
            self.child = child_id
            return
        og_cfg = {
            'r': {
                'min':15,
                'max':50,
                'period': 15,
                'offset':0
                },
            'b': {
                'min':5,
                'max':20,
                'period': 15,
                'offset':0.33
                },
            'g': {
                'min':0,
                'max':0,
                'period': 5,
                'offset':0.66
                }
            }
        if config is None:
            config = og_cfg
        print(config)
        
        
        start = time.time()
        while True:#(time.time() - start) < total_time:            
            r = int(self.timeWave(config['r']['min'], config['r']['max'], time.time(), config['r']['period'], config['r']['period'] * config['r']['offset']))
            g = int(self.timeWave(config['g']['min'], config['g']['max'], time.time(), config['g']['period'], config['g']['period'] * config['g']['offset']))
            b = int(self.timeWave(config['b']['min'], config['b']['max'], time.time(), config['b']['period'], config['b']['period'] * config['b']['offset']))
            
            await self.updateRGB(r,g,b)
        await self.updateRGB(0,0,0)
            
            
    def timeWave(self, low, high, time, period, offset):
        '''
        maps time wave inputs to sin wave of defined range
        '''
        amp = (high - low) / 2
        mid = low + amp
        k = (2*math.pi) / period
        return mid + (amp * math.sin(k * time + k * offset))


    def getRgbStdIn(self):
        rgb_str = input("\nR,G,B: ")
        rgb_list = rgb_str.strip().split(",")
        try:
            if len(rgb_list) != 3:
                raise Exception("Error. Usage: \"<R>,<G>,<B>\" where vals are 0-255")
            r = int(rgb_list[0])
            g = int(rgb_list[1])
            b = int(rgb_list[2])
        except Exception as e:
            print(e)
            return getRgbStandIn()
        return r, g, b
    
    
    async def manualRgb(self):
        r,g,b = self.getRgbStdIn()
        await self.updateRGB(r,g,b)
    
    
    async def search(self):
        query = input("Query: ").strip()
        if query == "":
            return
        if self.child:
            os.kill(self.child, signal.SIGSTOP)
        child_id = os.fork()
        if child_id: # parent
            self.child = child_id
            await self.search()
            return
        config = getWaveInfo(query)
        await self.waves(config=config)
    
    async def newFork(self):
        if self.child is not None:
            os.kill(self.child, signal.SIGSTOP)
        return os.fork()
    
    
commands = {
    'm':'manually input rgb',
    'waves': 'execute wave',
    'search <query>': 'uses search term to find a vibe of matching colors',
    'help': 'here you are'
}

async def mainControl(lights):
    resp = " "
    while True:
        resp = input("|--> ").strip()
        resp_list = resp.split(" ")
        prog = resp_list[0]
        if prog == "":
            break
        elif prog == "m":
            await lights.manualRgb()
        elif prog == "waves":
            await lights.waves()
        elif prog == "search":
            try:
                query = resp_list[1]   # there's a better way to do this
                await lights.search()
            except:
                print("Usage: search <query>")
        elif prog == "help":
            print(commands)
        else:
            print("Invalid program, use 'help'?")
            
            
            
        
async def main(address, uuid):
    lights = Lights(address, uuid)
    await lights.connect()
    await mainControl(lights)
    await lights.disconnect()


if __name__=="__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(my_address, my_uuid))