import socket
from library_upnp import *
import sys
import requests
from xml.dom import minidom
from xml.etree import ElementTree as ET

def main():
    global urlBase
    #udpsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #location = SSDP.GetLocation(udpsocket=udpsocket)
    #location = "http://192.168.1.170:55003/description.xml"
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

    servicesList = SCPD.GetServices(xml)
    if servicesList:
        selectedService = SelectService(servicesList)
    else:
        print("Services NULL")
        sys.exit()

    selectedAction = SelectAction(selectedService) 
    for arg in selectedAction.inArgs:  # populates the in arguments 
        value=input(arg.ToString() + ": ") #create method and implement argument types
        selectedAction.arguments.update({arg: value})

        url=urlBase + selectedService.ctrlURL
        soapaction = "\"{0}#{1}\"".format(selectedService.seviceType,selectedAction.name)
        body = GenXMLbody(selectedService,selectedAction)
        #body = dom.toxml()
        headers={'HOST': urlBase, 'CONTENT-TYPE': 'text/xml; charset=\"utf-8\"',"CONNECTION":"close", 'SOAPACTION': soapaction}

        s = requests.Session()
        s.headers = headers
        s.verify = False #without this we get a connection reset error
        r =s.post(url, data=body)
        #print(dom.toprettyxml())
        print(r.text)
    else:
        print("Actions NULL")

    # print("Server: ", server)
    # print("Recieved from: "from_addr[0])


if __name__ == "__main__":
    main()
