from vmjuggler import VCenter

args = {'host': '10.0.0.1',  # VCenter IP or hostname
        'user': 'foo',       # VCenter username
        'pwd':  'foo_pwd'}   # Password

vm_name = 'BuildBox01'       # VM name

vc = VCenter(args['host'], args['user'], args['pwd'])
vc.set_return_single(True)
vc.connect()

vm = vc.get_vm(name=vm_name)
if vm:
    vm.power_on()

vc.disconnect()
