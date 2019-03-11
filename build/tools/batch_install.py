#!/usr/bin/env python
# Batch installation script for FreeNAS/TrueNAS.
# This is intended to be run as part of the build tests.
# It takes one option, and at least one argument.
# The one option is for an install.conf file location,
# which can be used to set some defaults
# The first argument is the location of the build directory
# (it will determine everything else from there, including
# setting the search path for python); the optional other
# arguments are disk names to be installed onto.

import os, sys
import argparse

def ParseConfig(path="/etc/install.conf"):
    """
    Parse a configuration file used to automate installations.
    The result is a dictionary with the values parsed into their
    correct types.  The supported settings are:

    minDiskSize
    maxDiskSize:	A value indicationg the minimum and maximum disk size
    		when searching for disks.  No default value.
    whenDone:	A string, eithe reboot, wait, or halt, indicating what action to
		take after the installation is finished.  Default is to reboot.
    upgrade:	A string, "yes" or "no", indicating whether or not to do an upgrade.
    		Default is not to upgrade.
    mirror:	A string, "yes" or "no" or "force", indicating whether or not to install
    		to a mirror.
    format:	A string, either "efi" or "bios", indicating how to format the disk.
    		Default is None, which means not to format at all.
    disk,
    disks	A string indicating which disks to use for the installation.
    diskCount:	An integer, indicating how many disks to use when mirroring.

    By default, it will select the first disk it finds.  If mindDiskSize and/or maxDiskSize
    are set, it will use those to filter out disks.  If mirror is True, then it will use either
    two or diskCount (if set) disks to createa  mirror; if mirror is set to "force", then it
    will fail if it cannot find enough disks to create a mirror.
    """

    def yesno(s):
        if s.lower() in ["yes", "true"]:
            return True
        return False
    
    rv = {
        "whenDone" : "reboot",
        "upgrade"  : False,
        "mirror"   : False,
    }
    try:
        with open(path, "r") as f:
            for line in f:
                line = line.rstrip()
                if line.startswith("#"):
                    continue
                if not '=' in line:
                    continue
                (key, val) = line.split("=")
                if key in ["minDiskSize", "maxDiskSize"]:
                    val = ParseSize(val)
                elif key == "whenDone":
                    if val not in ["reboot", "wait", "halt"]:
                        continue
                elif key == "upgrade":
                    val = yesno(val)
                elif key == "format":
                    if val not in ["efi", "bios"]:
                        continue
                elif key == "mirror":
                    if val.lower() == "force":
                        val = True
                        rv["forceMirror"] = True
                    else:
                        val = yesno(val)
                elif key in ["disk", "disks"]:
                    key = "disks"
                    val = var.split()
                elif key == "diskCount":
                    val = int(val)
                    
                rv[key] = val
    except:
        pass
    return rv

arg_parser = argparse.ArgumentParser(description="Batch Installer")
arg_parser.add_argument('-C', '--config',
                        dest='config_file',
                        default='/etc/install.conf',
                        help='Specify configuration file')
arg_parser.add_argument("buildroot", nargs=1,
                        help='Specify root of build (e.g., /build/freenas/freenas/_BE)')
arg_parser.add_argument("disks", nargs='*',
                        help='Optional list of disks to install onto')

args = arg_parser.parse_args()

print("Args = {}".format(args))
# We locate certain files and libraries in the build root.
for p in ["objs/instufs/usr/local/lib"]:
    sys.path.append(os.path.join(args.buildroot[0], p))

avatar_file = os.path.join(args.buildroot[0], "objs/instufs/etc/avatar.conf")

from bsd.sysctl import sysctlbyname
from ixsystems.installer.Install import Install, InstallationError
import ixsystems.installer.Utils as Utils
from ixsystems.installer.Utils import InitLog, LogIt, Title, Project, SetProject
from ixsystems.installer.Utils import IsTruenas, LoadAvatar
from ixsystems.installer.Menu import validate_disk, ValidationError
import freenasOS.Manifest as Manifest
import freenasOS.Configuration as Configuration

InitLog(sys.stdout)
LoadAvatar(avatar_file)

install_config = ParseConfig(args.config_file)
# The big potential conflict between the config file and the
# command-line arguments are disks.  If no disks were specified, then
# we have to depend on the paramters in the config file.
if args.disks:
    install_config['disks'] = args.disks

if not install_config.get("disks", None):
    min_disk_size = install_config.get("minDiskSize", 0)
    max_disk_size = install_config.get("maxDiskSize", 0)
    diskCount = install_config.get("diskCount", 1)
    mirror = install_config.get("mirror", False)
    force_mirror = install_config.get("forceMirror", False)
    if force_mirror and diskCount < 2:
        diskCount = 2
    # Let's try searching for some disks then
    system_disks = sysctlbyname("kern.disks")
    if ord(system_disks[-1]) == 0:
        system_disks = system_disks[:-1]
    possible_disks = []
    for disk_name in system_disks.split():
        try:
            validate_disk(disk_name)
            disk = Utils.Disk(disk_name)
            if min_disk_size and disk.size < min_disk_size:
                LogIt("Disk {} is too small".format(disk_name))
                comtinue
            if max_disk_size and disk.size > max_disk_size:
                LogIt("Disk {} is too large".format(disk_name))
            possible_disks.append(disk_name)
        except ValidationError as e:
            LogIt(e.message)
        if len(possible_disks) >= diskCount:
            break

    if not possible_disks:
        LogIt("No suitable disks found for installation")
        raise InstallationError("No Disks Found")
    if len(possible_disks) < diskCount:
        LogIt("Needed {} disks, only found {}".format(diskCount, len(possible_disks)))
        raise InstallationError("Insufficient number of disks found")
    install_config['disks'] = possible_disks
    
if install_config["upgrade"]:
    LogIt("Currently cannot handle an upgrade, sorry")
    raise InstallationError("Cannot currently handle an upgrade")

install_disks = []
for disk in install_config["disks"]:
    install_disks.append(Utils.Disk(disk))

# Okay, at this point we are nearly all set.  Let's set up some variables
manifest_path = os.path.join(args.buildroot[0],
                             "release/LATEST/{}-MANIFEST".format(Project()))
manifest = Manifest.Manifest()
manifest.LoadPath(manifest_path)

package_dir = os.path.join(args.buildroot[0], "release/LATEST/Packages")

fn_conf = Configuration.SystemConfiguration()

template_dir = os.path.join(args.buildroot[0], "objs/instufs/data")

try:
    Install(interactive=False,
                    manifest=manifest,
                    config=fn_conf,
                    package_directory=package_dir,
                    disks=install_disks,
                    efi=install_config.get("format", "bios") == "efi",
                    upgrade=False,
                    data_dir=template_dir,
                    password=install_config.get("password", ""),
                    trampoline=True)
except BaseException as e:
    LogIt("Got exception {} during install".format(str(e)))
    raise e
sys.exit(0)
