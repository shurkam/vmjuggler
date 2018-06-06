What is vmjuggler
-----------------

**vmjuggler** provides the simple high level API to VMWare’s SDK.

It built around pyvmomi_ library with aim to simplify interaction to VMWare VCenter and it's managed objects
for DevOps crowd and those who don't want to plunge deeply to object's relations. At the same time ability
to perform actions on low level was preserved.

Installation
------------

``pip install vmjuggler``

Manual installation
-------------------
- Install following python packages

    - pyvmomi_
    - future-fstrings_ if used Python version < 3.5

- Download latest **vmjuuggler** from https://github.com/shurkam/vmjuggler
- Unpack and run ``python setup.py install``

Getting started
---------------

.. code-block:: python

    from vmjuggler import VCenter

    # Create instance of VCenter and connect to VCenter
    vc = VCenter('10.0.0.1', 'user', 'super_secret_password')
    vc.return_single(True)
    vc.connect()

    # Find VM and print out it's power state
    vm = vc.get_vm(name='My_Linux_VM')
    if vm:
        print(f'{vm.name} | {vm.state}')

    # Close connection to VCenter
    vc.disconnect()

Please check documentation_ for more examples.

.. _pyvmomi: https://github.com/vmware/pyvmomi
.. _future-fstrings: https://github.com/asottile/future-fstrings
.. _documentation: https://vmjuggler.readthedocs.io/en/latest/
