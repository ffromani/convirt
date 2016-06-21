conVirt
=======

conVirt is a python module that provides a [libvirt](http://libvirt.org/index.html)-like API,
and allows you to run containers various runtimes.
conVirt is implemented in pure python and plugs into python libvirt bindings, so your
python program which already uses libvirt can use conVirt with minimal or no changes.

License
-------
(C) 2015-2016 Red Hat Inc.
Released under the terms of the GNU Lesser General Public License v2 or later (LGPLv2+).


Dependencies
------------
* [libvirt](http://libvirt.org) - python bindings for common infrastructure to plug into.
* [systemd](http://www.freedesktop.org/wiki/Software/systemd/) - to supervise containers.

conVirt is developed and tested primarily on [fedora >= 24](https://getfedora.org/)
and [centos >= 7.2](https://www.centos.org/).


Installation
-----------

This is a regular python package, so it is installable using the standard means:


  python setup.py install


The availability of RPM/deb packages and the uploading on PyPI is planned for near future.


Supported runtimes
------------------

* [rkt](http://coreos.com/rkt) - fully supported, reference runtime

* [runc](https://runc.io) - planned support, we never want this to break

* [docker](http://www.docker.com) - experimental support - may be broken

* NEXT - add your container runtime here!
