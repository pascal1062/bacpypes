#!/usr/bin/env python

"""
This application is a special example of building a custom data structure
to be written to a proprietary property of a proprietary object.  Unlike the
other 'write property' sample applications, this one make no attempt to
translate keywords into object types and property identifiers, it only takes
integers.

Exemple: write 192.168.5.50 278 1 1101 5 145.70.22.234

"""

import sys

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob
from bacpypes.consolelogging import ConfigArgumentParser
from bacpypes.consolecmd import ConsoleCmd

from bacpypes.core import run, enable_sleeping
from bacpypes.iocb import IOCB

from bacpypes.pdu import Address
from bacpypes.app import BIPSimpleApplication
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
            addr, obj_type, obj_inst, prop_id = args[:4]

            obj_type = int(obj_type)
            obj_inst = int(obj_inst)
            prop_id = int(prop_id)

            # build a request
            request = WritePropertyRequest(
                objectIdentifier=(obj_type, obj_inst),
                propertyIdentifier=prop_id,
                )
            request.pduDestination = Address(addr)

            if len(args) >= 5: 
                request.propertyArrayIndex = int(args[4])

            if len(args) == 6:
				#convert ip to byte array and then to hex string
				proxy = bytearray(args[5])
				proxy_hex = str(proxy).encode('hex')

            # build a custom datastructure... BACnet settings IP BBMD Foreign port DSC 3.40
            tag_list = TagList([
                OpeningTag(1),
                ContextTag(0, xtob('9ca4')),
                ContextTag(1, xtob('02')),
                ContextTag(2, xtob('02')),
                ContextTag(3, xtob('003030302e3030302e3030302e303030')),
                ContextTag(4, xtob('3c')),
                ContextTag(5, xtob("00"+ proxy_hex)),
                ContextTag(6, xtob('00')), 
                ContextTag(7, xtob('00')),
                ContextTag(8, xtob('00')),
                ContextTag(9, xtob('bac0')),
                ContextTag(10, xtob('00')), 
                ContextTag(11, xtob('00')),
                ContextTag(12, xtob('00')),
                ContextTag(13, xtob('ffffffff')), 
                ContextTag(14, xtob('00')),
                ContextTag(15, xtob('00')),  
                ContextTag(16, xtob('00')),
                ContextTag(17, xtob('00')), 
                ClosingTag(1)
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
    this_application = BIPSimpleApplication(this_device, args.ini.address)
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
