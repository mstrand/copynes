import time, logging, platform, glob
from serial import Serial
from copynes.rom import NESROM


class CopyNES(object):
    '''
    Interface to a CopyNES device
    '''

    ###########################################################################
    ##
    ## Status operations
    ##
    ###########################################################################

    def __init__(self, data_device, control_device):
        '''
        Connects to a USB CopyNES
        '''

        self.data_channel = Serial(data_device, 115200, timeout = 5)
        self.control_channel = Serial(control_device, 115200, timeout = 5)

        # Empty the read buffer
        time.sleep(0.1)
        self.data_channel.flushInput()

    def disconnect(self):
        '''
        Disconnects from the CopyNES device and frees up all resources
        '''
        self.data_channel.close()
        self.control_channel.close()

    def power(self):
        '''
        Returns True if the CopyNES is powered on
        '''
        return not self.control_channel.getCD()

    def reset(self):
        '''
        Resets the CopyNES CPU.
        In "play" mode, this runs the cartridge program
        In "copy" mode, the CopyNES will be waiting for commands
        '''
        self.control_channel.setDTR(False)
        self.control_channel.setDTR(True)

    def play_mode(self):
        '''
        Resets the CopyNES and puts it in "play" mode
        This disables the BIOS, so no I/O operations will be available
        until "copy" mode is enabled again
        '''
        self.control_channel.setRTS(False)
        self.reset()

    def copy_mode(self):
        '''
        Resets the CopyNES and puts it in "copy" mode
        '''
        self.control_channel.setRTS(True)
        self.reset()

    ###########################################################################
    ##
    ## IO operations
    ##
    ###########################################################################

    def write(self, data):
        '''
        Writes a sequence of bytes to the CopyNES
        '''
        if isinstance(data, int):
            data = bytes((data,))
        result = self.data_channel.write(data)
        self.data_channel.flush()
        return result

    def wait_for_data(self, timeout):
        '''
        Wait until data is available for reading
        '''
        while self.data_channel.inWaiting() == 0 and timeout > 0:
            time.sleep(0.1)
            timeout -= 0.1 # XXX Not very exact method of waiting
        return self.data_channel.inWaiting() > 0

    def read(self, size = 1):
        '''
        Reads a sequence of bytes transferred from the CopyNES
        '''
        if size == 0:
            return

        result = self.data_channel.read(size)
        if len(result) != size:
            raise Exception("timeout")
        return result

    def read_int(self):
        '''
        Reads a single byte transferred from the CopyNES
        '''
        return int(self.read()[0])

    def read_string(self):
        '''
        Reads a zero terminated string
        '''
        result = bytearray()
        byte = self.read()
        while ord(byte) != 0x00:
            result += byte
            byte = self.read()
        return result.decode()

    def flush(self):
        self.data_channel.flush()

    ###########################################################################
    ##
    ## BIOS operations
    ##
    ###########################################################################

    def version_string(self):
        '''
        Returns the CopyNES firmware version string
        '''
        self.write(0xa1)
        return self.read_string()

    def version(self):
        '''
        Returns the CopyNES firmware version number
        '''
        self.write(0xa2)
        return self.read_int()

    def __send_command(self, prolog, address, length, epilog):
        '''
        Send a CopyNES command
        '''
        address_lsb = (address & 0x00ff)
        address_msb = (address & 0xff00) >> 8
        length_lsb = (length & 0x00ff)
        length_msb = (length & 0xff00) >> 8

        if length_lsb != 0x00:
            raise Exception('Memory may only be read/written in $0100 byte chunks, you are trying with a $%04x byte chunk' % length)

        self.write(prolog)
        self.write(address_lsb)
        self.write(address_msb)
        self.write(length_msb)
        self.write(epilog)

    def read_cpu_memory(self, address, length):
        self.__send_command(0x3a, address, length, 0xa3)
        return self.read(length)

    def write_cpu_memory(self, address, data):
        self.__send_command(0x4b, address, len(data), 0xb4)
        return self.write(data)

    def execute_code(self, address):
        self.__send_command(0x7e, address, 0x00, 0xe7)

    ###########################################################################
    ##
    ## Convenience methods
    ##
    ###########################################################################

    def run_plugin(self, plugin):
        self.write_cpu_memory(0x0400, plugin.data)
        self.execute_code(0x0400)

    def download_rom(self, plugin, ines_mapper):

        ##
        ## Packet types sent by dumping plugins
        ##
        PACKET_EOD = 0
        PACKET_PRG_ROM = 1
        PACKET_CHR_ROM = 2
        PACKET_WRAM = 3
        PACKET_RESET = 4

        self.run_plugin(plugin)
        prom = crom = wram = []
        mirroring = self.read_int() ^ 0x01
        (packet_type, data) = self.__read_packet()
        while packet_type != PACKET_EOD:
            if packet_type == PACKET_PRG_ROM:
                prom = data
            elif packet_type == PACKET_CHR_ROM:
                crom = data
            elif packet_type == PACKET_WRAM:
                wram = data
            elif packet_type == PACKET_RESET:
                self.reset()
            else:
                raise Exception('Unexpected packet type: %d' % packet_type)
            (packet_type, data) = self.__read_packet()
        logging.debug('Downloaded prg: %d bytes, chr: %d bytes, wram: %d bytes, mirroring: %d, mapper: %d', len(prom), len(crom), len(wram), mirroring, ines_mapper)
        return NESROM(prom, crom, ines_mapper, mirroring)

    def __read_packet(self):
        pages = self.read_int() | (self.read_int() << 8)
        length = pages << 8
        packet_type = self.read_int()
        if packet_type == 0:
            return (packet_type, 0)
        data = self.read(length)
        return (packet_type, data)

    
    @staticmethod
    def default_data_device():
        if platform.system() == 'Windows':
            return 'COM3'
        elif platform.system() == 'Darwin':
            serial_devices = glob.glob('/dev/tty.usbserial-*')
            return serial_devices[0] if len(serial_devices) >= 2 else '?'
        else:
            return '/dev/ttyUSB0'

    @staticmethod
    def default_control_device():
        if platform.system() == 'Windows':
            return 'COM4'
        elif platform.system() == 'Darwin':
            serial_devices = glob.glob('/dev/tty.usbserial-*')
            return serial_devices[1] if len(serial_devices) >= 2 else '?'
        else:
            return '/dev/ttyUSB1'