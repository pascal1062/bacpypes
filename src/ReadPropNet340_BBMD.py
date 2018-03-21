#!/usr/bin/env python

"""
This application presents a 'console' prompt to the user asking for read commands
which create ReadPropertyRequest PDUs, waits for the response, then decodes the
value if it is application encoded.  This is useful for reading the values
of propietary properties when the datatype isn't known.

Dans la console faire: read 192.168.5.50 278 1 1101 5  *** Attention index 5 pour un DSC ***
Dans la console faire: read 192.168.5.50 278 1 1101 6  *** Attention index 6 pour un DSM-RTR ou eBMGR *** 	

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
        """read <addr> <type> <inst> <prop> [ <indx> ]"""
        args = args.split()
        if _debug: ReadPropertyAnyConsoleCmd._debug("do_read %r", args)

        try:
            addr, obj_type, obj_inst, prop_id = args[:4]

            if obj_type.isdigit():
                obj_type = int(obj_type)
            elif not get_object_class(obj_type):
                raise ValueError("unknown object type")

            obj_inst = int(obj_inst)

            # build a request
			# Pascal: modifier propertyIdentifier=int(prop_id) ....j'ai ajouter le int(  )
            request = ReadPropertyRequest(
                objectIdentifier=(obj_type, obj_inst),
                propertyIdentifier=int(prop_id),
                )
            request.pduDestination = Address(addr)

            if len(args) == 5:
                request.propertyArrayIndex = int(args[4])
            if _debug: ReadPropertyAnyConsoleCmd._debug("    - request: %r", request)

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

				#get tag length
                value_tag = apdu.propertyValue.tagList.Peek()
				
				#context tag
                if value_tag.tagClass == Tag.openingTagClass:
					l = apdu.propertyValue.tagList.__len__()
					IP_NetNumber = 0 
					context_tag_2 = 0					
					IP_type = ""  			
					Foreign_IP = ""  	
					Foreign_ttl = 0  	
					Proxy_IP = ""  
					context_tag_6_7_8 = ""
					IP_Port = 0  
					context_tag_10_11_12 = ""
					context_tag_13 = "" 
					context_tag_14_17 = "" 

 					value_tag = apdu.propertyValue.tagList.Pop()
					value_tag = apdu.propertyValue.tagList.Peek()	

					for i in range(1,l-1):
						if i == 1:
							IP_NetNumber = int(str(value_tag.tagData).encode('hex'),16)			
						elif (i == 2):
							context_tag_2 = str(value_tag.tagData).encode('hex')
						elif (i <= 3):
							IP_type = str(value_tag.tagData).encode('hex')
						elif (i == 4):
							Foreign_IP = value_tag.tagData
						elif (i == 5):
							Foreign_ttl = int(str(value_tag.tagData).encode('hex'),16)
						elif (i == 6):
							Proxy_IP = value_tag.tagData
						elif (i >= 7) and (i <= 9):
							context_tag_6_7_8 = context_tag_6_7_8 + str(value_tag.tagData).encode('hex')
						elif (i == 10): 	
							IP_Port = int(str(value_tag.tagData).encode('hex'),16)
						elif (i >= 11) and (i <= 13):
							context_tag_10_11_12 = context_tag_10_11_12 + str(value_tag.tagData).encode('hex')
						elif (i == 14):					
							context_tag_13 = str(value_tag.tagData).encode('hex')
						elif (i >= 15) and (i <= 18):
							context_tag_14_17 = context_tag_14_17 + str(value_tag.tagData).encode('hex') 

						value_tag = apdu.propertyValue.tagList.Pop()
						value_tag = apdu.propertyValue.tagList.Peek()

					sys.stdout.write("Bacnet IP Net Number: "+str(IP_NetNumber)+"\n")
					sys.stdout.write("context_tag_2: "+str(context_tag_2)+"\n")
					sys.stdout.write("Bacnet IP Type (00=Regular 01=Foreign 02=BBMD): "+str(IP_type)+"\n")
					sys.stdout.write("Bacnet IP Foreign Address: "+str(Foreign_IP)+"\n")
					sys.stdout.write("Bacnet IP Foreign time to live: "+str(Foreign_ttl)+"\n")
					sys.stdout.write("Bacnet IP Proxy Address: "+str(Proxy_IP)+"\n")
					sys.stdout.write("BACnet IP Port: "+str(IP_Port)+"\n")
					sys.stdout.write("context_tag_6_7_8: "+str(context_tag_6_7_8)+"\n")
					sys.stdout.write("context_tag_10_11_12: "+str(context_tag_10_11_12)+"\n")
					sys.stdout.write("context_tag_13: "+str(context_tag_13)+"\n")
					sys.stdout.write("context_tag_14_17: "+str(context_tag_14_17)+"\n")
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
