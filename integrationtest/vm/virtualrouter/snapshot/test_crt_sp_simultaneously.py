'''
Test create 100 snapshots simultaneously
@author: Mirabel
'''

import zstackwoodpecker.operations.resource_operations as res_ops
import zstackwoodpecker.operations.config_operations as con_ops
import zstackwoodpecker.zstack_test.zstack_test_volume as zstack_volume_header
import zstackwoodpecker.header.volume as volume_header
import zstackwoodpecker.test_util as test_util
import zstackwoodpecker.test_lib as test_lib
import zstackwoodpecker.test_state as test_state
import apibinding.inventory as inventory
import threading
import time

test_stub = test_lib.lib_get_test_stub()
test_obj_dict = test_state.TestStateDict()
session_to = None
session_mc = None

def test():
    global session_to
    global session_mc

    session_to = con_ops.change_global_config('identity', 'session.timeout', '720000')
    session_mc = con_ops.change_global_config('identity', 'session.maxConcurrent', '10000')
    test_util.test_dsc('Create test vm as utility vm')
    vm = test_stub.create_vlan_vm()
    test_obj_dict.add_vm(vm)
    #use root volume to skip add_checking_point
    test_util.test_dsc('Use root volume for snapshot testing')
    root_volume_inv = test_lib.lib_get_root_volume(vm.get_vm())
    root_volume = zstack_volume_header.ZstackTestVolume()
    root_volume.set_volume(root_volume_inv)
    root_volume.set_state(volume_header.ATTACHED)
    root_volume.set_target_vm(vm)
    test_obj_dict.add_volume(root_volume)
    vm.check()

    snapshots = test_obj_dict.get_volume_snapshot(root_volume.get_volume().uuid)
    snapshots.set_utility_vm(vm)

    ori_num = 100
    index = 1
    while index < 101:
        thread = threading.Thread(target=snapshots.create_snapshot, args=('create_snapshot%s' % str(index),))
        thread.start()
        index += 1

    while threading.activeCount() > 1:
        time.sleep(0.1)

    #snapshot.check() doesn't work for root volume
    #snapshots.check()
    #check if snapshot exists in install_path
    ps = test_lib.lib_get_primary_storage_by_vm(vm.get_vm())
    if ps.type == inventory.NFS_PRIMARY_STORAGE_TYPE or ps.type == inventory.LOCAL_STORAGE_TYPE:
        host = test_lib.lib_get_vm_host(vm.get_vm())
        for snapshot in snapshots.get_snapshot_list():
            snapshot_inv = snapshot.get_snapshot()
            sp_ps_install_path = snapshot_inv.primaryStorageInstallPath
            if test_lib.lib_check_file_exist(host, sp_ps_install_path):
                test_util.test_logger('Check result: snapshot %s is found in host %s in path %s' % (snapshot_inv.name, host.managementIp, sp_ps_install_path))
            else:
                test_lib.lib_robot_cleanup(test_obj_dict)
                test_util.test_fail('Check result: snapshot %s is not found in host %s in path %s' % (snapshot_inv.name, host.managementIp, sp_ps_install_path))
    else:
        test_util.test_logger('Skip check file install path for %s primary storage' % (ps.type))

    cond = res_ops.gen_query_conditions('volumeUuid', '=', root_volume.get_volume().uuid)
    sps_num = res_ops.query_resource_count(res_ops.VOLUME_SNAPSHOT, cond)

    if sps_num != ori_num:
        test_util_test_fail('Create %d snapshots, but only %d snapshots were successfully created' % (ori_num, sps_num))

    test_lib.lib_robot_cleanup(test_obj_dict)
    test_util.test_pass('Test create 100 snapshots simultaneously success')

def error_cleanup():
    test_lib.lib_error_cleanup(test_obj_dict)
