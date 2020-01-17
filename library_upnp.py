import requests
import socket
from xml.dom import minidom
import sys
import upnp_practice

def XMLGetNodeText(node):  # borrowed code
    """
    Return text contents of an XML Text Node.
    """
    text = []
    for childNode in node:
        if childNode.firstChild.nodeType == minidom.Text.TEXT_NODE:
            text.append(childNode.firstChild.data)
        #else
    return(''.join(text))

class Argument(object):
    def __init__(self, name, direction, relatedStateVariable):
        self.name = name
        self.direction = direction
        self.relatedStateVariable = relatedStateVariable
    
    def ToString(self):
        return "{0}, {1}, {2}".format(self.name,self.direction,self.relatedStateVariable)
    
    @staticmethod
    def GetArguments(argumentListNode):
        argumentList = list()
        for node in argumentListNode.childNodes:
            if node.nodeName == "argument":
                for subnode in node.childNodes:
                    if subnode.nodeName == "name":
                        name = subnode.firstChild.data
                    if subnode.nodeName == "direction":
                        direction = subnode.firstChild.data
                    if subnode.nodeName == "relatedStateVariable":
                        relatedStateVariable = subnode.firstChild.data
                argumentList.append(Argument(name,direction,relatedStateVariable))
        return argumentList

    def __init__(self, name, direction, relatedStateVariable):
        self.name = name
        self.direction = direction
        self.relatedStateVariable = relatedStateVariable

class Action(object):    
    def __init__(self,name, arguments):
        self.name = name
        argsdict = dict()
        if arguments:
            for arg in arguments:
                argsdict.update({arg : ""})
        self.arguments = argsdict
    def ToString(self):
        argumentStringList = list()
        if self.arguments:
            for i in self.arguments:
                argumentStringList.append(i.ToString())
        else:
            argumentStringList.append("[]")
        text = ""
        text+=("\n"+self.name)
        for argumentString in argumentStringList:
            text+=("\n\t"+argumentString)
        return text
    @staticmethod
    def GetAction(actionNode):
        """
        Returns an Action object from an action node
        """
        name = None
        arguments = None
        for node in actionNode.childNodes:
            if node.nodeName == "name":
                    name = node.firstChild.data
            if node.nodeName == "argumentList":
                arguments = Argument.GetArguments(node)
        action = Action(name,arguments)
        return action

class Service(object):
    def __init__(self, servicename, ctrlURL, scpdURL, parentDevice): #add actions as a property of services
        self.servicename = servicename
        self.ctrlURL = ctrlURL
        self.scpdURL = scpdURL
        self.parentDevice = parentDevice

    def ToString(self):
        return "{0}, {1}, {2}".format(self.servicename, self.ctrlURL, self.scpdURL)

class HTTP():

    global urlBase
    @staticmethod
    def POST(body="",service = Service,action = Action):
        body  ="<?xml version=\"1.0\"?><s:Envelopexmlns:s=\"http://schemas.xmlsoap.org/soap/envelope\"s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\"><s:Body><u:actionName xmlns:u={0}/></s:Body></s:Envelope>".format(service.parentDevice)
        
        soapaction = "{0}:{1}".format(service.parentDevice,action.name)
        headers = {'HOST':urlBase+service.ctrlURL,'CONTENT-LENGHT':str(len(bytes(body,"utf8"))),'CONTENT-TYPE':'text/xml; charset=\"utf-8\"','SOAPACTION':soapaction}
        r = requests.post(urlBase+service.ctrlURL,data=body,headers=headers)
        return r
    @staticmethod
    def GET(url):
        """
        Requests an specified HTTP URL address and returns the request object
        """
        url = url
        i = 0
        while i <= 3:
            try:
                print("Getting...")
                r = requests.get(url, timeout=10)
                print("Done")
                break
            except requests.Timeout:
                print("Request Timed Out")
            except  requests.ConnectionError as e:
                print("Connection Error\n",str(e))
            except Exception as e:
                print("UNHANDLED EXCEPTION!!\n",e)
                sys.exit()
            if i == 2:
                print("byebye")
                sys.exit()  #handle this error better
            else:
                print("Retrying")
                i += 1
                continue
        return r

class SSDP():  # Simple Service Discovery Protocol
    @staticmethod
    def __Search(socket, ST="upnp:rootdevice"): #double underscore for declaring private method
        """
        Sends a HTTP M-SEARCH broadcast message, SSDP protocol
        """
        broadcast_host = "239.255.255.250"
        port = 1900
        data = "M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\nMAN: \"ssdp:discover\"\r\nMX: 120\r\nST: {0}\r\n".format(ST)
        try:
            print("Sending...")
            socket.sendto(bytes(data, "utf8"), (broadcast_host, port))
            print("Done")
            return 0 #return with no errors
        except OSError as e:
            print("(!)", str(e))
            return 1
        except Exception as e:
            print("UNHANDLED EXCEPTION\n\n",e)

    @staticmethod
    def GetLocation(udpsocket):
        """
        Returns the location of a single upnp device that responds to the crafted upnp search request
        """
        seconds = 120
        udpsocket.settimeout(seconds)
        print("timeout set to",seconds)
        response = b""
        i = 0
        while i < 3:
            if SSDP.__Search(socket=udpsocket) == 1:
                prompt = input("Search packet could not be sent, continue? [BLANK YES|ANY NO]")
                if prompt == "":
                    seconds = 2
                    pass
                else:
                    sys.exit()
            try:
                print("Recieving...")# assuming only one response, threading in the future to get more responses
                response = udpsocket.recvfrom(1024)
                break
            except socket.timeout: #make sure to call .timeout from the package name and not a variable with the same name. Do not name variables the same as packages.
                print("Connection Timeout Error")
            if i == 2:
                print("byebye")
                sys.exit()
            else:
                print("Retrying")
                i += 1

        response = response[0].decode()
        location = ""
        for line in response.split("\n"):
            if "location:" in line.lower():
                location = line[10:] #strip the word "Location" by selecting the characters after it
                location = location.strip()
                return location

class SCPD():  # Service Control Point Definition
    @staticmethod
    def GetUrlBase(xml):
        global urlBase
        urlBase = xml.getElementsByTagName('URLBase')
        if urlBase:
            urlBase = XMLGetNodeText(urlBase)
            return urlBase
        else:
            return None

    @staticmethod
    def GetServices(xml):
        """
        Returns a List of Service objects from a services XML
        """
        servicesNodes = xml.getElementsByTagName("service")
        services = list()
        if servicesNodes:
            for node in servicesNodes:
                name = node.getElementsByTagName("serviceId")
                name = XMLGetNodeText(name)
                ctrlURL = node.getElementsByTagName("controlURL")
                ctrlURL = XMLGetNodeText(ctrlURL)
                scpdURL = node.getElementsByTagName("SCPDURL")
                scpdURL = XMLGetNodeText(scpdURL)
                parentDevice = node.parentNode.parentNode.getElementsByTagName("deviceType")[0].firstChild.data
                service = Service(name, ctrlURL, scpdURL,parentDevice)
                services.append(service)
            return services
        else:
            return None
    @staticmethod
    def GetActionNodesList(services):
        """
        Returns a NodeList of action XML node objects from an scpd URL's xml minidom element
        """
        global urlBase
        actionNodesList = minidom.NodeList()
        url = urlBase + services.scpdURL
        request = HTTP.GET(url)
        xml = request.content
        status_code = request.status_code
        if status_code == 200:
            xml = minidom.parseString(xml)
            nodes = xml.childNodes[0].childNodes
            for node in nodes:
                if node.nodeName == "actionList":
                    for subnode in node.childNodes:
                        if subnode.nodeName == "action":
                            actionNodesList.append(subnode)
            return actionNodesList
        else:
            return None
