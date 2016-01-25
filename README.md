conVirt
=======

conVirt is a python module that extends [libvirt](http://libvirt.org/index.html) and allows
you to run containers using [runc](http://runc.io/).
conVirt is implemented in pure python and plugs into python libvirt bindings, so your
python program which already uses libvirt can use conVirt with minimal or no changes.


License
-------
(C) 2015-206 Red Hat Inc.
Released under the terms of the GNU Lesser General Public License v2 or later (LGPLv2+).


Dependencies
------------
* [libvirt](http://libvirt.org) - python bindings for common infrastructure to plug into.
* [runc](http://runc.io) - to run containers.
* [systemd](http://www.freedesktop.org/wiki/Software/systemd/) - to supervise containers.

conVirt is developed and tested primarily on [fedora](https://getfedora.org/) and [centos](https://www.centos.org/).


Installation
-----------

TBW
