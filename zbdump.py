#!/usr/bin/env python

'''
zbdump.py - a tcpdump-like tool for ZigBee/IEEE 802.15.4 networks

Compatible with Wireshark 1.1.2 and later (jwright@willhackforsushi.com)
The -p flag adds CACE PPI headers to the PCAP (ryan@rmspeers.com)
'''

import sys
import signal
import argparse

import killerbee

def interrupt(signum, frame):
    global packetcount
    global kb
    global pd, dt
    kb.sniffer_off()
    kb.close()
    if pd:
        pd.close()
    if dt:
        dt.close()
    print(("{0} packets captured".format(packetcount)))
    sys.exit(0)

# PcapDumper, only used if -w is specified
pd = None
# DainTreeDumper, only used if -W is specified
dt = None

# Global
packetcount = 0

# Command-line arguments
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('-i', '--iface', '--dev', action='store', dest='devstring')
#parser.add_argument('-g', '--gps', '--ignore', action='append', dest='ignore')
parser.add_argument('-w', '--pcapfile', action='store')
parser.add_argument('-W', '--dsnafile', action='store')
parser.add_argument('-p', '--ppi', action='store_true')
parser.add_argument('-c', '-f', '--channel', action='store', type=int, default=None)
parser.add_argument('-n', '--count', action='store', type=int, default=-1)
parser.add_argument('-D', action='store_true', dest='showdev')
args = parser.parse_args()

if args.showdev:
    killerbee.show_dev()
    sys.exit(0)

if args.channel == None:
    print("ERROR: Must specify a channel.", file=sys.stderr)
    sys.exit(1)

if args.pcapfile is None and args.dsnafile is None:
    print("ERROR: Must specify a savefile with -w (libpcap) or -W (Daintree SNA)", file=sys.stderr)
    sys.exit(1)
elif args.pcapfile is not None:
    pd = killerbee.PcapDumper(killerbee.DLT_IEEE802_15_4, args.pcapfile, ppi=args.ppi)
elif args.dsnafile is not None:
    dt = killerbee.DainTreeDumper(args.dsnafile)

kb = killerbee.KillerBee(device=args.devstring)
signal.signal(signal.SIGINT, interrupt)
if not kb.is_valid_channel(args.channel):
    print("ERROR: Must specify a valid IEEE 802.15.4 channel for the selected device.", file=sys.stderr)
    kb.close()
    sys.exit(1)
kb.set_channel(args.channel)
kb.sniffer_on()

print(("zbdump.py: listening on \'{0}\', link-type DLT_IEEE802_15_4, capture size 127 bytes".format(kb.get_dev_info()[0])))

rf_freq_mhz = (args.channel - 10) * 5 + 2400
while args.count != packetcount:
    packet = kb.pnext()
    # packet[1] is True if CRC is correct, check removed to have promiscous capture regardless of CRC
    if packet != None: # and packet[1]:
        packetcount+=1
        if pd:
            pd.pcap_dump(packet['bytes'], ant_dbm=packet['dbm'], freq_mhz=rf_freq_mhz)
        if dt:
            dt.pwrite(packet['bytes'])

kb.sniffer_off()
kb.close()
if pd:
    pd.close()
if dt:
    dt.close()

print(("{0} packets captured".format(packetcount)))

