import socket
from library_upnp import *
import sys
import requests
from xml.dom import minidom

def main():
    global urlBase
    udpsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # location = SSDP.GetLocation(udpsocket=udpsocket)
    # location = "http://192.168.1.170:55003/description.xml"
    location = "http://192.168.1.1:80/RootDevice.xml"
    print("XML Location:", location)
    request = HTTP.GET(location)
    xml = request.content
    status_code = request.status_code
    if status_code == 200 and "schemas-upnp-org" in request.text:
        xml = minidom.parseString(xml)  # returns minidom document
    else:
        print("(!)Description could not be identified")
        print("status code:", status_code)
        print(request.text)
        sys.exit()

    urlBase = SCPD.GetUrlBase(xml)
    if urlBase == None:
        urlBase = location
    services = SCPD.GetServices(xml)
    if services:
        for i in range(len(services)):
            print(i, services[i].ToString())
    else:
        print("Services NULL")
        sys.exit()
    selected = int(input("select a service: "))  # implement try except
    selectedservice = services[selected]
    actionNodesList = SCPD.GetActionNodesList(selectedservice)
    actionsObjList = list()
    if actionNodesList:
        for node in actionNodesList: #gets all the actions objects in a list
            action = Action.GetAction(node)
            actionsObjList.append(action) 
        for i in range(len(actionsObjList)): #displays them to the screen
            if actionsObjList[i].arguments:
                inArgs = list()
                for arg in actionsObjList[i].arguments:#.keys()| for loop iterates through keys of a dict
                    if arg.direction == "in":
                        inArgs.append(arg)
                print("[{0}] {1} ({2})".format(i, actionsObjList[i].name, len(inArgs)))
            else:
                print("[{0}] {1} (0)".format(i, actionsObjList[i].name))

        selected = int(input("select an action: "))
        action = actionsObjList[selected]
        for arg in actionsObjList[selected].arguments: #populates the in arguments
            if arg.direction == "in":
                value = input(arg.ToString() + ": ")
                actionsObjList[selected].arguments.update({arg:value})
                
        request = HTTP.POST(service=selectedservice, action=action, body="") # finish
        print(request.text)
    else:
        print("Actions NULL")

    # print("Server: ", server)
    # print("Recieved from: "from_addr[0])


if __name__ == "__main__":
    main()
