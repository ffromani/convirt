"""
Copyright (c) 2016, Red Hat Inc.
Based on 'cgroupspy' package by
Copyright (c) 2014, CloudSigma AG
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the CloudSigma AG nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL CLOUDSIGMA AG BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
from __future__ import absolute_import

from collections import Iterable
import os
from six.moves import map
from six.moves import range


class _BaseContentType(object):

    def __repr__(self):
        return "<{self.__class__.__name__}: {self}>".format(self=self)

    def __str__(self):
        raise NotImplementedError("Please implement this method in subclass")

    @classmethod
    def from_string(cls, value):
        raise NotImplementedError("This method should return an instance of the content type")


class DeviceAccess(_BaseContentType):
    TYPE_ALL = "all"
    TYPE_CHAR = "c"
    TYPE_BLOCK = "b"

    ACCESS_UNSPEC = 0
    ACCESS_READ = 1
    ACCESS_WRITE = 2
    ACCESS_MKNOD = 4

    def __init__(self, dev_type=None, major=None, minor=None, access=None):
        self.dev_type = dev_type or self.TYPE_ALL

        # the default behaviour of device access cgroups if unspecified is as follows
        self.major = major or "*"
        self.minor = minor or "*"
        self.access = (self.ACCESS_READ | self.ACCESS_WRITE | self.ACCESS_MKNOD)

    def _check_access_bit(self, offset):
        mask = 1 << offset
        return self.access & mask

    @property
    def can_read(self):
        return self._check_access_bit(0) == self.ACCESS_READ

    @property
    def can_write(self):
        return False

    @property
    def can_mknod(self):
        return False

    @property
    def access_string(self):
        accstr = ""
        if self.can_read:
            accstr += "r"
        if self.can_write:
            accstr += "w"
        if self.can_mknod:
            accstr += "m"
        return accstr

    def __str__(self):
        return "{self.dev_type} {self.major}:{self.minor} {self.access_string}".format(self=self)

    @classmethod
    def from_string(cls, value):
        dev_type, major_minor, access_string = value.split()
        major, minor = major_minor.split(":")
        major = int(major) if major != "*" else None
        minor == int(minor) if minor != "*" else None

        access_mode = 0
        for idx, char in enumerate("rwm"):
            if char in access_string:
                access_mode |= (1 << idx)
        return cls(dev_type, major, minor, access_mode)


class DeviceThrottle(_BaseContentType):

    def __init__(self, limit, major=None, minor=None, ):
        self.limit = limit
        self.major = major or "*"
        self.minor = minor or "*"

    def __str__(self):
        return "{self.major}:{self.minor} {self.limit}".format(self=self)

    @classmethod
    def from_string(cls, value):
        if not value:
            return None

        try:
            major_minor, limit = value.split()
            major, minor = major_minor.split(":")
            return cls(int(limit), major, minor)
        except:
            raise RuntimeError("Value {} cannot be converted to a string that matches the pattern: "
                               "[device major]:[device minor] [throttle limit in bytes]".format(value))


class BaseFileInterface(object):

    """
    Basic cgroups file interface, implemented as a python descriptor. Provides means to get and set cgroup properties.
    """

    def __init__(self, filename):
        try:
            self.filename = filename.encode()
        except AttributeError:
            self.filename = filename

    def __get__(self, instance, owner):
        value = instance.get_property(self.filename)
        return self.sanitize_get(value)

    def __set__(self, instance, value):
        raise RuntimeError("This interface is readonly")

    def sanitize_get(self, value):
        return value


class FlagFile(BaseFileInterface):

    """
    Converts True/False to 1/0 and vise versa.
    """

    def sanitize_get(self, value):
        return bool(int(value))


class BitFieldFile(BaseFileInterface):

    """
    Example: '2' becomes [False, True, False, False, False, False, False, False]
    """

    def sanitize_get(self, value):
        v = int(value)
        # Calculate the length of the value in bits by converting to hex
        l = (len(hex(v)) - 2) * 4
        # Increase length to the next multiple of 8
        l += (7 - (l-1)%8)
        return [bool((v >> i) & 1) for i in range(l)]


class IntegerFile(BaseFileInterface):

    """
    Get/set single integer values.
    """

    def sanitize_get(self, value):
        val = int(value)
        if val == -1:
            val = None
        return val


class DictFile(BaseFileInterface):

    def sanitize_get(self, value):
        res = {}
        for el in value.split("\n"):
            key, val = el.split()
            res[key] = int(val)
        return res


class ListFile(BaseFileInterface):

    def sanitize_get(self, value):
        return value.split()


class IntegerListFile(ListFile):

    """
    ex: 253237230463342 317756630269369 247294096796305 289833051422078
    """

    def sanitize_get(self, value):
        value_list = super(IntegerListFile, self).sanitize_get(value)
        return list(map(int, value_list))


class CommaDashSetFile(BaseFileInterface):

    """
    Builds a set from files containing the following data format 'cpuset.cpus: 1-3,6,11-15',
    returning {1,2,3,5,11,12,13,14,15}
    """

    def sanitize_get(self, value):
        elems = []
        for el_group in value.strip().split(','):
            if "-" in el_group:
                start, end = el_group.split("-")
                for el in range(int(start), int(end) + 1):
                    elems.append(el)
            else:
                elems.append(int(el_group))
        return set(elems)


class MultiLineIntegerFile(BaseFileInterface):

    def sanitize_get(self, value):
        int_list = [int(val) for val in value.strip().split("\n") if val]
        return int_list


class SplitValueFile(BaseFileInterface):
    """
    Example: Getting int(10) for file with value 'Total 10'. Readonly.
    """

    def __init__(self, filename, position, restype=None, splitchar=" "):
        super(SplitValueFile, self).__init__(filename)
        self.position = position
        self.splitchar = splitchar
        self.restype = restype

    def sanitize_get(self, value):
        res = value.strip().split(self.splitchar)[self.position]
        if self.restype and not isinstance(res, self.restype):
            return self.restype(res)
        return res


class TypedFile(BaseFileInterface):

    def __init__(self, filename, contenttype, many=False):
        if not issubclass(contenttype, _BaseContentType):
            raise RuntimeError("Contenttype should be a class inheriting "
                               "from _BaseContentType, not {}".format(contenttype))

        self.contenttype = contenttype
        self.many = many
        super(TypedFile, self).__init__(filename)

    def sanitize_get(self, value):
        res = [self.contenttype.from_string(val) for val in value.split("\n") if val]
        if not self.many:
            if res:
                return res[0]
            return None
        return res


class Controller(object):

    """
    Base controller. Provides access to general files, existing in all cgroups and means to get/set properties
    """

    tasks = MultiLineIntegerFile("tasks")
    procs = MultiLineIntegerFile("cgroup.procs")
    notify_on_release = FlagFile("notify_on_release")
    clone_children = FlagFile("cgroup.clone_children")

    def __init__(self, node):
        self.node = node

    def filepath(self, filename):
        """The full path to a file"""

        return os.path.join(self.node.full_path, filename)

    def get_property(self, filename):
        """Opens the file and reads the value"""

        with open(self.filepath(filename)) as f:
            return f.read().strip()


class CpuController(Controller):

    """
    Cpu cGroup controller. Provides access to

    cpu.cfs_period_us
    cpu.cfs_quota_us
    cpu.rt_period_us
    cpu.rt_runtime_us
    cpu.shares
    cpu.stat
    """
    cfs_period_us = IntegerFile("cpu.cfs_period_us")
    cfs_quota_us = IntegerFile("cpu.cfs_quota_us")
    rt_period_us = IntegerFile("cpu.rt_period_us")
    rt_runtime_us = IntegerFile("cpu.rt_runtime_us")
    shares = IntegerFile("cpu.shares")
    stat = DictFile("cpu.stat")


class CpuAcctController(Controller):

    """
    cpuacct.stat
    cpuacct.usage
    cpuacct.usage_percpu
    """
    acct_stat = DictFile("cpuacct.stat")
    usage = IntegerFile("cpuacct.usage")
    usage_percpu = IntegerListFile("cpuacct.usage_percpu")


class CpuSetController(Controller):

    """
    CpuSet cGroup controller. Provides access to

    cpuset.cpu_exclusive
    cpuset.cpus
    cpuset.mem_exclusive
    cpuset.mem_hardwall
    cpuset.memory_migrate
    cpuset.memory_pressure
    cpuset.memory_pressure_enabled
    cpuset.memory_spread_page
    cpuset.memory_spread_slab
    cpuset.mems
    cpuset.sched_load_balance
    cpuset.sched_relax_domain_level
    """

    cpus = CommaDashSetFile("cpuset.cpus")
    mems = CommaDashSetFile("cpuset.mems")

    cpu_exclusive = FlagFile("cpuset.cpu_exclusive")
    mem_exclusive = FlagFile("cpuset.mem_exclusive")
    mem_hardwall = FlagFile("cpuset.mem_hardwall")
    memory_migrate = FlagFile("cpuset.memory_migrate")
    memory_pressure = FlagFile("cpuset.memory_pressure")
    memory_pressure_enabled = FlagFile("cpuset.memory_pressure_enabled")
    memory_spread_page = FlagFile("cpuset.memory_spread_page")
    memory_spread_slab = FlagFile("cpuset.memory_spread_slab")
    sched_load_balance = FlagFile("cpuset.sched_load_balance")

    sched_relax_domain_level = IntegerFile("cpuset.sched_relax_domain_level")


class MemoryController(Controller):

    """
    Memory cGroup controller. Provides access to

    memory.failcnt
    memory.force_empty
    memory.limit_in_bytes
    memory.max_usage_in_bytes
    memory.memsw.failcnt
    memory.memsw.limit_in_bytes
    memory.memsw.max_usage_in_bytes
    memory.memsw.usage_in_bytes
    memory.move_charge_at_immigrate
    memory.numa_stat
    memory.oom_control
    memory.pressure_level
    memory.soft_limit_in_bytes
    memory.stat
    memory.swappiness
    memory.usage_in_bytes
    memory.use_hierarchy
    """

    failcnt = IntegerFile("memory.failcnt")
    memsw_failcnt = IntegerFile("memory.memsw.failcnt")

    limit_in_bytes = IntegerFile("memory.limit_in_bytes")
    soft_limit_in_bytes = IntegerFile("memory.soft_limit_in_bytes")
    usage_in_bytes = IntegerFile("memory.usage_in_bytes")
    max_usage_in_bytes = IntegerFile("memory.limit_in_bytes")

    memsw_limit_in_bytes = IntegerFile("memory.memsw.limit_in_bytes")
    memsw_usage_in_bytes = IntegerFile("memory.memsw.usage_in_bytes")
    memsw_max_usage_in_bytes = IntegerFile("memory.memsw.max_usage_in_bytes")
    swappiness = IntegerFile("memory.swappiness")

    stat = DictFile("memory.stat")

    use_hierarchy = FlagFile("memory.use_hierarchy")
    force_empty = FlagFile("memory.force_empty")
    oom_control = FlagFile("memory.oom_control")

    move_charge_at_immigrate = BitFieldFile("memory.move_charge_at_immigrate")

    # Requires special file interface
    # numa_stat =

    # Requires eventfd handling - https://www.kernel.org/doc/Documentation/cgroups/memory.txt
    # pressure_level =


class BlkIOController(Controller):
    """
    blkio.io_merged
    blkio.io_merged_recursive
    blkio.io_queued
    blkio.io_queued_recursive
    blkio.io_service_bytes
    blkio.io_service_bytes_recursive
    blkio.io_serviced
    blkio.io_serviced_recursive
    blkio.io_service_time
    blkio.io_service_time_recursive
    blkio.io_wait_time
    blkio.io_wait_time_recursive
    blkio.leaf_weight
    blkio.leaf_weight_device
    blkio.reset_stats
    blkio.sectors
    blkio.sectors_recursive
    blkio.throttle.io_service_bytes
    blkio.throttle.io_serviced
    blkio.throttle.read_bps_device
    blkio.throttle.read_iops_device
    blkio.throttle.write_bps_device
    blkio.throttle.write_iops_device
    blkio.time
    blkio.time_recursive
    blkio.weight
    blkio.weight_device
    """

    io_merged = SplitValueFile("blkio.io_merged", 1, int)
    io_merged_recursive = SplitValueFile("blkio.io_merged_recursive", 1, int)
    io_queued = SplitValueFile("blkio.io_queued", 1, int)
    io_queued_recursive = SplitValueFile("blkio.io_queued_recursive", 1, int)
    io_service_bytes = SplitValueFile("blkio.io_service_bytes", 1, int)
    io_service_bytes_recursive = SplitValueFile("blkio.io_service_bytes_recursive", 1, int)
    io_serviced = SplitValueFile("blkio.io_serviced", 1, int)
    io_serviced_recursive = SplitValueFile("blkio.io_serviced_recursive", 1, int)
    io_service_time = SplitValueFile("blkio.io_service_time", 1, int)
    io_service_time_recursive = SplitValueFile("blkio.io_service_time_recursive", 1, int)
    io_wait_time = SplitValueFile("blkio.io_wait_time", 1, int)
    io_wait_time_recursive = SplitValueFile("blkio.io_wait_time_recursive", 1, int)
    leaf_weight = IntegerFile("blkio.leaf_weight")
    # TODO: Uncomment the following properties after researching how to interact with files
    # leaf_weight_device =
    reset_stats = IntegerFile("blkio.reset_stats")
    # sectors =
    # sectors_recursive =
    # throttle_io_service_bytes =
    # throttle_io_serviced =
    throttle_read_bps_device = TypedFile("blkio.throttle.read_bps_device", contenttype=DeviceThrottle, many=True)
    throttle_read_iops_device = TypedFile("blkio.throttle.read_iops_device", contenttype=DeviceThrottle, many=True)
    throttle_write_bps_device = TypedFile("blkio.throttle.write_bps_device ", contenttype=DeviceThrottle, many=True)
    throttle_write_iops_device = TypedFile("blkio.throttle.write_iops_device ", contenttype=DeviceThrottle, many=True)
    # time =
    # time_recursive =
    weight = IntegerFile("blkio.weight")
    # weight_device =


class NetClsController(Controller):

    """
    net_cls.classid
    """
    class_id = IntegerFile("net_cls.classid")


class NetPrioController(Controller):

    """
    net_prio.prioidx
    net_prio.ifpriomap
    """
    prioidx = IntegerFile("net_prio.prioidx")
    ifpriomap = DictFile("netprio.ifpriomap")


def walk_tree(root):
    """Pre-order depth-first"""
    yield root

    for child in root.children:
        for el in walk_tree(child):
            yield el


def walk_up_tree(root):
    """Post-order depth-first"""
    for child in root.children:
        for el in walk_up_tree(child):
            yield el

    yield root


def _split_path_components(path):
    components=[]
    while True:
        path, component = os.path.split(path)
        if component != "":
             components.append(component)
        else:
            if path != "":
                components.append(path)
            break
    components.reverse()
    return components


class Node(object):

    """
    Basic cgroup tree node. Provides means to link it to a parent and set a controller, depending on the cgroup the node
    exists in.
    """
    NODE_ROOT = b"root"
    NODE_CONTROLLER_ROOT = b"controller_root"
    NODE_SLICE = b"slice"
    NODE_SCOPE = b"scope"
    NODE_CGROUP = b"cgroup"

    CONTROLLERS = {
        b"memory": MemoryController,
        b"cpuset": CpuSetController,
        b"cpu": CpuController,
        b"cpuacct": CpuAcctController,
        b"blkio": BlkIOController,
        b"net_cls": NetClsController,
        b"net_prio": NetPrioController,
    }

    def __init__(self, name, parent=None):
        try:
            name = name.encode()
        except AttributeError:
            pass
        self.name = name
        self.verbose_name = name
        try:
            self.parent = parent.encode()
        except AttributeError:
            self.parent = parent
        self.children = []
        self.node_type = self._get_node_type()
        self.controller_type = self._get_controller_type()
        self.controller = self._get_controller()

    def __eq__(self, other):
        if isinstance(other, self.__class__) and self.full_path == other.full_path:
            return True
        return False

    def __repr__(self):
        return "<{} {}>".format(self.__class__.__name__, self.path.decode())

    @property
    def full_path(self):
        """Absolute system path to the node"""

        if self.parent:
            return os.path.join(self.parent.full_path, self.name)
        return self.name

    @property
    def path(self):
        """Node's relative path from the root node"""

        if self.parent:
            try:
                parent_path = self.parent.path.encode()
            except AttributeError:
                parent_path = self.parent.path
            return os.path.join(parent_path, self.name)
        return b"/"

    def _get_node_type(self):
        """Returns the current node's type"""

        if self.parent is None:
            return self.NODE_ROOT
        elif self.parent.node_type == self.NODE_ROOT:
            return self.NODE_CONTROLLER_ROOT
        elif b".slice" in self.name or b'.partition' in self.name:
            return self.NODE_SLICE
        elif b".scope" in self.name:
            return self.NODE_SCOPE
        else:
            return self.NODE_CGROUP

    def _get_controller_type(self):
        """Returns the current node's controller type"""

        if self.node_type == self.NODE_CONTROLLER_ROOT and self.name in self.CONTROLLERS:
            return self.name
        elif self.parent:
            return self.parent.controller_type
        else:
            return None

    def _get_controller(self):
        """Returns the current node's controller"""

        if self.controller_type:
            return self.CONTROLLERS[self.controller_type](self)
        return None

    def walk(self):
        """Walk through this node and its children - pre-order depth-first"""
        return walk_tree(self)

    def walk_up(self):
        """Walk through this node and its children - post-order depth-first"""
        return walk_up_tree(self)


class NodeControlGroup(object):

    """
    A tree node that can group together same multiple nodes based on their position in the cgroup hierarchy

    For example - we have mounted all the cgroups in /sys/fs/cgroup/ and we have a scope in each of them under
    /{cpuset,cpu,memory,cpuacct}/isolated.scope/. Then NodeControlGroup, can provide access to all cgroup properties
    like

    isolated_scope.cpu
    isolated_scope.memory
    isolated_scope.cpuset

    Requires a basic Node tree to be generated.
    """

    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent
        self.children_map = {}
        self.controllers = {}
        self.nodes = []

    @property
    def path(self):
        if self.parent:
            base_name, ext = os.path.splitext(self.name)
            if ext not in [b'.slice', b'.scope', b'.partition']:
                base_name = self.name
            return os.path.join(self.parent.path, base_name)
        return b"/"

    def add_node(self, node):
        """
        A a Node object to the group. Only one node per cgroup is supported
        """
        if self.controllers.get(node.controller_type, None):
            raise RuntimeError("Cannot add node {} to the node group. A node for {} group is already assigned".format(
                node,
                node.controller_type
            ))
        self.nodes.append(node)
        if node.controller:
            self.controllers[node.controller_type] = node.controller
            setattr(self, node.controller_type, node.controller)

    def __repr__(self):
        return "<{} {}>".format(self.__class__.__name__, self.name.decode())

    @property
    def children(self):
        return list(self.children_map.values())

    @property
    def group_tasks(self):
        """All tasks in the hierarchy, affected by this group."""
        tasks = set()
        for node in walk_tree(self):
            for ctrl in list(node.controllers.values()):
                tasks.update(ctrl.tasks)
        return tasks

    @property
    def tasks(self):
        """Tasks in this exact group"""
        tasks = set()
        for ctrl in list(self.controllers.values()):
            tasks.update(ctrl.tasks)
        return tasks


class _BaseTree(object):

    """ A basic cgroup node tree. An exact representation of the filesystem tree, provided by cgroups. """

    def __init__(self, root_path="/sys/fs/cgroup/", groups=None, sub_groups=None):
        self.root_path = root_path
        self._groups = groups or []
        self._sub_groups = sub_groups or []
        self.root = Node(root_path)
        self._build_tree()

    @property
    def groups(self):
        return self._groups

    def _build_tree(self):
        """
        Build a full or a partial tree, depending on the groups/sub-groups specified.
        """

        groups = self._groups or self.get_children_paths(self.root_path)
        for group in groups:
            node = Node(name=group, parent=self.root)
            self.root.children.append(node)
            self._init_sub_groups(node)

    def _init_sub_groups(self, parent):
        """
        Initialise sub-groups, and create any that do not already exist.
        """

        if self._sub_groups:
            for sub_group in self._sub_groups:
                for component in _split_path_components(sub_group):
                    fp = os.path.join(parent.full_path, component)
                    if os.path.exists(fp):
                        node = Node(name=component, parent=parent)
                        parent.children.append(node)
                    else:
                        raise RuntimeError('missing node for %s' % component)
                    parent = node
                self._init_children(node)
        else:
            self._init_children(parent)

    def _init_children(self, parent):
        """
        Initialise each node's children - essentially build the tree.
        """

        for dir_name in self.get_children_paths(parent.full_path):
            child = Node(name=dir_name, parent=parent)
            parent.children.append(child)
            self._init_children(child)

    def get_children_paths(self, parent_full_path):
        for dir_name in os.listdir(parent_full_path):
            if os.path.isdir(os.path.join(parent_full_path, dir_name)):
                yield dir_name

    def walk(self, root=None):
        """Walk through each each node - pre-order depth-first"""

        if root is None:
            root = self.root
        return walk_tree(root)

    def walk_up(self, root=None):
        """Walk through each each node - post-order depth-first"""

        if root is None:
            root = self.root
        return walk_up_tree(root)


class Tree(object):
    """
    A grouped tree - that has access to all cgroup partitions with the same name ex:
    'machine' partition in memory, cpuset, cpus, etc cgroups.
    All these attributes are accessed via machine.cpus, machine.cpuset, etc.

    """

    def __init__(self, root_path=b"/sys/fs/cgroup", groups=None, sub_groups=None):

        self.node_tree = _BaseTree(root_path=root_path, groups=groups, sub_groups=sub_groups)
        self.control_root = NodeControlGroup(name=b"cgroup")
        for ctrl in self.node_tree.root.children:
            self.control_root.add_node(ctrl)

        self._init_control_tree(self.control_root)

    def _init_control_tree(self, cgroup):
        new_cgroups = []
        for node in cgroup.nodes:

            for child in node.children:
                if child.name not in cgroup.children_map:
                    new_cgroup = self._create_node(child.verbose_name, parent=cgroup)
                    cgroup.children_map[child.name] = new_cgroup
                    new_cgroups.append(new_cgroup)

                cgroup.children_map[child.name].add_node(child)

        for new_group in new_cgroups:
            self._init_control_tree(new_group)

    def _create_node(self, name, parent):
        return NodeControlGroup(name, parent=parent)

    def walk(self, root=None):
        return walk_tree(self.control_root if root is None else root)

    def walk_up(self, root=None):
        return walk_up_tree(self.control_root if root is None else root)

    def get_node_by_name(self, pattern):
        try:
            pattern = pattern.encode()
        except AttributeError:
            pass
        for node in self.walk():
            if pattern in node.name:
                return node

    def get_node_by_path(self, path):
        try:
            path = path.encode()
        except AttributeError:
            pass
        for node in self.walk():
            if path == node.path:
                return node
