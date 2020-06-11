import serial
import time
from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM
import threading
import sys
import re
from gpiozero import CPUTemperature


    
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

    def sendPacketOverSerial(self,packet):
        # print(packet)
        packet = packet + "\n"
        self.serial.write(packet.encode())

    def calcualuteCheckSum(self,message):
        return sum(bytearray(message, encoding="ascii"))

    def findFlag(self,packet):
        try:
            return (packet.split("@"))[1].split("@")[0]
        except Exception as e:
            return ""

    def encodeSend(self,flag,inData):
        packet = self.encodePacket(flag,inData)
        self.sendPacketOverSerial(packet)

    def encodePacket(self,flag,inData):
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

    def decodePacket(self,flag, packet):
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

def OLED_Print(text):
    fmPacker.encodeSend("LCD",[text])
def OLED_Clear():
    fmPacker.encodeSend("LCD_CLEAR",["0"])
def Set_LED(state):
    fmPacker.encodeSend("LED",[state])


# global variables
cpu = CPUTemperature()
serial_port = None
socket_port = None

#  start the program
print("program starting")
serialConnected = False
try:
    serial_port = serial.Serial("/dev/serial0",115200)
    serialConnected = True
    print("Connected to serial port")
except:
    print("FAILED TO CONNECT TO SERIAL")

fmPacker = PacketSender(serial_port)


# fmPacker.encodeSend("LCD_CLEAR",["0"])
# fmPacker.encodeSend("LCD",["hello"])
# fmPacker.encodeSend("LCD",["frank"])
# fmPacker.encodeSend("LCD",["nice"])
# fmPacker.encodeSend("LCD",["screen"])
fmPacker.encodeSend("LED_MODE",["3"])

for i in range(38):
    fmPacker.encodeSend("L",[i,35,70,20])
    time.sleep(.05)

time.sleep(2)
fmPacker.encodeSend("LED_BRIGHTNESS",["20"])

time.sleep(1)
fmPacker.encodeSend("SERVO",[90,90,90,90])
time.sleep(2)
# (r_pit,l_pit,l_yaw, r_yaw)
# (more up, more down, more left, more left )

fmPacker.encodeSend("MOTOR",[-120,-120]) # forward
time.sleep(1)
fmPacker.encodeSend("MOTOR",[0,0])
# "MOTOR",[right motor,left motor] 
# "MOTOR",[+ backwards,+ backwards] 





while True:
    myIP = getSystemIP()
    Set_LED(1)
    time.sleep(.5)
    OLED_Clear()
    OLED_Print(myIP)
    OLED_Print("CPU: "+str(round(cpu.temperature))+"*C" )
    



#     threading.Thread(target=readFromSocketServer,args=(serial_port,192.168.1.200,1963)).start()
#     # threading.Thread(target=readFromSerial,args=(serial_port)).start()



# serial loop
while True:
    # When we get a new line, parse it and fill out the appropriate data structures
    line = fmPacker.serial.readline()
    # decode the packet
    try:
        packet = line.decode("utf-8")
    except UnicodeDecodeError:
        print("Could not decode incoming arduino packet")
    #  determine the flag
    flag = fmPacker.findFlag(packet)
    if flag is not "":
        # get the data out of the packet
        print(flag)
        packet_data = fmPacker.decodePacket(flag, packet)
        if flag == "DATA":
            print(packet_data)



