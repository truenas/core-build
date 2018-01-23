# Building FreeNAS 11 from Scratch

Note: All these commands must be run as `root`.


## Requirements:

* Hardware

  * CPU: amd64-compatible 64-bit Intel or AMD CPU.
  * 16GB memory, or the equivalent in memory plus swap space
  * at least 80GB of free disk space


* Software

  * The build environment must be FreeBSD 11.x (or 11-STABLE)
    (building on FreeBSD 10 or 12 is not supported at this time).

  * Required packages must be installed and set up:

    * ```
      pkg install -y archivers/pigz archivers/pxz devel/git devel/gmake lang/python3 lang/python ports-mgmt/poudriere-devel sysutils/grub2-efi sysutils/grub2-pcbsd sysutils/xorriso sysutils/grub2-efi```
      rehash
      python2.7 -m ensurepip
      python2.7 -m pip install six
      ```

    ```textproc/py-sphinx_numfig``` must be installed from ports as there
    is no package for it. This requires the ports tree to be installed:

    * ```make -C /usr/ports/textproc/py-sphinx_numfig install clean```

    ```make bootstrap-pkgs``` installs required dependencies automatically.
    It only installs what is listed in the ```Makefile```.


## Make Targets

* ```checkout``` creates a local working copy of the git repositories with
  ```git clone```

* ```update``` does a ```git pull``` to update the local working copy with
  any changes made to the git repositories since the last update

* ```release``` actually builds the FreeNAS release

* ```clean``` removes previously built files


## Procedure

Clone the build repository and switch to that directory
(```/usr/build``` is used for this example):

```
git clone https://github.com/freenas/build /usr/build
cd /usr/build
```


First-time checkout of source:

```
make checkout
```


A FreeNAS release is built by first updating the source, then building:

```
make update
make release
```

To build the SDK version:

```
make update
make release BUILD_SDK=yes
```


Clean builds take a while, not just due to operating system builds, but
because poudriere has to build all of the ports. Later builds are faster,
only rebuilding files that need it.

Use ```make clean``` to remove all built files.


## Results

Built files are in the ```freenas/_BE``` subdirectory,
```/usr/build/freenas/_BE``` in this example.

ISO files: ```freenas/_BE/release/FreeNAS-11-MASTER-{date}/x64/```.

Update files: ```freenas/_BE/release/```.

Log files: ```freenas/_BE/objs/logs/```.
