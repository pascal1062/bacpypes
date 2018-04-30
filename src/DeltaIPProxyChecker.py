#!/usr/bin/env python

"""
This application 
"""

import sys

from collections import deque 

from json import load
from urllib2 import urlopen

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob
from bacpypes.consolelogging import ConfigArgumentParser
#from bacpypes.consolecmd import ConsoleCmd

from bacpypes.core import run, enable_sleeping, stop, deferred
from bacpypes.iocb import IOCB

from bacpypes.pdu import Address, GlobalBroadcast
from bacpypes.object import get_datatype
from bacpypes.apdu import WhoIsRequest, IAmRequest, ReadPropertyRequest, WritePropertyRequest, SimpleAckPDU
from bacpypes.basetypes import ServicesSupported
from bacpypes.errors import DecodingError
from bacpypes.primitivedata import Unsigned, TagList, OpeningTag, ClosingTag, ContextTag
from bacpypes.constructeddata import Array, Any

from bacpypes.app import BIPSimpleApplication
from bacpypes.service.device import LocalDeviceObject

from decode import bcp, net, contextTagsToWrite  

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
this_device = None
this_application = None
#device = 75000
device = 1200

# point list, set according to your device
point_list = [
    ['192.168.1.50', 'device', 100, 'modelName'],
    ['192.168.1.50', 'device', 100, 'applicationSoftwareVersion'],
    ]


#
#   WhoIsIAmApplication
#

@bacpypes_debugging
class WhoIsIAmApplication(BIPSimpleApplication):

    def __init__(self, *args):
        if _debug: WhoIsIAmApplication._debug("__init__ %r", args)
        BIPSimpleApplication.__init__(self, *args)

        # turn the point list into a queue
        self.point_queue = deque(point_list)
        
        # make a list of the response values
        self.response_values = []

        # keep track of requests to line up responses
        self._request = None
        
        # list of the response values from "bacnet settings" (NET, BCP)
        self.response_bacset = []
        
        # variable for Proxy IP
        self.proxyIP = "0.0.0.0"

    def request(self, apdu):
        if _debug: WhoIsIAmApplication._debug("request %r", apdu)

        # save a copy of the request
        self._request = apdu

        # forward it along
        BIPSimpleApplication.request(self, apdu)

    def confirmation(self, apdu):
        if _debug: WhoIsIAmApplication._debug("confirmation %r", apdu)

        # forward it along
        BIPSimpleApplication.confirmation(self, apdu)

    def indication(self, apdu):
        if _debug: WhoIsIAmApplication._debug("indication %r", apdu)

        if (isinstance(self._request, WhoIsRequest)) and (isinstance(apdu, IAmRequest)):
            device_type, device_instance = apdu.iAmDeviceIdentifier
            if device_type != 'device':
                raise DecodingError("invalid object type")

            if (self._request.deviceInstanceRangeLowLimit is not None) and \
                    (device_instance < self._request.deviceInstanceRangeLowLimit):
                pass
            elif (self._request.deviceInstanceRangeHighLimit is not None) and \
                    (device_instance > self._request.deviceInstanceRangeHighLimit):
                pass
            else:
                # Received I-am from target's Device instance
                dev_ObjID = apdu.iAmDeviceIdentifier
                dev_pdusource = apdu.pduSource
 
                point_list[0][0] = str(dev_pdusource)
                point_list[1][0] = str(dev_pdusource)
                point_list[0][2] = dev_ObjID[1]
                point_list[1][2] = dev_ObjID[1]

                #fire off request. read device properties model name and software version
                deferred(self.next_request)                
         
        # forward it along
        BIPSimpleApplication.indication(self, apdu)
        
    def next_request(self):
        if _debug: WhoIsIAmApplication._debug("next_request")

        # check to see if we're done
        if not self.point_queue:
            if _debug: WhoIsIAmApplication._debug("    - done")
            
            # dump out the results... ici caller fonction qui analyse quel type de panneau et ensuite faire read du IP Proxy..
            for request, response in zip(point_list, self.response_values):
                print(request, response)
            
            # Adjust depending on object type NET or BCP and also version dependent 3.33 or 3.40
            # Here is NET object DSC-xxxx 3.40 
            self.net_obj_id(278,1,1101,5) 

            return

        # get the next request
        addr, obj_type, obj_inst, prop_id = self.point_queue.popleft()

        # build a request
        request = ReadPropertyRequest(
            objectIdentifier=(obj_type, obj_inst),
            propertyIdentifier=prop_id,
            )
        request.pduDestination = Address(addr)
        if _debug: WhoIsIAmApplication._debug("    - request: %r", request)

        # make an IOCB
        iocb = IOCB(request)

        # set a callback for the response
        iocb.add_callback(self.complete_request)
        if _debug: WhoIsIAmApplication._debug("    - iocb: %r", iocb)

        # send the request
        this_application.request_io(iocb)
        
    def complete_request(self, iocb):
        if _debug: WhoIsIAmApplication._debug("complete_request %r", iocb)

        if iocb.ioResponse:
            apdu = iocb.ioResponse

            # find the datatype
            datatype = get_datatype(apdu.objectIdentifier[0], apdu.propertyIdentifier)
            if _debug: WhoIsIAmApplication._debug("    - datatype: %r", datatype)
            if not datatype:
                raise TypeError("unknown datatype")

            # special case for array parts, others are managed by cast_out
            if issubclass(datatype, Array) and (apdu.propertyArrayIndex is not None):
                if apdu.propertyArrayIndex == 0:
                    value = apdu.propertyValue.cast_out(Unsigned)
                else:
                    value = apdu.propertyValue.cast_out(datatype.subtype)
            else:
                value = apdu.propertyValue.cast_out(datatype)
            if _debug: WhoIsIAmApplication._debug("    - value: %r", value)

            # save the value
            self.response_values.append(value)

        if iocb.ioError:
            if _debug: WhoIsIAmApplication._debug("    - error: %r", iocb.ioError)
            self.response_values.append(iocb.ioError)

        # fire off another request
        deferred(self.next_request) 
     
    def net_obj_id(self,obj,inst,prop,idx):
        self.obj = obj
        self.inst = inst
        self.prop = prop
        self.idx = idx
        
        deferred(self.read_prop_vendor)

    def read_prop_vendor(self):
        #get bacnet source pdu from point_list array. point_list has been override by next_request method
        addr = point_list[0][0]

        obj_type = self.obj
        obj_inst = self.inst
        prop_id = self.prop
        
        # build a request
        request = ReadPropertyRequest(
            objectIdentifier=(obj_type, obj_inst),
            propertyIdentifier=int(prop_id),
            )
        request.pduDestination = Address(addr)
        
        request.propertyArrayIndex = self.idx
        #if _debug: ReadPropertyAnyConsoleCmd._debug("    - request: %r", request)
        
        # make an IOCB
        iocb = IOCB(request)

        #if _debug: ReadPropertyAnyConsoleCmd._debug("    - iocb: %r", iocb)
        
        # set a callback for the response
        iocb.add_callback(self.prop_vendor_ack)
        
        # give it to the application
        this_application.request_io(iocb)
        
    def prop_vendor_ack(self,iocb):
       
        # do something for success
        if iocb.ioResponse:
            apdu = iocb.ioResponse

        # decode results from bacnet_settings's read property 
        self.response_bacset = net.dcode(apdu) 
        
        # get actual proxy IP from Device
        actual_IP = self.response_bacset[1]
        
        # Check public IP
        public_IP = self.get_public_ip()
        print public_IP
        
        # check if IPs are real IPV4  
        # If both IPs are different, do a write property to the correct object
        if self.validate_ip(actual_IP) and self.validate_ip(public_IP):
            if actual_IP != public_IP:
                self.proxyIP = public_IP
                deferred(self.write_bac_set) 
                print actual_IP, public_IP
            else:
                print "IPs are the same"
                stop()
        else:
            print "IPs are not valid"
            stop()
                
        #deferred(self.write_bac_set) 
        
        # do something for error/reject/abort
        if iocb.ioError:
            sys.stdout.write(str(iocb.ioError) + '\n')

        
    def write_bac_set(self):
        
        addr = point_list[0][0]
        obj_type = self.obj
        obj_inst = self.inst
        prop_id = self.prop
        
        tags = self.response_bacset[0]
        proxy_ip = self.proxyIP
        print tags
        print proxy_ip

        try:

            # build a request
            request = WritePropertyRequest(
                objectIdentifier=(obj_type, obj_inst),
                propertyIdentifier=prop_id,
                )
            request.pduDestination = Address(addr)
            request.propertyArrayIndex = self.idx

            # build a custom datastructure... BACnet settings IP net or bcp
            tag_list = contextTagsToWrite.build_list(self.response_bacset,proxy_ip)
            
            #if _debug: WriteSomethingConsoleCmd._debug("    - tag_list: %r", tag_list)

            # stuff the tag list into an Any
            request.propertyValue = Any()
            request.propertyValue.decode(tag_list)

            #if _debug: WriteSomethingConsoleCmd._debug("    - request: %r", request)

            # make an IOCB
            iocb = IOCB(request)
            #if _debug: WriteSomethingConsoleCmd._debug("    - iocb: %r", iocb)
            
            # set a callback for the response
            iocb.add_callback(self.simple_ack)

            # give it to the application
            this_application.request_io(iocb)

        except Exception as error:
            #WriteSomethingConsoleCmd._exception("exception: %r", error)  
            print error 
            
    def simple_ack(self,iocb):
        if iocb.ioResponse:
            # should be an ack
            if not isinstance(iocb.ioResponse, SimpleAckPDU):
                #if _debug: WriteSomethingConsoleCmd._debug("    - not an ack")
                #return
                stop()

            sys.stdout.write("ack\n") 
            stop()
                
        # do something for error/reject/abort
        if iocb.ioError:
            sys.stdout.write(str(iocb.ioError) + '\n')
            stop() 
            
    def get_public_ip(self):
        my_ip = load(urlopen('http://jsonip.com'))['ip']
        return my_ip
 
    def validate_ip(self,s):
        a = s.split('.')
        if len(a) != 4:
            return False
        for x in a:
            if not x.isdigit():
                return False
            i = int(x)
            if i < 0 or i > 255:
                return False
            
        return True
    
    
#        
#   WhoIsIAmConsoleCmd
#

@bacpypes_debugging
class WhoIsIAmCmd():

    def do_whois(self, args):
        """whois [ <addr>] [ <lolimit> <hilimit> ]"""
        args = args.split()
        #if _debug: WhoIsIAmConsoleCmd._debug("do_whois %r", args)

        try:
            # build a request
            request = WhoIsRequest()
            if (len(args) == 1) or (len(args) == 3):
                request.pduDestination = Address(args[0])
                del args[0]
            else:
                request.pduDestination = GlobalBroadcast()

            if len(args) == 2:
                request.deviceInstanceRangeLowLimit = int(args[0])
                request.deviceInstanceRangeHighLimit = int(args[1])
            #if _debug: WhoIsIAmConsoleCmd._debug("    - request: %r", request)

            # make an IOCB
            iocb = IOCB(request)
            #if _debug: WhoIsIAmConsoleCmd._debug("    - iocb: %r", iocb)

            # give it to the application
            this_application.request_io(iocb)

        except Exception as err:
            WhoIsIAmCmd._exception("exception: %r", err)
            

#
#   main
#

def main():
    global this_device, this_application

    # parse the command line arguments
    args = ConfigArgumentParser(description=__doc__).parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # make a device object
    this_device = LocalDeviceObject(
        objectName=args.ini.objectname,
        objectIdentifier=int(args.ini.objectidentifier),
        maxApduLengthAccepted=int(args.ini.maxapdulengthaccepted),
        segmentationSupported=args.ini.segmentationsupported,
        vendorIdentifier=int(args.ini.vendoridentifier),
        )
    if _debug: _log.debug("    - this_device: %r", this_device)

    # build a bit string that knows about the bit names
    pss = ServicesSupported()
    pss['whoIs'] = 1
    pss['iAm'] = 1
    pss['readProperty'] = 1
    pss['writeProperty'] = 1

    # set the property value to be just the bits
    this_device.protocolServicesSupported = pss.value

    # make a simple application
    this_application = WhoIsIAmApplication(this_device, args.ini.address)
    if _debug: _log.debug("    - this_application: %r", this_application)

    # get the services supported
    services_supported = this_application.get_services_supported()
    if _debug: _log.debug("    - services_supported: %r", services_supported)

    # let the device object know
    this_device.protocolServicesSupported = services_supported.value

    # make a console
    #this_console = WhoIsIAmConsoleCmd().do_whois("1200 1200")
    this_console = WhoIsIAmCmd().do_whois(str(device)+" "+str(device))

    if _debug: _log.debug("    - this_console: %r", this_console)

    # enable sleeping will help with threads
    enable_sleeping()

    _log.debug("running")

    run()
     
    _log.debug("fini")


if __name__ == "__main__":
    main()
