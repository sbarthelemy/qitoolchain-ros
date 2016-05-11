How to build the rosbag package
===============================

Linux
-----

On ubuntu trusty 64 bits. Install deps as root::

  sudo apt-get install --assume-yes python python-devi git

All platforms:
--------------

Install the following packages with pip:

 * empy
 * catkin_pkg

On Windows, pending PR#144 (https://github.com/ros-infrastructure/catkin_pkg/pull/144),
you have to use catkin_pkg==0.20.1-win1 from our local PyPi mirror;
http://10.0.2.107/pypi/catkin_pkg-0.2.10-win1.zip

Then run build.py: package.xml and cmake files are stored in the
qibuild/ subdirectory: one per target (linux32, mac64, win32-vs2013 ...)
