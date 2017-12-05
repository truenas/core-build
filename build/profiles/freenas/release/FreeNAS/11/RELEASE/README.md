# Building FreeNAS 11 from Scratch

Note: All these commands must be run as `root`.


## Requirements:

* Hardware

  * CPU: amd64-compatible 64-bit Intel or AMD CPU.
  * 12GB memory, or the equivalent in memory plus swap space


* Software

  * The build environment must be FreeBSD 11.x (or 11-STABLE)
    (building on FreeBSD 10 or 12 is not supported at this time).

  * Required packages must be installed:

    * ```pkg install -y archivers/pigz archivers/pxz devel/git devel/gmake lang/python3 lang/python ports-mgmt/poudriere-devel sysutils/grub2-efi sysutils/grub2-pcbsd sysutils/xorriso sysutils/grub2-efi```

    ```textproc/py-sphinx_numfig``` must be installed from ports as there
    is no package for it:

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

First-time checkout of source:

```
% make checkout
```

A FreeNAS release is built by first updating the source, then building:

```
% make update
% make release
```

## Results

After a successful build, the release is in the _BE subdirectory.
