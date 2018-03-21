#!/usr/bin/env python

"""
This application is an example of command to reinitialize a device. 
There are many types of reinitialized state of device like coldstart,
warmstart, etc... look at pdu.py file.
"""

import sys

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser
from bacpypes.consolecmd import ConsoleCmd

from bacpypes.core import run, enable_sleeping
from bacpypes.iocb import IOCB

from bacpypes.pdu import Address
from bacpypes.app import BIPSimpleApplication
from bacpypes.service.device import LocalDeviceObject

from bacpypes.apdu import ReinitializeDeviceRequest, SimpleAckPDU

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
this_application = None

#
#   ReinitDeviceConsoleCmd
#

@bacpypes_debugging
class ReinitDeviceConsoleCmd(ConsoleCmd):

    def do_reinit(self, args):
        """reinit <addr> <state> Example state is coldstart..."""
        args = args.split()
        if _debug: ReinitDeviceConsoleCmd._debug("do_reinit %r", args)

        try:
            addr, state = args[:2]

            # build a request 
            request = ReinitializeDeviceRequest(
                reinitializedStateOfDevice=state
                )
            request.pduDestination = Address(addr)

            if _debug: ReinitDeviceConsoleCmd._debug("    - request: %r", request)

            # make an IOCB
            iocb = IOCB(request)
            if _debug: ReinitDeviceConsoleCmd._debug("    - iocb: %r", iocb)

            # give it to the application
            this_application.request_io(iocb)

            # wait for it to complete
            iocb.wait()

            # do something for success
            if iocb.ioResponse:
                # should be an ack
                if not isinstance(iocb.ioResponse, SimpleAckPDU):
                    if _debug: ReinitDeviceConsoleCmd._debug("    - not an ack")
                    return

                sys.stdout.write("ack\n")

            # do something for error/reject/abort
            if iocb.ioError:
                sys.stdout.write(str(iocb.ioError) + '\n')

        except Exception as error:
            ReinitDeviceConsoleCmd._exception("exception: %r", error)


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
    this_console = ReinitDeviceConsoleCmd()
    if _debug: _log.debug("    - this_console: %r", this_console)

    # enable sleeping will help with threads
    enable_sleeping()

    _log.debug("running")

    run()

    _log.debug("fini")

if __name__ == "__main__":
    main()
