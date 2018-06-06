#!/usr/bin/env python
# -*- coding: future_fstrings -*-

# MIT License
#
# Copyright (c) 2018 Alexandr Malygin
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import print_function
from functools import wraps  # used by sphinx to pick up docstring from decorated methods properly
import logging
import atexit
from pyVim.connect import SmartConnectNoSSL, Disconnect
from pyVmomi import vim, vmodl
from .helpers import VMJHelper
from .exceptions import WrongObjectTypeError


class VCenter(object):
    """
    VCenter object

    :param str address: VCenter address or IP.
    :param str username: User name.
    :param str password: User password.
    """

    def __init__(self, address, username, password,):
        self._raw_global = None
        self._return_single = False
        self._address = address
        self._username = username
        self._password = password
        self.si = None  #: ServiceInstance. Populated once connected to VMWare VCenter.
        self.content = None  #: "content" of ServiceInstance. Populated once connected to VMWare VCenter.
    
    class Decor(object):
        @staticmethod
        def single_object(fn):
            @wraps(fn)
            def wrapper(self, *args, **kwargs):
                r = fn(self, *args, **kwargs)
                if len(r) == 1 and self.return_single:
                    r = r[0]
                elif len(r) == 0 and self.return_single:
                    r = None
                return r
            return wrapper

        @staticmethod
        def benchmark(func):
            import time

            def wrapper(*args, **kwargs):
                t = time.clock()
                res = func(*args, **kwargs)
                print(f'---  | {func.__name__} | {time.clock() - t} |  ---')
                return res

            return wrapper

    def connect(self, exit_on_fault=True):
        """
        Connect to VCenter.

        Currently doesn't use certificate, as it not used in the most installations or self-signed used.

        :param bool exit_on_fault: Perform exit on connection fault if True, otherwise returns None.
        :return: VMWare ServiceInstance object or None in case of connection fault.
        """
        logging.info(f'Connecting to {self._address} ...')
        try:
            si = SmartConnectNoSSL(host=self._address,
                                   user=self._username,
                                   pwd=self._password)
            self.si = si
            self.content = si.RetrieveServiceContent()
            atexit.register(Disconnect, si)
            logging.info(f'Connected to {self._address}')
            return si

        except vim.fault.InvalidLogin as e:
            logging.info(e.msg)
            if exit_on_fault:
                exit(1)
            else:
                return None
        except Exception:
            logging.info('Unable to connect. Check address and credentials.')
            if exit_on_fault:
                exit(1)
            else:
                return None

    def disconnect(self):
        """Close connection with VCenter."""
        if self.si:
            Disconnect(self.si)
            self.si = None
            logging.info(f'Disconnected from {self._address}')
        return 0

    @property
    def raw_global(self):
        """
        Return raw_global parameter.

        :return: Boolean or None.
        """
        return self._raw_global

    def set_raw_global(self, value):
        """
        Set raw_global parameter.

        The raw_globals defines type of objects to be returned by get_* methods.\n
        True -  always return raw VMWare Managed object.\n
        False - always return extended vmjuggler.* object.\n
        None -  return type defined independently by 'raw' parameter of the get_* methods.

        :param bool value: True/False/None.
        :return: set value.
        """
        if value is None or isinstance(value, bool):
            self._raw_global = value
            return self.raw_global
        else:
            raise TypeError('Boolean or None expected')

    @property
    def return_single(self):
        """
        Return return_single parameter.

        :return:
        """
        return self._return_single

    def set_return_single(self, value):
        """
        Set return_single parameter

        If set, output of get_* methods changes as follow:\n
        If returning list of objects has the only one element it will be returned as single object, not as a list.\n
        If returning list is empty, the None will be returned.\n
        The feature is implemented by using decorator :mod:`@Decor.single_object`.

        :param bool value:
        :return: set value.
        """
        if isinstance(value, bool):
            self._return_single = value
            return self._return_single
        else:
            raise TypeError('Boolean expected')

    def _get_return_type(self, return_type, raw):
        """
        Helper method to calculate return_type depends on 'raw_global' and 'raw' parameters.

        :param cls return_type: Class of desired return type.
        :param bool raw: True/False.
        :return: bool or None.
        """
        if self.raw_global is None:
            r = None if raw else return_type
        elif self.raw_global:
            r = None
        else:
            r = return_type
        return r

    def _get_vc_objects(self, obj_type, root=None, name=None, get_all=True, recursive=True, return_type=None):
        """
        Fetch list of objects from VCenter such as VM, DC, Folder, VApp, Network, Datastore, Host.

        :param obj_type: List of object's types to fetch. The following are valid values:
                         [vim.VirtualMachine,
                          vim.Datacenter,
                          vim.Folder,
                          vim.VirtualApp,
                          vim.Network,
                          vim.Datastore,
                          vim.HostSystem]
        :param str root: The folder to start looking from. Default 'si.content.rootFolder' used if not specified.
        :param str name: The name or list of names of objects to find.
        :param bool get_all: The 'name' ignored and all objects of specified types are returned if set to True.
        :param bool recursive: Find objects recursively or not.
        :param: return_type: The Class the output will be converted to.
        :return: List of objects.
        """
        root = root if root else self.content.rootFolder
        obj_view = self.content.viewManager.CreateContainerView(root, obj_type, recursive)
        obj_list = obj_view.view
        obj_view.Destroy()

        r = []
        if get_all:
            r = obj_list
        elif name is not None:
            name = [name] if isinstance(name, str) else name
            cnt = len(name)
            for el in obj_list:
                el_name = el.name
                for n in name:
                    if el_name == n:
                        r.append(el)
                        cnt -= 1
                        break
                if cnt == 0:  # all names found
                    break

        if return_type is not None:
            rn = []
            for el in r:
                rn.append(return_type(el))
            r = rn
        return r

    @Decor.single_object
    def get_vm(self, name=None, root=None, get_all=False, raw=False):
        """
        Get the VM by name or list of all VMs.

        :param str name: VM name or list of names.
        :param str root: The folder to start looking from.
        :param bool get_all: The 'name' ignored and all objects of specified types are returned if set to True.
        :param bool raw: The raw objects will be returned if set otherwise 'vmjuggler.VirtualMachine' type.
        :return: List of objects.
        """
        obj_type = [vim.VirtualMachine]
        return_type = VirtualMachine
        return_type = self._get_return_type(return_type, raw)
        obj_list = self._get_vc_objects(obj_type, root=root, name=name, get_all=get_all, return_type=return_type)
        return obj_list

    @Decor.single_object
    def get_dc(self, name=None, root=None, get_all=False, raw=False):
        """
        Get the Datacenter by name or list of all DCs.

        :param str name: DC name or list of names.
        :param str root: The folder to start looking from.
        :param bool get_all: The 'name' ignored and all objects of specified types are returned if set to True.
        :param bool raw: The raw objects will be returned if set otherwise 'vmjuggler.DataCenter' type.
        :return: List of objects.
        """
        obj_type = [vim.Datacenter]
        return_type = Datacenter
        return_type = self._get_return_type(return_type, raw)
        obj_list = self._get_vc_objects(obj_type, root=root, name=name, get_all=get_all, return_type=return_type)
        return obj_list

    @Decor.single_object
    def get_folder(self, name=None, root=None, get_all=False, raw=False):
        """
        Get the Folder by name or list of all Folders.

        :param str name: Folder name or list of names.
        :param str root: The folder to start looking from.
        :param bool get_all: The 'name' ignored and all objects of specified types are returned if set to True.
        :param bool raw: The raw objects will be returned if set otherwise 'vmjuggler.Folder' type.
        :return: List of objects.
        """
        obj_type = [vim.Folder]
        return_type = Folder
        return_type = self._get_return_type(return_type, raw)
        obj_list = self._get_vc_objects(obj_type, root=root, name=name, get_all=get_all, return_type=return_type)
        return obj_list

    @Decor.single_object
    def get_vapp(self, name=None, root=None, get_all=False, raw=False):
        """
        Get the VApp by name or list of all VApps.

        :param str name: VApp name or list of names.
        :param str root: The folder to start looking from.
        :param bool get_all: The 'name' ignored and all objects of specified types are returned if set to True.
        :param bool raw: The raw objects will be returned if set otherwise 'vmjuggler.VApp' type.
        :return: List of objects.
        """
        obj_type = [vim.VirtualApp]
        return_type = VApp
        return_type = self._get_return_type(return_type, raw)
        obj_list = self._get_vc_objects(obj_type, root=root, name=name, get_all=get_all, return_type=return_type)
        return obj_list

    @Decor.single_object
    def get_network(self, name=None, root=None, get_all=False, raw=False):
        """
        Get the Network by name or list of all Networks.

        :param str name: Network name or list of names.
        :param str root: The folder to start looking from.
        :param bool get_all: The 'name' ignored and all objects of specified types are returned if set to True.
        :param bool raw: The raw objects will be returned if set otherwise 'vmjuggler.Network' type.
        :return: List of objects.
        """
        obj_type = [vim.Network]
        return_type = Network
        return_type = self._get_return_type(return_type, raw)
        obj_list = self._get_vc_objects(obj_type, root=root, name=name, get_all=get_all, return_type=return_type)
        return obj_list

    @Decor.single_object
    def get_datastore(self, name=None, root=None, get_all=False, raw=False):
        """
        Get the Datastore by name or list of all Datastores.

        :param str name: Datastore name or list of names.
        :param str root: The folder to start looking from.
        :param bool get_all: The 'name' ignored and all objects of specified types are returned if set to True.
        :param bool raw: The raw objects will be returned if set otherwise 'vmjuggler.Datastore' type.
        :return: List of objects.
        """
        obj_type = [vim.Datastore]
        return_type = Datastore
        return_type = self._get_return_type(return_type, raw)
        obj_list = self._get_vc_objects(obj_type, root=root, name=name, get_all=get_all, return_type=return_type)
        return obj_list

    @Decor.single_object
    def get_host(self, name=None, root=None, get_all=False, raw=False):
        """
        Get the Host by name or list of all Hosts.

        :param str name: DC name or list of names.
        :param str root: The folder to start looking from.
        :param bool get_all: The 'name' ignored and all objects of specified types are returned if set to True.
        :param bool raw: The raw objects will be returned if set otherwise 'vmjuggler.Host' type.
        :return: List of objects.
        """
        obj_type = [vim.HostSystem]
        return_type = Host
        return_type = self._get_return_type(return_type, raw)
        obj_list = self._get_vc_objects(obj_type, root=root, name=name, get_all=get_all, return_type=return_type)
        return obj_list

    @Decor.single_object
    def get_all(self, name=None, root=None, get_all=False, raw=False):
        """
        Get the object by name or list of all objects.

        :param str name: Object name or list of names.
        :param str root: The folder to start looking from.
        :param bool get_all: The 'name' ignored and all objects of specified types are returned if set to True.
        :param bool raw: The raw objects will be returned if set otherwise 'vmjuggler.BaseVCObject' type.
        :return: List of objects.
        """
        obj_type = []
        return_type = BaseVCObject
        return_type = self._get_return_type(return_type, raw)
        obj_list = self._get_vc_objects(obj_type, root=root, name=name, get_all=get_all, return_type=return_type)
        return obj_list

    def create_vm(self):
        """
        Create new VM.

        :return:
        """
        # Not implemented
        pass


class BaseVCObject(object):
    """
    Base object for vmjuggler objects.

    :param vc_object: Raw VMWare ManagedObject
    """

    _raw_obj = None  #: Raw object. Populated once instance created.
    _name = None  #: Object's name. Populated once instance created.

    def __init__(self, vc_object):
        self._raw_obj = vc_object
        self._name = vc_object.name
        self._ex = [vmodl.RuntimeFault]  # To keep common catchable exceptions

    @property
    def raw_obj(self):
        """Raw object. Populated once instance created."""
        return self._raw_obj

    @property
    def name(self):
        """Object's name. Populated once instance created."""
        return self._name

    def _do(self, task, catch_exception=None):
        """
        Execute task and catch passed exceptions.

        Used to run tasks which not create the Task object.

        :param vim.Task task: The method to execute.
        :param list catch_exception: List of possible exceptions to catch.
        :return: True on success, False if any listed exception occurred
        """
        ex = tuple(set(self._ex + catch_exception)) if isinstance(catch_exception, list) else tuple(self._ex)
        try:
            task()
            return True
        except ex as e:
            logging.info(f'Error: {e.msg}')
            return False


class VirtualMachine(BaseVCObject):
    """
    VirtualMachine object

    Wrapper for vim.VirtualMachine

    :param vim.VirtualMachine vc_object: Raw VMWare ManagedObject
    """
    def __init__(self, vc_object):
        expect = vim.VirtualMachine  # Allowed object type
        # Object specific exceptions to catch
        common_exceptions = [vmodl.fault.NotSupported,
                             vim.fault.TaskInProgress, vim.fault.InvalidState, vim.fault.InvalidPowerState]
        if isinstance(vc_object, expect):
            super(VirtualMachine, self).__init__(vc_object)
            self._ex = list(set(self._ex + common_exceptions))
        else:
            raise WrongObjectTypeError(self.__class__.__name__, expect.__name__)

    @property
    def _is_snap_exists(self):
        """Check if snapshots exist"""
        return True if self.raw_obj.snapshot else False

    def _get_snaps(self, root=None, name=None, **kwargs):
        """
        Return snapshot(s) if exists

        :param str root: Root snapshot folder to look for in
        :param str name: Snapshot name to look for. All snapshots fetched if not specified.
        :param bool to_print: If set, the tuple prepared for print will be returned. !!!Use only for print!!!
        :param int level: Snapshot level from root. Used with 'to_print' to form tree.
        :param: mo_id: ManagedObject ID, used to retrieve snapshot name when current snapshot used.
        :return: List of snapshots
        """
        if not self._is_snap_exists:
            return []

        to_print = kwargs['to_print'] if 'to_print' in kwargs else False
        level = kwargs['level'] if 'level' in kwargs and to_print else 0
        mo_id = kwargs['mo_id'] if 'mo_id' in kwargs else None

        root = root if root is not None else self.raw_obj.snapshot.rootSnapshotList
        sn_list = []
        for snl in root:
            rr = {'level': level, 'snap': snl.name} if to_print else snl
            r = self._get_snaps(root=snl.childSnapshotList, name=name, level=level + 1, to_print=to_print, mo_id=mo_id)
            r.insert(0, rr)
            for el in r:
                if name is None and mo_id is None:
                    sn_list.append(el)
                elif el.name == name:
                    sn_list.append(el)
                    break
                elif mo_id and el.snapshot._moId == mo_id:
                    sn_list.append(el)
                    break
        return sn_list

    def get_snap(self, name=None, current=False, get_all=False, raw=False):
        """
        Return list of snapshot objects.

        :param str name: Snapshot name.
        :param bool current: If set the 'name' is ignored and current snapshot returned.
        :param bool get_all: If set the 'name' and 'current' are ignored and all VM snapshots returned.
        :param bool raw: If set the raw VMWare snapshot object returned.
        :return: List of vmjuggler.VMSnapshot objects.
        """

        r = []
        if name is None and not current and not get_all:
            return r
        sn_name = None if get_all else name
        current = False if get_all else current

        if current:
            sn = self.raw_obj.snapshot.currentSnapshot
            snls = self._get_snaps(mo_id=sn._moId)  # Need SnapshotTree object to get name and other data

        else:
            snls = self._get_snaps(name=sn_name)

        if not raw:
            for el in snls:
                logging.debug(f'Found snapshot: {el.name}')
                r.append(VMSnapshot(el))
        else:
            r = snls
        return r

    def list_snaps(self):
        """
        Prints out all VM snapshots.

        :return: n/a
        """
        for sn in self._get_snaps(to_print=True):
            indent = ' '*sn['level']
            print(f'{indent}|{sn["snap"]}')

    def revert(self, snapshot_name=None, current=False):
        """
        Revert to snapshot.

        :param str snapshot_name: Snapshot name.
        :param bool current: Revert to current snapshot if set. The 'name' is ignored.
        :return: True on success, otherwise False.
        """
        if snapshot_name is None and not current:
            logging.info('Either "snapshot_name" or "current" parameter should be specified.')
            return False
        sn = self.get_snap(name=snapshot_name, current=current, raw=False)
        return sn[0].revert() if len(sn) == 1 else False

    def create_snap(self, name, description=None, memory=True, quiesce=False):
        """
        Create snapshot.

        :param str name: Snapshot name.
        :param str description: Snapshot description.
        :param bool memory: If set, the memory will be included to snapshot.
        :param bool quiesce: If set, the quiesce snapshot will be created.
        :return: True on success, otherwise False
        """
        logging.info(f'Creating snapshot "{name}" for VM "{self.name}"...')
        ex = [vim.fault.InvalidName]
        ex = list(set(self._ex + ex))
        task = self.raw_obj.CreateSnapshot_Task
        r = VMJHelper.do_task(task, catch_exception=ex, name=name, description=description, memory=memory, quiesce=quiesce)
        return r

    def remove_snap(self, name=None, current=False, remove_all=False, remove_children=False, consolidate=False):
        """
        Remove snapshot or all snapshots.

        :param str name: Snapshot name.
        :param bool current: If set, the current snapshot will be deleted, "name" parameter is ignored.
        :param bool remove_all: If set, all snapshots will be removed, "name" and "current" parameters are ignored.
        :param bool remove_children: If set, children snapshots will be removed along with parent.
        :param bool consolidate: If set, the consolidation will be performed.
        :return: True on success, False if any of snapshots failed to be removed.
        """
        if name is None and not current and not remove_all:
            logging.info('Either "snapshot_name" or "current" or "remove_all" parameter should be specified.')
            return False

        sn = self.get_snap(name=name, current=current, get_all=remove_all, raw=False)
        r = True
        for el in sn:
            pr = el.remove(remove_children=remove_children, consolidate=consolidate)
            r = pr if not pr else r
        return r

    @property
    def state(self):
        """
        VM power state.

        :return: str: "poweredOff", "poweredOn" or "suspended"
        """
        r = self.raw_obj.summary.runtime.powerState
        return r

    def power_on(self):
        """
        Power On VM.

        :return: True on success, otherwise False.
        """
        logging.info(f'Powering on VM "{self.name}" ...')
        task = self.raw_obj.PowerOnVM_Task
        r = VMJHelper.do_task(task, catch_exception=self._ex)
        return r

    def power_off(self):
        """
        Power Off VM.

        :return: True on success, otherwise False.
        """
        logging.info(f'Powering on VM "{self.name}" ...')
        task = self.raw_obj.PowerOffVM_Task
        r = VMJHelper.do_task(task, catch_exception=self._ex)
        return r

    def shutdown(self):
        """
        Shutdown OS on VM.

        :return: True on success, otherwise False.
        """
        logging.info(f'Shutting down VM "{self.name}"...')
        ex = [vim.fault.ToolsUnavailable]
        ex = list(set(self._ex + ex))
        task = self.raw_obj.ShutdownGuest
        r = self._do(task, catch_exception=ex)
        return r

    def terminate(self):
        """
        Immediately terminate VM.

        :return: True on success, otherwise False.
        """
        logging.info(f'Terminating VM "{self.name}"...')
        ex = self._ex
        task = self.raw_obj.TerminateVM
        r = self._do(task, catch_exception=ex)
        return r

    def suspend(self):
        """
        Suspend VM.

        :return: True on success, otherwise False.
        """
        logging.info(f'Suspending VM "{self.name}"...')
        ex = [vim.fault.TaskInProgress, vim.fault.ToolsUnavailable]
        ex = list(set(self._ex + ex))
        task = self.raw_obj.SuspendVM_Task
        r = VMJHelper.do_task(task, catch_exception=ex)
        return r

    def reboot(self):
        """
        Reboot VM.

        :return: True on success, otherwise False.
        """
        logging.info(f'Rebooting VM "{self.name}"...')
        ex = [vim.fault.TaskInProgress, vim.fault.ToolsUnavailable]
        ex = list(set(self._ex + ex))
        task = self.raw_obj.SRebootGuest
        r = self._do(task, catch_exception=ex)
        return r

    def reset(self):
        """
        Reset VM power.

        :return: True on success, otherwise False.
        """
        logging.info(f'Resetting VM "{self.name}"...')
        ex = [vim.fault.TaskInProgress]
        ex = list(set(self._ex + ex))
        task = self.raw_obj.ResetVM_Task
        r = VMJHelper.do_task(task, catch_exception=ex)
        return r


class Datacenter(BaseVCObject):
    """
    Datacenter object

    Wrapper for vim.Datacenter

    :param vim.Datacenjter vc_object: Raw VMWare ManagedObject
    """
    def __init__(self, vc_object):
        expect = vim.Datacenter
        common_exceptions = []
        if isinstance(vc_object, expect):
            super(Datacenter, self).__init__(vc_object)
            self._ex = list(set(self._ex + common_exceptions))
        else:
            raise WrongObjectTypeError(self.__class__.__name__, expect.__name__)


class Folder(BaseVCObject):
    """
    Folder object

    Wrapper for vim.Folder

    :param vim.Folder vc_object: Raw VMWare ManagedObject
    """
    def __init__(self, vc_object):
        expect = vim.Folder
        common_exceptions = []
        if isinstance(vc_object, expect):
            super(Folder, self).__init__(vc_object)
            self._ex = list(set(self._ex + common_exceptions))
        else:
            raise WrongObjectTypeError(self.__class__.__name__, expect.__name__)


class VApp(BaseVCObject):
    """
    VApp object

    Wrapper for vim.VApp

    :param vim.VApp vc_object: Raw VMWare ManagedObject
    """
    def __init__(self, vc_object):
        expect = vim.VirtualApp
        common_exceptions = []
        if isinstance(vc_object, expect):
            super(VApp, self).__init__(vc_object)
            self._ex = list(set(self._ex + common_exceptions))
        else:
            raise WrongObjectTypeError(self.__class__.__name__, expect.__name__)


class Network(BaseVCObject):
    """
    Network object

    Wrapper for vim.Network

    :param vim.Network vc_object: Raw VMWare ManagedObject
    """
    def __init__(self, vc_object):
        expect = vim.Network
        common_exceptions = []
        if isinstance(vc_object, expect):
            super(Network, self).__init__(vc_object)
            self._ex = list(set(self._ex + common_exceptions))
        else:
            raise WrongObjectTypeError(self.__class__.__name__, expect.__name__)


class Datastore(BaseVCObject):
    """
    Datastore object

    Wrapper for vim.Datastore

    :param vim.Datastore vc_object: Raw VMWare ManagedObject
    """
    def __init__(self, vc_object):
        expect = vim.Datastore
        common_exceptions = []
        if isinstance(vc_object, expect):
            super(Datastore, self).__init__(vc_object)
            self._ex = list(set(self._ex + common_exceptions))
        else:
            raise WrongObjectTypeError(self.__class__.__name__, expect.__name__)


class Host(BaseVCObject):
    """
    Host object

    Wrapper for vim.Host

    :param vim.Host vc_object: Raw VMWare ManagedObject
    """
    def __init__(self, vc_object):
        expect = vim.HostSystem
        common_exceptions = []
        if isinstance(vc_object, expect):
            super(Host, self).__init__(vc_object)
            self._ex = list(set(self._ex + common_exceptions))
        else:
            raise WrongObjectTypeError(self.__class__.__name__, expect.__name__)


class VMSnapshot(BaseVCObject):
    """
    VM Snapshot object.

    :param vc_object: SnapshotList object.
    """
    def __init__(self, vc_object):
        expect = vim.vm.SnapshotTree
        common_exceptions = []
        if isinstance(vc_object, expect):
            super(VMSnapshot, self).__init__(vc_object)
            self._ex = list(set(self._ex + common_exceptions))
            self.snap = vc_object.snapshot  #: Raw snapshot object. Populated once instance created.
            self.description = vc_object.description  #: Snapshot description. Populated once instance created.
            self.create_time = vc_object.createTime  #: Snapshot creation time. Populated once instance created.
            self.state = vc_object.state  #: vim.VirtualMachine.PowerState.[poweredOn, poweredOff, suspended]. Populated once instance created.
            self.vm = vc_object.vm  #: Raw vim.VirtualMachine object snapshot belongs to. Populated once instance created.
        else:
            raise WrongObjectTypeError(self.__class__.__name__, expect.__name__)

    def info(self):
        """
        Print out snapshot info.

        :return: n/a
        """
        msg = f"""\rSnapshot info:
                  \rVM:          {self.vm.name}
                  \rName:        {self.name}
                  \rDescription: {self.description}
                  \rCreated on:  {self.create_time}
                  \rState:       {self.state}"""
        print(msg)

    def remove(self, remove_children=False, consolidate=False):
        """
        Remove snapshot.

        :param bool remove_children: If set, the children snapshots will be removed too.
        :param bool consolidate: If set, disk images will be consolidated after snapshot removed.
        :return: True on success, otherwise False
        """
        task = self.snap.RemoveSnapshot_Task
        ex = [vim.fault.TaskInProgress]
        logging.info(f'Removing snapshot {self.name}...')
        r = VMJHelper.do_task(task, catch_exception=ex, removeChildren=remove_children, consolidate=consolidate)
        return r

    def rename(self, name=None, description=None):
        """
        Rename snapshot or change description.

        :param str name: New snapshot name.
        :param str description: New Description.
        :return: True on success, otherwise False
        """
        logging.info(f'Renaming snapshot "{self.name}" to "{name if  name else self.name}",'
                     f' with description "{description if description else self.description}"...')
        try:
            self.snap.RenameSnapshot(name=name, description=description)
            logging.info('Done')
            self.name = name if name else self.name
            return True
        except vim.fault.InvalidArgument as e:
            logging.info(f'Error: {e.msg}')
            return False

    def revert(self, suppress_power_on=False):
        """
        Revert snapshot.

        :param bool suppress_power_on:  If set, VM will not be powered on in case snapshot was created in VM powered on state.
        :return: True on success, otherwise False
        """
        task = self.snap.RevertToSnapshot_Task
        ex = [vim.fault.NotFound]
        logging.info(f'Reverting snapshot {self.name}...')
        r = VMJHelper.do_task(task, catch_exception=ex, suppressPowerOn=suppress_power_on)
        return r
