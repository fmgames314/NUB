#!/usr/bin/env python
# -*- coding: utf-8 -*-import re
# using https://pypi.org/project/pythonping/
import threading
import time
import asyncio
from websockets import WebSocketServerProtocol, serve
from asyncio import gather, run, Event
import json
from aioserial import AioSerial
from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM
import sys
import os
import re
from gpiozero import CPUTemperature
import copy
# python files
import IMU

# global variables
cpu = CPUTemperature()
serial_port = None
socket_port = None   
gamePadData = [] 
state = {}
state["driveMode"] = 0
state["ledMemory_state"] = 0
joyNames = [
    "Dpad_up",
    "Dpad_down",
    "Dpad_left",
    "Dpad_right",
    "Triangle",
    "X",
    "Square",
    "Circle",
    "Start",
    "Select",    
    "L3",
    "R3", 
    "L1",
    "R1", 
    "L2",
    "R2", 
    "Left_Joystick_up",
    "Left_Joystick_down",
    "Left_Joystick_left",
    "Left_Joystick_right",  
    "Right_Joystick_up",
    "Right_Joystick_down",
    "Right_Joystick_left",
    "Right_Joystick_right", 
]

def getState():
    return state


def getSystemIP():
    s = socket(AF_INET, SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(("10.255.255.255", 1))
        IP = s.getsockname()[0]
    except:
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP


class PacketSender:

    def __init__(self, serial_port):
        self.serial = serial_port

    async def sendPacketOverSerial(self, packet):
        # print(packet)
        packet = packet + "\n"
        await self.serial.write_async(packet.encode())

    async def encodeSend(self, flag, inData):
        packet = self.encodePacket(flag,inData)
        await self.sendPacketOverSerial(packet)

    def calcualuteCheckSum(self, message):
        return sum(bytearray(message, encoding="ascii"))

    def findFlag(self, packet):
        try:
            return (packet.split("@"))[1].split("@")[0]
        except:
            print("Could not find flag in packet")
            return ""

    def encodePacket(self, flag, inData):
        output = ""
        try:
            output = "@" + flag + "@"
            for param in inData:
                output += str(param) + ","
            checkSum = self.calcualuteCheckSum(output)
            output += str(checkSum)
        except Exception as e:
            print(e)
        return output

    def decodePacket(self, flag, packet):
        try:
            # get checksum of packet
            originalPacket = packet[0 : packet.rfind(",")] + ","
            packetEcc = self.calcualuteCheckSum(originalPacket)
            # break packet apart
            packetNoFlag = packet.replace("@" + flag + "@", "")
            packetList = packetNoFlag.split(",")
            packetList[-1] = re.sub(r"\W+", "", packetList[-1])
            ecc = packetList[-1]
            if str(ecc) == str(packetEcc):
                return packetList
            else:
                print("Bad packet checksum")
                return [""]
        except:
            print("Could not decode packet")
            return [""]

async def OLED_Print(fmp,text):
    await fmp.encodeSend("LCD",[text])
async def OLED_Clear(fmp):
    await fmp.encodeSend("LCD_CLEAR",["0"])

# headlight LED
async def Set_LED(fmp,ledState):
    ledState = int(ledState) # makes ledState a 0 or 1 if it's a true or false
    await fmp.encodeSend("LED",[ledState])
async def toggleLED(fmp,sta):
    sta["ledMemory_state"] = not sta["ledMemory_state"]
    await Set_LED(fmp,sta["ledMemory_state"])
# motors
async def driveMotors(fmp,sta,motorL,motorR):
    await fmPacker.encodeSend("MOTOR",[motorL,motorR]) 

# servos 
async def driveServos(fmp,sta,r_pit,l_pit,l_yaw, r_yaw):
    await fmPacker.encodeSend("SERVO",[r_pit,l_pit,l_yaw, r_yaw])
    # (r_pit,l_pit,l_yaw, r_yaw)
    # (more up, more down, more left, more left )

def mapRange(x, in_min, in_max, out_min, out_max):
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;

def normalizeJoysticks(up,down,left,right):
    Axis_V = 0
    if up[0] > .1:
        Axis_V = abs(up[0])
    if down[0] < -.1:
        Axis_V = -abs(down[0])
    Axis_H = 0
    if left[0] > .1:
        Axis_H = abs(left[0])
    if right[0] < -.1:
        Axis_H = -abs(right[0])
    return Axis_V,Axis_H

# drive the robot loop
gamepad = {}
gamepad_last = {}
async def driveTheRobot(sta):
    try:
        if len(sta["controller"]) > 0: # only if the controller list is populated
            # map the jot sticks to a easy to use dictionary
            gamepad_last = copy.deepcopy(gamepad)
            i = 0
            for namedex in joyNames:
                gamepad[namedex] = sta["controller"][i]
                i+=1
            # normalize jotsticks and mapping to make it easier to code
            lAxis_V,lAxis_H = normalizeJoysticks(gamepad["Left_Joystick_up"],gamepad["Left_Joystick_down"],gamepad["Left_Joystick_left"],gamepad["Left_Joystick_right"])
            rAxis_V,rAxis_H = normalizeJoysticks(gamepad["Right_Joystick_up"],gamepad["Right_Joystick_down"],gamepad["Right_Joystick_left"],gamepad["Right_Joystick_right"])
            if len(gamepad) > 0 and len(gamepad_last) > 0:
                # do things with the gamepad states
                # Lights with Triangle button
                if gamepad["Triangle"] == 1 and gamepad_last["Triangle"] == 0:
                    await toggleLED(fmPacker,sta)
                # check L1 button
                if gamepad["L1"] == 1: #L1 pressed, drive SERVOS with joysticks
                    print(lAxis_H,rAxis_H)
                    r_pit = mapRange(rAxis_V,-1,1,180,0)
                    l_pit = mapRange(lAxis_V,-1,1,0,180)
                    l_yaw = mapRange(lAxis_H,-1,1,180,0)
                    r_yaw = mapRange(rAxis_H,-1,1,180,0)
                    await driveServos(fmPacker,sta,r_pit,l_pit,l_yaw, r_yaw)
                    # (more up, more down, more left, more left )
                else: #L1 not pressed, drive MOTORS with joysticks
                    leftThrottle = mapRange(lAxis_V,-1,1,-255,255)
                    rightThrottle = mapRange(rAxis_V,-1,1,-255,255)
                    await driveMotors(fmPacker,sta,leftThrottle,rightThrottle)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        # print(e)






async def sendDataToWebsocket(websocket):
    try:
        json_data = {}
        json_data["event"] = "displayData"
        json_data["temp"] = getState()["cpuTemp"]
        json_data["volt"] = getState()["voltage"]
        json_data["xa"] = 360-(getState()["x_angle"])
        json_data["ya"] = getState()["y_angle"]
        json_out = json.dumps(json_data)
        await websocket.send(str(json_out))
    except:
        print("couldn't send data to websocket")


async def consumer_handler(websocket: WebSocketServerProtocol):
    async for message in websocket:
        try:
            packet = json.loads(message)
            try:
                # print(packet)
                if packet["event"] == "gamepadData": # got controller data
                    controllerData = packet["listOfGamepad"]
                    tempState = getState()
                    tempState["controller"] = controllerData
                    await driveTheRobot(getState())
                if packet["event"] == "saveController": # Save a controller Cal
                    fileName = packet["controllerName"]
                    dataForfile = message
                    with open("conCal_"+str(fileName)+'.json', 'w') as json_file:
                        json.dump(dataForfile, json_file)
                if packet["event"] == "getController": # got controller data               
                    for file in os.listdir("./"):
                         filename = os.fsdecode(file)
                         if filename.endswith(".json"): 
                            with open(filename) as json_file:
                                json_data_str = json.load(json_file)
                                json_data = json.loads(json_data_str)
                                json_data["event"] = "controllerCals"
                                json_out = json.dumps(json_data)
                                await websocket.send(str(json_out))
                         else:
                             continue

            except Exception as e:
                print("error with consumer" + str(e))
        except:
            print("failed to packet.loads: " + str(e))


async def producer_handler(websocket):
    while True:
        await sendDataToWebsocket(websocket)
        await asyncio.sleep(.4)


async def handler(websocket: WebSocketServerProtocol, path) -> None:
    # make the handlers
    print("client connected")
    consumer_task = asyncio.ensure_future(consumer_handler(websocket))
    producer_task = asyncio.ensure_future(producer_handler(websocket))
    done, pending = await asyncio.wait(
        [consumer_task, producer_task], return_when=asyncio.FIRST_COMPLETED,
    )
    for task in pending:
        task.cancel()

async def readSerialFromNUB(state):
    print("Spawning read NUB Serial", flush=True)
    # setup led modes
    await asyncio.sleep(.2)
    await fmPacker.encodeSend("LED_MODE",["3"])
    await asyncio.sleep(.2)
    await fmPacker.encodeSend("LED_BRIGHTNESS",["60"])
    await asyncio.sleep(.2)
    # main loops
    while True:
        # When we get a new line, parse it and fill out the appropriate data structures
        line = await fmPacker.serial.readline_async()
        try:
            packet = line.decode("utf-8")
        except UnicodeDecodeError:
            print("Could not decode incoming arduino packet")
        flag = fmPacker.findFlag(packet)
        packet_data = fmPacker.decodePacket(flag, packet)
        if flag == "DATA":  #this is loop of data that comes in from arduino
            # set voltage to state
            state["voltage"] = packet_data[0]
            # read from IMU.py file pdate to state
            state["x_angle"],state["y_angle"] = IMU.readGyroValues()
            # loop for LCD 
            if time.time()-state["LCDTimer"] > 3:
                state["LCDTimer"] = time.time()
                # x second loop
                state["myip"] = getSystemIP()
                state["cpuTemp"] = str(round(cpu.temperature))
                await OLED_Clear(fmPacker)
                await OLED_Print(fmPacker,state["myip"]) 
                await OLED_Print(fmPacker,"CPU: "+state["cpuTemp"]+"*C" ) 
                await OLED_Print(fmPacker,str(state["voltage"])+" volts" ) 
                if state["driveMode"] < 2:
                    if "controller" in state:
                        if len(state["controller"]) == 0:
                            await OLED_Print(fmPacker,"Cal Controller") 
                            for i in range(19):
                                await fmPacker.encodeSend("L",[i,200,(i*2),0])
                                await asyncio.sleep(.03)
                                await fmPacker.encodeSend("L",[37-i,200,(i*2),0])
                                await asyncio.sleep(.03)
                            for i in range(19):
                                await fmPacker.encodeSend("L",[i,0,0,0])
                                await asyncio.sleep(.03)
                                await fmPacker.encodeSend("L",[37-i,0,0,0])
                                await asyncio.sleep(.03)
                        else:
                            await OLED_Print(fmPacker,"Controller READY!") 
                            state["driveMode"] = 2
                            for i in range(19):
                                await fmPacker.encodeSend("L",[i,0,10+(i*5),255])
                                await asyncio.sleep(.05)
                                await fmPacker.encodeSend("L",[37-i,0,10+(i*5),255])
                                await asyncio.sleep(.05)
                            await asyncio.sleep(2)
                            # off
                            for i in range(19):
                                await fmPacker.encodeSend("L",[i,0,0,0])
                                await asyncio.sleep(.1)
                                await fmPacker.encodeSend("L",[37-i,0,0,0])
                                await asyncio.sleep(.1)
                                await fmPacker.encodeSend("L",[i,0,0,0])
                                await asyncio.sleep(.1)
                                await fmPacker.encodeSend("L",[37-i,0,0,0])
                                await asyncio.sleep(.1)
                    else:
                        await OLED_Print(fmPacker,"Waiting for controller") 


async def eventLoop(state):
    await gather(
        readSerialFromNUB(state),
        serve(handler, "0.0.0.0", 1997)
    )
    # asyncio.get_event_loop().run_until_complete(start_server)
    # asyncio.get_event_loop().run_forever()

   



def openSerial(ser_obj):
    ser = AioSerial(port=ser_obj,baudrate=115200)
    return ser


# --------------------------------------STARTUP--------------------------------------



# startup

print("program starting")
serialConnected = False
try:
    serial_port = openSerial("/dev/serial0")
    serialConnected = True
    print("Connected to serial port")
except:
    print("FAILED TO CONNECT TO SERIAL")

fmPacker = PacketSender(serial_port)


state["LCDTimer"] = time.time()

# start the async event loop
run(eventLoop(state))