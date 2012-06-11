# copynes
Command line interface for [CopyNES](http://www.retrousb.com/product_info.php?products_id=36), a NES copier originally designed by [Kevin Horton](http://kevtris.org/Projects/copynes/).

---

## Requirements

- clone the repository
- place your plugins in the "plugin" directory. The plugin filenames are assumed to use only upper case characters, e.g. `NROM.BIN`.

### Windows
- install [FTDI virtual COM port drivers](http://www.ftdichip.com/Drivers/VCP.htm)
- install [Python 3](http://www.python.org/download/releases/3.2.3/) and [pyserial](http://www.lfd.uci.edu/~gohlke/pythonlibs/#pyserial)

### Mac OS X

- install [FTDI virtual COM port drivers](http://www.ftdichip.com/Drivers/VCP.htm)
- install Python 3 and `pyserial`

e.g. using [MacPorts](http://www.macports.org/):

    sudo port install python32 py32-serial

### Linux
- install Python 3 and `pyserial`

e.g. using `apt-get`:

    sudo apt-get install python3 python3-serial

---

## Usage

Pass the `--help` parameter to get brief usage instructions:

    copynes.py --help

### Dump a ROM
First, make sure to place the appropriate plugin in the `plugins` directory, e.g. `plugins/NROM.BIN`.

CopyNES plugins don't communicate which iNES mapper they are dumping so you will need to explicitly declare a mapper number for the dump.

    copynes.py download NROM > smb.nes
    copynes.py download --mapper 3 CNROM > adventure-island.nes

### Upload to RAM cart
First, make sure to place the appropriate plugin in the `plugins` directory, e.g. `plugins/PPLITE.BIN`.

    copynes.py upload --plugin pplite < smb.nes

### Read memory
Get a binary dump of CPU memory space.

    copynes.py readcpu 0x0000 0x07ff > ram-dump.bin

### Write memory
Write data to CPU memory space.

    copynes.py writecpu 0x0000 < ram-dump.bin

### Run CopyNES plugin
Run a custom CopyNES plugin. Data sent from the plugin is not handled in any way, the plugin is just started and then ignored.

    copynes.py run < my-custom-plugin.bin

### Check BIOS version

    copynes.py version

### Play cartridge

If the USB cable is connected, CopyNES starts in "copy" mode, i.e. it does nothing and only only waits for a command. To start playing a cartridge, use the "play" command.

    copynes.py play

---

## Serial ports

CopyNES uses two serial ports for communication. The program will try to guess the names of these ports, but may get confused if there are other FTDI devices connected (e.g. Arduino). If you're having problems connecting to the CopyNES you may have to explicitly declare which ports to use:

    copynes.py --data COM4 --control COM5 ...