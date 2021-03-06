import sys, logging, argparse
from copynes import CopyNES
from copynes.rom import from_ines, to_ines
from copynes.plugin import CopyNESPlugin
import time

class CopyNESCLI(object):

    ##
    ## Parameter parsing
    ##
    
    @staticmethod
    def __parse_int(value):
        return int(value, 0)
    
    @staticmethod
    def __parse_input_file(value):
        return open(value, 'rb')

    @staticmethod
    def __parse_output_file(value):
        return open(value, 'wb')

    def process_command_line(self, parameters = sys.argv[1:]):
    
        parser = argparse.ArgumentParser(description = 'Command line interface to a USB CopyNES')
        parser.add_argument(
                '-v', '--verbose',
                action = 'count',
                help = 'increase logging level')
        parser.add_argument(
                '--data',
                metavar = 'DEVICE',
                default = CopyNES.default_data_device(),
                help = 'data device [default: %(default)s]')
        parser.add_argument(
                '--control',
                metavar = 'DEVICE',
                default =  CopyNES.default_control_device(),
                help = 'control device [default: %(default)s]')
        subparsers = parser.add_subparsers(
                dest = 'command',
                title = 'CopyNES operations',
                description = '(See "%(prog)s COMMAND -h" for more info)',
                help = '')
    
        subparser = subparsers.add_parser(
                'upload',
                description = 'Upload a ROM to a RAM cart and run it',
                help = 'upload NES ROM to RAM cart')
        subparser.add_argument(
                'file',
                nargs = '?',
                type = CopyNESCLI.__parse_input_file,
                default = sys.stdin.buffer,
                help = 'input filename [default: use stdin]')
        subparser.add_argument(
                '--plugin',
                choices = CopyNESPlugin.supported_upload_plugins(),
                default = CopyNESPlugin.supported_upload_plugins()[0],
                help = 'RAM cart plugin to use [default: %(default)s]')

        subparser = subparsers.add_parser(
                'run',
                description = 'run a CopyNES plugin',
                help = 'run a CopyNES plugin')
        subparser.add_argument(
                '--wait',
                metavar = 'n',
                default = 1,
                help = 'Let the plugin run for n seconds [default: %(default)s]')
        subparser.add_argument(
                'file',
                nargs = '?',
                type = CopyNESCLI.__parse_input_file,
                default = sys.stdin.buffer,
                help = 'plugin filename [default: use stdin]')

        subparser = subparsers.add_parser(
                'play',
                help = 'put the CopyNES in "play" mode')
    
        subparser = subparsers.add_parser(
                'download',
                help = 'dump a ROM from the CopyNES')
        subparser.add_argument(
                '--mapper',
                default = 0,
                help = 'iNES mapper number [default: %(default)s]')
        subparser.add_argument('plugin')
        subparser.add_argument(
                'file',
                nargs = '?',
                type = CopyNESCLI.__parse_output_file,
                default = sys.stdout.buffer,
                help = 'output filename [default: use stdout]')

        subparser = subparsers.add_parser(
                'readcpu',
                help = 'read bytes from CPU memory space')
        subparser.add_argument(
                'start',
                type = CopyNESCLI.__parse_int,
                help = 'start address (inclusive)')
        subparser.add_argument(
                'end',
                type = CopyNESCLI.__parse_int,
                help = 'end address (inclusive)')
        subparser.add_argument(
                'file',
                nargs = '?',
                type = CopyNESCLI.__parse_output_file,
                default = sys.stdout.buffer,
                help = 'output filename [default: use stdout]')

        subparser = subparsers.add_parser(
                'writecpu',
                help = 'write bytes to CPU memory space')
        subparser.add_argument(
                'address',
                type = CopyNESCLI.__parse_int,
                help = 'start address')
        subparser.add_argument(
                'file',
                nargs = '?',
                type = CopyNESCLI.__parse_output_file,
                default = sys.stdout.buffer,
                help = 'input filename [default: use stdout]')

        subparser = subparsers.add_parser(
                'version',
                help = 'display CopyNES BIOS version and exit',
                add_help = False)
    
        args = parser.parse_args(parameters)
        
        if not args.verbose:
            level = logging.ERROR
        elif args.verbose == 1:
            level = logging.INFO
        else:
            level = logging.DEBUG
        logging.basicConfig(stream = sys.stderr, level = level, format = '%(message)s')

        ##
        ## Handle command
        ##

        logging.info('Connecting to CopyNES')
        self.copynes = CopyNES(args.data, args.control)
    
        if not self.copynes.power():
            logging.error('Your CopyNES is not powered on!')
            exit(1)
    
        if args.command == 'version':
            self.display_version()
        elif args.command == 'upload':
            self.upload_rom(args.file, args.plugin)
        elif args.command == 'play':
            self.play_cart()
        elif args.command == 'download':
            self.download_rom(args.plugin, args.mapper, args.file)
        elif args.command == 'readcpu':
            if not (0 <= args.start < 0x10000) or not (0 <= args.end < 0x10000):
                logging.error("address must be within $0000-$FFFF")
            elif args.start > args.end:
                logging.error("end address must be >= start address")
            else:
                self.read_cpu_memory(args.start, args.end, args.file)
        elif args.command == 'writecpu':
            if not (0 <= args.address < 0x10000):
                logging.error("address must be within $0000-$FFFF")
            else:
                self.write_cpu_memory(args.address, args.file)
        elif args.command == 'run':
            self.run_plugin(args.file, args.wait)

        self.copynes.disconnect()
        logging.info('Disconnected from CopyNES')
        

    ##
    ## Actions
    ##
    
    def display_version(self):
        print("BIOS version: %d" % self.copynes.version())
        print(self.copynes.version_string())

    def play_cart(self):
        print("Entering play mode")
        self.copynes.play_mode()
        input("Press Enter to stop")
        self.copynes.copy_mode()
    
    def read_cpu_memory(self, start, end, file):
        read_start = start & 0xff00
        read_end = (end & 0xff00) + 0x0100
        read_length = read_end - read_start
        data = self.copynes.read_cpu_memory(read_start, read_length)

        data = data[start - read_start:end + 1 - read_start]
        file.write(data)
    
    def run_plugin(self, stream, wait):
        plugin = CopyNESPlugin(stream)
        self.copynes.run_plugin(plugin)
        time.sleep(float(wait))

    def write_cpu_memory(self, address, file):
        data = file.read()
        self.copynes.write_cpu_memory(address, data)

    def download_rom(self, plugin_name, ines_mapper, file):
        plugin = CopyNESPlugin.from_name(plugin_name)
        rom = self.copynes.download_rom(plugin, ines_mapper)
        to_ines(rom, file)

    def upload_rom(self, file, plugin_name):
        plugin = CopyNESPlugin.from_name(plugin_name)
        handler = CopyNESPlugin.upload_handler(plugin_name)
        rom = from_ines(file)
        handler(self.copynes, plugin, rom)
        self.play_cart()