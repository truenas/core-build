# Building TrueNAS 12 CORE/Enterprise from Scratch

Note: All these commands must be run as `root`.


## Requirements:

* Hardware

  * CPU: amd64-compatible 64-bit Intel or AMD CPU.
  * 16GB memory, or the equivalent in memory plus swap space
  * at least 80GB of free disk space

* Operating System

  * The build environment must be FreeBSD 12.x (or 12-STABLE)


## Make Targets

* ```checkout``` creates a local working copy of the git repositories with
  ```git clone```

* ```update``` does a ```git pull``` to update the local working copy with
  any changes made to the git repositories since the last update

* ```release``` actually builds the FreeNAS release

* ```clean``` removes previously built files


## Procedure

* Install git
    ```
    pkg install -y git
    rehash
    ```

* Clone the build repository (```/usr/build``` is used for this example):

    ```
    git clone https://github.com/truenas/build /usr/build
    ```

* Install Dependencies

    ```
    cd /usr/build
    make bootstrap-pkgs
    python3 -m ensurepip
    python3 pip install six
    ```


* First-time checkout of source:

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

ISO files: ```freenas/_BE/release/TrueNAS-12-MASTER-{date}/x64/```.

Update files: ```freenas/_BE/release/```.

Log files: ```freenas/_BE/objs/logs/```.
