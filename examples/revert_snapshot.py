from vmjuggler import VCenter

args = {'host': '10.0.0.1',    # VCenter IP or hostname
        'user': 'admin',       # VCenter username
        'pwd':  'admin_pwd'}   # Password

vm_name = 'TestBox01'          # VM name
snapshot_name = 'clean_state'  # Snapshot name

vc = VCenter(args['host'], args['user'], args['pwd'])
vc.set_return_single(True)
vc.connect()

vm = vc.get_vm(name=vm_name)
if vm:
    vm.revert(snapshot_name)

vc.disconnect()
