# Building / Updating FreeNAS 9.10 or 10

To update an existing FreeNAS 9.10 or 10 instance that you are using for development
purposes:

* ```make update```
* ```make ports```
* ```make reinstall-package package=freenas host=root@1.2.3.4```

Where 1.2.3.4 is the IP address of your development platform.  SSH will be
used to push and install the new packages onto that host.

To build FreeNAS 9.10 or 10 from scratch (experts only):

## Requirements:

* Your build environment must be  FreeBSD 10.1-RELEASE or later (or FreeBSD 10-STABLE)
(building on FreeBSD 9 or 11 is not supported at this time).

* An amd64 capable processor.  12GB of memory, or an equal/greater amount
  of swap space, is also required.

* You will need the following ports/packages when compiling anything
  FreeNAS-related:
  * ports-mgmt/poudriere-devel
  * devel/git
  * sysutils/cdrtools
  * archivers/pxz
  * lang/python3 (3.4 or later, must also be installed)
  * sysutils/grub2-pcbsd
  * sysutils/xorriso
  * devel/gmake
  * www/npm012

  (and all the dependencies that these ports/pkgs install, of course)
  
  You can also use ```make bootstrap-pkgs``` to let it install required
  dependencies automatically. It will only install whats listed in the Makefile
  you will need to install textproc/py-sphinx_numfig 
  from the ports systems as there are no packages available.

## Building the System Quickstart Flow:

Note: All these commands must be run as `root`.

To build FreeNAS 10
```
% make checkout
% make release
```

* Update the source tree to pull in new source code changes

```
% make update
```

This will also fetch TrueOS and ports for the build from github.

If you want to build FreeNAS 9.10, simply add the argument PROFILE=freenas9 to
the above commands (all of them, as relevant) or, if you are using a custom
profile (see build/profiles directory and copy / edit to suit).

## The End Result:

If your build completes successfully, you'll have release bits in the _BE
directory.
