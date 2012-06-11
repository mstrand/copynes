import os.path

def _upload_to_powerpak_lite(copynes, plugin, rom):
    copynes.run_plugin(plugin)

    prom_banks = len(rom.prom) >> 14;
    crom_banks = len(rom.crom) >> 13;
    prom_config = (prom_banks - 1) * 0x10
    crom_config = (crom_banks - 1)

    if crom_banks == 0:
        crom_config = 0x20

    if rom.mirroring == 0x01:
        crom_config |= 0x10

    if rom.ines_mapper == 0:
        prom_max = 0x0400 * 32;
        crom_max = 0x0400 * 8;
        prom_config |= 0;
    elif rom.ines_mapper == 1:
        prom_max = 0x0400 * 256;
        crom_max = 0x0400 * 128
        prom_config |= 1;
    elif rom.ines_mapper == 2:
        prom_max = 0x0400 * 256;
        crom_max = 0;
        prom_config |= 2;
    elif rom.ines_mapper == 3:
        prom_max = 0x0400 * 32;
        crom_max = 0x0400 * 32;
        prom_config |= 3;
    elif rom.ines_mapper == 7:
        prom_max = 0x0400 * 256;
        crom_max = 0;
        prom_config |= 4;
    elif rom.ines_mapper == 11:
        prom_max = 0x0400 * 128;
        crom_max = 0x0400 * 128;
        prom_config |= 5;
    elif rom.ines_mapper == 34:
        prom_max = 0x0400 * 128;
        crom_max = 0;
        prom_config |= 6;
    elif rom.ines_mapper == 66:
        prom_max = 0x0400 * 128;
        crom_max = 0x0400 * 32;
        prom_config |= 7;
    else:
        raise Exception("Unsupported iNES mapper: %d" % rom.ines_mapper)

    if len(rom.prom) > prom_max:
        raise Exception("This NES ROM seems to have too much PRG data")

    if len(rom.crom) > crom_max:
        raise Exception("This NES ROM seems to have too much CHR data")

    copynes.write(prom_banks)
    copynes.write(rom.prom)
    copynes.write(crom_banks)
    copynes.write(rom.crom)
    copynes.write(prom_config)
    copynes.write(crom_config)

class CopyNESPlugin(object):
    '''
    A CopyNES plugin binary
    '''
    def __init__(self, file):

        data = file.read()
        self.header = data[:0x80]
        self.data = data[0x80:0x0480]

    @staticmethod
    def from_name(plugin_name):
        filename = os.path.join(os.path.dirname(__file__), '..', 'plugins', ("%s.bin" % plugin_name).upper())
        file = open(filename, 'rb')
        plugin = CopyNESPlugin(file)
        file.close()
        return plugin

    #
    # Each type of RAM cart uses a different protocol
    # This is a mapping from plugin name to an approprate "protocol handler"
    #
    __upload_plugins = {
        'pplite' : _upload_to_powerpak_lite
    
    }

    @staticmethod
    def supported_upload_plugins():
        return list(CopyNESPlugin.__upload_plugins.keys())

    @staticmethod
    def upload_handler(plugin_name):
        return CopyNESPlugin.__upload_plugins[plugin_name]

