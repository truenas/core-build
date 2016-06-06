# Building / Updating FreeNAS 9.10 or 10

## Build Guide

Detailed instructions for building FreeNAS can be found [here](https://github.com/freenas/freenas-build/wiki/FreeNAS-9.10---10-—-Setting-up-a-FreeNAS-build-environment).

The steps below are the short summary version.

## Requirements

* Your build environment must be  FreeBSD 10.3-RELEASE or later (or FreeBSD 10-STABLE)
(building on FreeBSD 9 or 11 is not supported at this time).

* An amd64 capable processor.  12GB of memory, or an equal/greater amount
  of swap space, is also required.

* An internet connection for downloading source and packages

## Building FreeNAS

Note: All these commands must be run as `root`.

Install the dependencies:

    # make bootstrap-pkgs

Download and assemble the source code:

    # make checkout

Compile the source, then generate the .ISO:

    # make release

Once the build completes successfully, you'll have release bits in the _BE
directory. :smile:

### FreeNAS 9.10

To build FreeNAS 9.10, simply add the argument `PROFILE=freenas9` to the `checkout` and
`release` commands, or if you are using a custom profile (see build/profiles directory,
copy to new profile) then edit to suit. eg:

    # make checkout PROFILE=freenas9
    # make release PROFILE=freenas9

## Updating an existing installation

To update an existing FreeNAS 9.10 or 10 instance that you are using for development
purposes:

* ```make update```
* ```make ports```
* ```make reinstall-package package=freenas host=root@1.2.3.4```

Where 1.2.3.4 is the IP address of your development platform.  SSH will be
used to push and install the new packages onto that host.
