#!/usr/bin/env python

"""
This application is a special example of building a custom data structure
to be written to a proprietary property of a proprietary object.  Unlike the
other 'write property' sample applications, this one make no attempt to
translate keywords into object types and property identifiers, it only takes
integers.

BACnet settings object BCP etCH/DCU
Exemple: write 192.168.5.50 OR read 50750:0
***attention*** Foreign
"""

import sys

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob
from bacpypes.consolelogging import ConfigArgumentParser
from bacpypes.consolecmd import ConsoleCmd

from bacpypes.core import run, enable_sleeping
from bacpypes.iocb import IOCB

from bacpypes.pdu import Address
from bacpypes.app import BIPSimpleApplication
from bacpypes.app import BIPForeignApplication
from bacpypes.service.device import LocalDeviceObject

from bacpypes.primitivedata import TagList, OpeningTag, ClosingTag, ContextTag
from bacpypes.constructeddata import Any
from bacpypes.apdu import WritePropertyRequest, SimpleAckPDU

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
this_application = None

#
#   WriteSomethingConsoleCmd
#

@bacpypes_debugging
class WriteSomethingConsoleCmd(ConsoleCmd):

    def do_write(self, args):
        """write <addr> <type> <inst> <prop> [ <indx> ]"""
        args = args.split()
        if _debug: WriteSomethingConsoleCmd._debug("do_write %r", args)

        try:
            addr = args[0]

            obj_type = 162 #int(obj_type)
            obj_inst = 1 #int(obj_inst)
            prop_id = 1034 #int(prop_id)
            idx = 2

            # build a request
            request = WritePropertyRequest(
                objectIdentifier=(obj_type, obj_inst),
                propertyIdentifier=prop_id,
                )
            request.pduDestination = Address(addr)

            if len(args) >= 5: 
                request.propertyArrayIndex = 2 #int(args[4])
                
            request.propertyArrayIndex = idx    

            if len(args) == 6:
                #convert ip to byte array and then to hex string
                proxy = bytearray(args[5])
                proxy_hex = str(proxy).encode('hex')

            # build a custom data structure... BACnet settings BCP object IP BBMD Foreign port eTCH 3.40
            # Context #0 inside Opening tag #9 is the IP Type 00=Regular, 01=Foreign, 02=BBMD
            # Context #2 inside Opening tag #9 is the Foreign IP in hex
            # Context #4 inside Opening tag #9 is the Proxy IP in hex
            tag_list = TagList([
                OpeningTag(0),
                ContextTag(0, xtob('19')),
                ContextTag(1, xtob('01')),
                ClosingTag(0),
                ContextTag(1, xtob('01')),
                ContextTag(2, xtob('00')),
                ContextTag(3, xtob('9c40')),
                ContextTag(4, xtob('00')),
                OpeningTag(5),
                ContextTag(0, xtob('00')),
                ContextTag(1, xtob('00')), 
                ClosingTag(5),
                ContextTag(6, xtob('00')),
                ContextTag(7, xtob('00')),
                OpeningTag(8),
                ContextTag(0, xtob('00')),
                ContextTag(1, xtob('00')), 
                ContextTag(2, xtob('00')),
                ContextTag(3, xtob('00')),
                ContextTag(4, xtob('00')), 
                ContextTag(5, xtob('00')),
                ContextTag(6, xtob('00')),
                ContextTag(7, xtob('00')),
                ContextTag(8, xtob('ffffffff')), 
                ClosingTag(8),               
                OpeningTag(9),
                ContextTag(0, xtob('02')),
                ContextTag(1, xtob('bac0')), 
                ContextTag(2, xtob('00')),
                ContextTag(3, xtob('3c')),
                ContextTag(4, xtob('480c600c')), 
                ContextTag(5, xtob('00')),
                ContextTag(6, xtob('ffffffff')), 
                ClosingTag(9), 
                ContextTag(10, xtob('00')),
                ContextTag(11, xtob('00')),
                ContextTag(12, xtob('00')),
                ContextTag(13, xtob('00000000'))                
                ])
            if _debug: WriteSomethingConsoleCmd._debug("    - tag_list: %r", tag_list)

            # stuff the tag list into an Any
            request.propertyValue = Any()
            request.propertyValue.decode(tag_list)

            if _debug: WriteSomethingConsoleCmd._debug("    - request: %r", request)

            # make an IOCB
            iocb = IOCB(request)
            if _debug: WriteSomethingConsoleCmd._debug("    - iocb: %r", iocb)

            # give it to the application
            this_application.request_io(iocb)

            # wait for it to complete
            iocb.wait()

            # do something for success
            if iocb.ioResponse:
                # should be an ack
                if not isinstance(iocb.ioResponse, SimpleAckPDU):
                    if _debug: WriteSomethingConsoleCmd._debug("    - not an ack")
                    return

                sys.stdout.write("ack\n")

            # do something for error/reject/abort
            if iocb.ioError:
                sys.stdout.write(str(iocb.ioError) + '\n')

        except Exception as error:
            WriteSomethingConsoleCmd._exception("exception: %r", error)


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
    #this_application = BIPSimpleApplication(this_device, args.ini.address)
    this_application = BIPForeignApplication(
        this_device, args.ini.address,
        Address(args.ini.foreignbbmd),
        int(args.ini.foreignttl),
        )    
    if _debug: _log.debug("    - this_application: %r", this_application)

    # get the services supported
    services_supported = this_application.get_services_supported()
    if _debug: _log.debug("    - services_supported: %r", services_supported)

    # let the device object know
    this_device.protocolServicesSupported = services_supported.value

    # make a console
    this_console = WriteSomethingConsoleCmd()
    if _debug: _log.debug("    - this_console: %r", this_console)

    # enable sleeping will help with threads
    enable_sleeping()

    _log.debug("running")

    run()

    _log.debug("fini")

if __name__ == "__main__":
    main()