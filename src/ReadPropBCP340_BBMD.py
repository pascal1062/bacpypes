#!/usr/bin/env python

"""
This application presents a 'console' prompt to the user asking for read commands
which create ReadPropertyRequest PDUs, waits for the response, then decodes the
value if it is application encoded.  This is useful for reading the values
of propietary properties when the datatype isn't known.

Lecture du BACnet settings object BCP eTCH et DCU
Dans la console faire: read 192.168.5.50 OR read 50750:0

"""

import sys

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser
from bacpypes.consolecmd import ConsoleCmd

from bacpypes.core import run, enable_sleeping
from bacpypes.iocb import IOCB

from bacpypes.pdu import Address
from bacpypes.object import get_datatype, get_object_class

from bacpypes.apdu import ReadPropertyRequest, Error, AbortPDU, ReadPropertyACK
from bacpypes.primitivedata import Tag

from bacpypes.app import BIPSimpleApplication
from bacpypes.service.device import LocalDeviceObject


# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
this_application = None

#
#   ReadPropertyAnyConsoleCmd
#

@bacpypes_debugging
class ReadPropertyAnyConsoleCmd(ConsoleCmd):

    def do_read(self, args):
        """read <addr>"""
        args = args.split()
        if _debug: ReadPropertyAnyConsoleCmd._debug("do_read %r", args)

        try:
            addr = args[0]

            obj_type = 162
            obj_inst = 1
            prop_id = 1034
            idx = 2

            # build a request
            request = ReadPropertyRequest(
                objectIdentifier=(obj_type, obj_inst),
                propertyIdentifier=int(prop_id),
                )
            request.pduDestination = Address(addr)

            if len(args) == 5:
                request.propertyArrayIndex = 2
            if _debug: ReadPropertyAnyConsoleCmd._debug("    - request: %r", request)
            
            request.propertyArrayIndex = idx

            # make an IOCB
            iocb = IOCB(request)

            if _debug: ReadPropertyAnyConsoleCmd._debug("    - iocb: %r", iocb)

            # give it to the application
            this_application.request_io(iocb)

            # wait for it to complete
            iocb.wait()

            # do something for success
            if iocb.ioResponse:
                apdu = iocb.ioResponse
                
                temp = ""
                opening_tag_0 = ""    
                context_tag_1_2 = ""  
                IP_NetNumber = 0 
                context_tag_4 = ""  
                opening_tag_5 = ""
                context_tag_6_7 = ""
                opening_tag_8 = ""
                IP_type = ""    
                IP_Port = 0 
                Foreign_ttl = 0  
                Proxy_IP = "0.0.0.0"                                                           
                Foreign_IP = "0.0.0.0"  
                context_tag_5_6 = ""    
                context_tag_10_13 = ""

                #get tag type
                value_tag = apdu.propertyValue.tagList.Peek()

                #opening tag #0
                if value_tag.tagClass == Tag.openingTagClass:

                    value_tag = apdu.propertyValue.tagList.Pop()
                    value_tag = apdu.propertyValue.tagList.Peek()	

                    for i in range(0,2):
                        if (i >= 0) and (i <= 1):
                            opening_tag_0 = opening_tag_0 + str(value_tag.tagData).encode('hex')	

                        value_tag = apdu.propertyValue.tagList.Pop()
                        value_tag = apdu.propertyValue.tagList.Peek()
                        if (value_tag.tagClass == Tag.closingTagClass): break

                    sys.stdout.write("opening_tag_0: "+str(opening_tag_0)+"\n")

                else:
                    pass

                #Go forward in tagList
                value_tag = apdu.propertyValue.tagList.Pop()
                value_tag = apdu.propertyValue.tagList.Peek()                
                
                #context tag #1,2,3,4. Get Net Number
                if value_tag.tagClass == Tag.contextTagClass:

                    for i in range(1,5):
                        if (i >= 1) and (i <= 2):
                            context_tag_1_2 = context_tag_1_2 + str(value_tag.tagData).encode('hex') 
                        elif (i == 3):
                            IP_NetNumber = int(str(value_tag.tagData).encode('hex'),16)  
                        elif (i == 4):
                            context_tag_4 = str(value_tag.tagData).encode('hex')                                                         

                        value_tag = apdu.propertyValue.tagList.Pop()
                        value_tag = apdu.propertyValue.tagList.Peek()
                        if (value_tag.tagClass == Tag.openingTagClass): break

                    sys.stdout.write("context_tag_1_2: "+str(context_tag_1_2)+"\n")
                    sys.stdout.write("IP_NetNumber: "+str(IP_NetNumber)+"\n")
                    sys.stdout.write("context_tag_4: "+str(context_tag_4)+"\n")                    

                else:
                    pass                

                #get next tag type
                value_tag = apdu.propertyValue.tagList.Peek()

                #opening tag #5
                if value_tag.tagClass == Tag.openingTagClass:

                    value_tag = apdu.propertyValue.tagList.Pop()
                    value_tag = apdu.propertyValue.tagList.Peek()    

                    for i in range(0,2):
                        if (i >= 0) and (i <= 1):
                            opening_tag_5 = opening_tag_5 + str(value_tag.tagData).encode('hex')    

                        value_tag = apdu.propertyValue.tagList.Pop()
                        value_tag = apdu.propertyValue.tagList.Peek()
                        if (value_tag.tagClass == Tag.closingTagClass): break

                    sys.stdout.write("opening_tag_5: "+str(opening_tag_5)+"\n")

                else:
                    pass

                #Go forward in tagList
                value_tag = apdu.propertyValue.tagList.Pop()
                value_tag = apdu.propertyValue.tagList.Peek()                
              
                #context tag #6,7 Get Net Number
                if value_tag.tagClass == Tag.contextTagClass:

                    for i in range(6,8):
                        if (i >= 6) and (i <= 7):
                            context_tag_6_7 = context_tag_6_7 + str(value_tag.tagData).encode('hex') 
 
                        value_tag = apdu.propertyValue.tagList.Pop()
                        value_tag = apdu.propertyValue.tagList.Peek()
                        if (value_tag.tagClass == Tag.openingTagClass): break

                    sys.stdout.write("context_tag_6_7: "+str(context_tag_6_7)+"\n")

                else:
                    pass    

                #get next tag type
                value_tag = apdu.propertyValue.tagList.Peek()

                #opening tag #8
                if value_tag.tagClass == Tag.openingTagClass:

                    value_tag = apdu.propertyValue.tagList.Pop()
                    value_tag = apdu.propertyValue.tagList.Peek()    

                    for i in range(0,9):
                        if (i >= 0) and (i <= 8):
                            opening_tag_8 = opening_tag_8 + str(value_tag.tagData).encode('hex')    

                        value_tag = apdu.propertyValue.tagList.Pop()
                        value_tag = apdu.propertyValue.tagList.Peek()
                        if (value_tag.tagClass == Tag.closingTagClass): break

                    sys.stdout.write("opening_tag_8: "+str(opening_tag_8)+"\n")

                else:
                    pass

                #Go forward in tagList
                value_tag = apdu.propertyValue.tagList.Pop()
                value_tag = apdu.propertyValue.tagList.Peek()                
              
                #opening tag #9. Get Device Type, IP port,  Proxy addr and Foreign addr
                if value_tag.tagClass == Tag.openingTagClass:
                    
                    value_tag = apdu.propertyValue.tagList.Pop()
                    value_tag = apdu.propertyValue.tagList.Peek() 

                    for i in range(0,7):
                        if (i == 0):  
                            IP_type = str(value_tag.tagData).encode('hex') 
                        elif (i == 1): 
                            IP_Port = int(str(value_tag.tagData).encode('hex'),16) 
                        elif (i == 2): 
                            temp = bytearray.fromhex(str(value_tag.tagData).encode('hex'))
                            if len(temp) == 4: Foreign_IP = str(temp[0])+"."+str(temp[1])+"."+str(temp[2])+"."+str(temp[3]) 
                        elif (i == 3): 
                            Foreign_ttl = int(str(value_tag.tagData).encode('hex'),16)
                        elif (i == 4): 
                            temp = bytearray.fromhex(str(value_tag.tagData).encode('hex'))
                            if len(temp) == 4: Proxy_IP = str(temp[0])+"."+str(temp[1])+"."+str(temp[2])+"."+str(temp[3])
                        if (i >= 5) and (i <= 6):   
                            context_tag_5_6 = context_tag_5_6 + str(value_tag.tagData).encode('hex')                             
                             
                        value_tag = apdu.propertyValue.tagList.Pop()
                        value_tag = apdu.propertyValue.tagList.Peek()
                        if (value_tag.tagClass == Tag.closingTagClass): break

                    sys.stdout.write("Bacnet IP Type (00=Regular 01=Foreign 02=BBMD): "+str(IP_type)+"\n")
                    sys.stdout.write("BACnet IP Port: "+str(IP_Port)+"\n")
                    sys.stdout.write("Bacnet IP Foreign Address: "+str(Foreign_IP)+"\n")
                    sys.stdout.write("Bacnet IP Foreign time to live: "+str(Foreign_ttl)+"\n")
                    sys.stdout.write("Bacnet IP Proxy Address: "+str(Proxy_IP)+"\n")
                    sys.stdout.write("context_tag_5_6: "+str(context_tag_5_6)+"\n")
                    
                else:
                    pass   

                #Go forward in tagList
                value_tag = apdu.propertyValue.tagList.Pop()
                value_tag = apdu.propertyValue.tagList.Peek()                
              
                #context tag #10,11,12,13
                if value_tag.tagClass == Tag.contextTagClass:

                    for i in range(10,14):
                        if (i >= 10) and (i <= 13):
                            context_tag_10_13 = context_tag_10_13 + str(value_tag.tagData).encode('hex') 
 
                        value_tag = apdu.propertyValue.tagList.Pop()
                        value_tag = apdu.propertyValue.tagList.Peek()
                        if (i == 14): break

                    sys.stdout.write("context_tag_10_13: "+str(context_tag_10_13)+"\n")

                else:
                    pass  
                
                sys.stdout.flush()

            # do something for error/reject/abort
            if iocb.ioError:
                sys.stdout.write(str(iocb.ioError) + '\n')

        except Exception as error:
            ReadPropertyAnyConsoleCmd._exception("exception: %r", error)

#
#   __main__
#

def main():
    global this_application

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

    # make a simple application
    this_application = BIPSimpleApplication(this_device, args.ini.address)
    if _debug: _log.debug("    - this_application: %r", this_application)

    # get the services supported
    services_supported = this_application.get_services_supported()
    if _debug: _log.debug("    - services_supported: %r", services_supported)

    # let the device object know
    this_device.protocolServicesSupported = services_supported.value

    # make a console
    this_console = ReadPropertyAnyConsoleCmd()
    if _debug: _log.debug("    - this_console: %r", this_console)

    # enable sleeping will help with threads
    enable_sleeping()

    _log.debug("running")

    run()

    _log.debug("fini")

if __name__ == "__main__":
    main()
