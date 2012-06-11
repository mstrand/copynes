MIRRORING_HORIZONTAL  = 0x00
MIRRORING_VERTICAL    = 0x01
MIRRORING_FOUR_SCREEN = 0x02

class NESROM(object):

    def __init__(self, prom, crom, ines_mapper, mirroring):
        self.prom = prom
        self.crom = crom
        self.ines_mapper = ines_mapper & 0xff
        self.mirroring = mirroring & 0x03

def from_ines(file):
    header = file.read(0x10)
    if (header[:0x04] != b'NES\x1a'):
        raise Exception("Invalid iNES header")

    prom_size = header[4] * 0x4000
    crom_size = header[5] * 0x2000
    prom = file.read(prom_size)
    crom = file.read(crom_size)
    ines_mapper = (header[6] >> 4) | (header[7] & 0xf0)
    mirroring = MIRRORING_FOUR_SCREEN if (header[6] & 0x08) else (header[6] & 0x01)
    return NESROM(prom, crom, ines_mapper, mirroring)

def to_ines(rom, file):
    header = bytearray(0x10)
    header[0] = ord('N')
    header[1] = ord('E')
    header[2] = ord('S')
    header[3] = 0x1a
    header[4] = len(rom.prom) >> 14
    header[5] = len(rom.crom) >> 13
    header[6] = MIRRORING_FOUR_SCREEN if (rom.mirroring & MIRRORING_FOUR_SCREEN) else rom.mirroring
    header[6] |= (rom.ines_mapper & 0x0f) << 4
    header[7] = (rom.ines_mapper & 0xf0)

    file.write(header)
    file.write(rom.prom)
    file.write(rom.crom)
