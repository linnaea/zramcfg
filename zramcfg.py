#
# zramcfg
# Copyright (c) 2016 Julius & Hannes Reinecke
#
# Load and save the current ZRAM configuration
#

import io
import re
import glob
import subprocess
import argparse
import ConfigParser

class zramcfg:
    cfgnames = ['max_comp_streams' , 'comp_algorithm', 'disksize', 'mem_limit' ]

    def __init__(self, name):
        self.config = ConfigParser.SafeConfigParser()
        self.cfgfile = name

    def is_active(self, dev):
        # A disksize of '0' indicates an inactive device
        attrname = '/sys/block/' + dev + '/disksize'
        with open(attrname, 'r') as f:
            value = f.read()
            f.close()
            return int(value) != 0
        return False

    def save(self):
        # Read sysfs attributes from /sys/block/zram*
        for devpath in glob.glob('/sys/block/zram*'):
            zram = devpath.split('/')[-1]
            if not self.is_active(zram):
                continue
            # Save current configuration
            print 'Save configuration for /dev/' + zram
            self.config.add_section(zram)
            for attr in self.cfgnames:
                attrname = '/sys/block/' + zram + '/' + attr
                with open(attrname, 'r') as f:
                    value = f.readline()
                    f.close()
                    if attr == 'comp_algorithm':
                        for algo in value.split():
                            if algo.startswith('['):
                                self.config.set(zram, attr, algo.strip('[]'))
                    else:
                        self.config.set(zram, attr, value.rstrip())

        # Writing configuration file
        if self.config.sections():
            with open(self.cfgfile, 'wb') as configfile:
                self.config.write(configfile)

    def load(self):
        # Read configuration file
        if not self.config.read(self.cfgfile):
            print 'Could not load configuration file ' + self.cfgfile
            exit(0)

        for zram in self.config.sections():
            m = re.match(r"zram([0-9]*)", zram)
            if not m.group(1):
                print 'Invalid group name ' + zram
                continue
            zram_num = m.group(1)
            print 'Load configuration for /dev/zram' + str(zram_num)
            # Activate zram device
            while not glob.glob('/sys/block/' + zram):
                if not glob.glob('/sys/module/zram'):
                    if subprocess.call(["/sbin/modprobe","zram"]):
                        print 'Cannot load zram module'
                        exit(1)
                if not glob.glob('/sys/class/zram-control'):
                    print 'zram-control not present, cannot configure ' + zram
                    exit(1)
                with open('/sys/class/zram-control/hot_add', 'r') as f:
                    value = f.read()
                    f.close()
                    if int(value) >= zram_num:
                        break

            # Not able to configure device
            if not glob.glob('/sys/block/' + zram):
                print '/dev/' + zram + ' is not configured'
                continue

            # check if zram device is active
            if self.is_active(zram):
                print '/dev/' + zram + ' already active, skipping'
                continue
            # Write out configuration to sysfs attributes
            for attr in self.cfgnames:
                value = self.config.get(zram, attr)
		attrname = '/sys/block/' + zram + '/' + attr
		with open(attrname, 'w') as f:
                    f.write(value)
                    f.close()

# Main program
cfg = '/etc/zram.cfg'
parser = argparse.ArgumentParser(description="Configure ZRAM devices")
parser.add_argument("-c", "--config",
                    help="Use specified configuration file instead of /etc/zram.cfg")
parser.add_argument("action",
                    choices=['load', 'save'],
                    help="load/save the configuration file")
args = parser.parse_args()

if args.config:
    cfg = args.config

zram = zramcfg(cfg)
if args.action == 'load':
    zram.load()
else:
    zram.save()
