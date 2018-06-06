from vmjuggler import VCenter

args = {'host': '10.0.0.1',  # VCenter IP or hostname
        'user': 'foo',       # VCenter username
        'pwd':  'foo_pwd'}   # Password

vc = VCenter(args['host'], args['user'], args['pwd'])
vc.connect()

vms = vc.get_vm(get_all=True)
for vm in vms:
    print(f'{vm.name} | {vm.state}')

vc.disconnect()
