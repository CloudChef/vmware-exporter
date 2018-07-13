import os
from prometheus_client.core import GaugeMetricFamily


DEFAULT_LOG_PATH = '/var/log/cloudchef/vmware_exporter/vmware_exporter.log'
APP_NAME = 'vmware-exporter'
log_path = os.environ.get('LOG_PATH', DEFAULT_LOG_PATH)

cloudentry_path = '/v1/kv/cmp/cloud_entry/vsphere?recurse'
vms_path = '/v1/kv/cmp/resource/vms?recurse'

vm_labels = ['external_id', 'external_name']

metric_list = {}
metric_list['vms'] = {
    'vmware_vm_power_state': GaugeMetricFamily(
        'vmware_vm_power_state',
        'VMWare VM Power state (On / Off)',
        labels=vm_labels),
    'vmware_vm_boot_timestamp_seconds': GaugeMetricFamily(
        'vmware_vm_boot_timestamp_seconds',
        'VMWare VM boot time in seconds',
        labels=vm_labels),
    'vmware_vm_snapshots': GaugeMetricFamily(
        'vmware_vm_snapshots',
        'VMWare current number of existing snapshots',
        labels=vm_labels),
    'vmware_vm_snapshot_timestamp_seconds': GaugeMetricFamily(
        'vmware_vm_snapshot_timestamp_seconds',
        'VMWare Snapshot creation time in seconds',
        labels=vm_labels + ['vm_snapshot_name']),
    'vmware_vm_num_cpu': GaugeMetricFamily(
        'vmware_vm_num_cpu',
        'VMWare Number of processors in the virtual machine',
        labels=vm_labels)
}
metric_list['datastores'] = {
    'vmware_datastore_capacity_size': GaugeMetricFamily(
        'vmware_datastore_capacity_size',
        'VMWare Datasore capacity in bytes',
        labels=['cloud_entry_id', 'name', 'datastore_id', 'host_id']),
    'vmware_datastore_freespace_size': GaugeMetricFamily(
        'vmware_datastore_freespace_size',
        'VMWare Datastore freespace in bytes',
        labels=['cloud_entry_id', 'name', 'datastore_id', 'host_id']),
    'vmware_datastore_uncommited_size': GaugeMetricFamily(
        'vmware_datastore_uncommited_size',
        'VMWare Datastore uncommitted in bytes',
        labels=['cloud_entry_id', 'name', 'datastore_id', 'host_id']),
    'vmware_datastore_provisoned_size': GaugeMetricFamily(
        'vmware_datastore_provisoned_size',
        'VMWare Datastore provisoned in bytes',
        labels=['cloud_entry_id', 'name', 'datastore_id', 'host_id']),
    'vmware_datastore_hosts': GaugeMetricFamily(
        'vmware_datastore_hosts',
        'VMWare Hosts number using this datastore',
        labels=['cloud_entry_id', 'name', 'datastore_id']),
    'vmware_datastore_vms': GaugeMetricFamily(
        'vmware_datastore_vms',
        'VMWare Virtual Machines number using this datastore',
        labels=['cloud_entry_id', 'name', 'datastore_id'])
}
metric_list['hosts'] = {
    'vmware_host_power_state': GaugeMetricFamily(
        'vmware_host_power_state',
        'VMWare Host Power state (On / Off)',
        labels=['cloud_entry_id', 'name', 'host_id']),
    'vmware_host_boot_timestamp_seconds': GaugeMetricFamily(
        'vmware_host_boot_timestamp_seconds',
        'VMWare Host boot time in seconds',
        labels=['cloud_entry_id', 'name', 'host_id']),
    'vmware_host_cpu_usage': GaugeMetricFamily(
        'vmware_host_cpu_usage',
        'VMWare Host CPU usage in Mhz',
        labels=['cloud_entry_id', 'name', 'host_id']),
    'vmware_host_cpu_max': GaugeMetricFamily(
        'vmware_host_cpu_max',
        'VMWare Host CPU max availability in Mhz',
        labels=['cloud_entry_id', 'name', 'host_id']),
    'vmware_host_memory_usage': GaugeMetricFamily(
        'vmware_host_memory_usage',
        'VMWare Host Memory usage in Mbytes',
        labels=['cloud_entry_id', 'name', 'host_id']),
    'vmware_host_memory_max': GaugeMetricFamily(
        'vmware_host_memory_max',
        'VMWare Host Memory Max availability in Mbytes',
        labels=['cloud_entry_id', 'name', 'host_id']),
}


perf_labels = {'vmware_vm_host_memory_usage': "summary.quickStats.hostMemoryUsage",
               "vmware_vm_overall_cpu_usage": "summary.quickStats.overallCpuUsage",
               "vmware_vm_overall_cpu_demand": "summary.quickStats.overallCpuDemand",
               "vmware_vm_max_cpu_usage": "summary.runtime.maxCpuUsage",
               "vmware_vm_memory_size_mb": "summary.config.memorySizeMB",
               "vmware_vm_guest_memory_usage": "summary.quickStats.guestMemoryUsage",
               "vmware_vm_max_memory_usage": "summary.runtime.maxMemoryUsage",
               "vmware_vm_private_memory": "summary.quickStats.privateMemory",
               "vmware_vm_shared_memory": "summary.quickStats.sharedMemory",
               "vmware_vm_compressed_memory": "summary.quickStats.compressedMemory",
               "vmware_vm_ballooned_memory": "summary.quickStats.balloonedMemory",
               "vmware_vm_swapped_memory": "summary.quickStats.swappedMemory",
               "vmware_vm_consumed_overhead_memory": "summary.quickStats.consumedOverheadMemory",
               "vmware_vm_storage_committed": "summary.storage.committed",
               "vmware_vm_storage_uncommitted": "summary.storage.uncommitted",
               "vmware_vm_storage_unshared": "summary.storage.unshared",
               "vmware_vm_storage_committed_and_uncommitted": None
               }


vm_properties = ["summary.runtime.powerState", "summary.runtime.bootTime",
                 "summary.runtime.maxMemoryUsage", "summary.quickStats.privateMemory",
                 "summary.quickStats.sharedMemory", "summary.quickStats.compressedMemory",
                 "summary.quickStats.balloonedMemory", "summary.quickStats.swappedMemory",
                 "summary.runtime.maxCpuUsage", "summary.quickStats.overallCpuUsage",
                 "summary.quickStats.consumedOverheadMemory",
                 "summary.quickStats.hostMemoryUsage", "summary.quickStats.overallCpuDemand",
                 "summary.quickStats.guestMemoryUsage", "summary.runtime.maxMemoryUsage",
                 "summary.storage.committed", "summary.storage.uncommitted",
                 "summary.storage.unshared", "guest.disk",
                 "name", "snapshot", "snapshot.rootSnapshotList",
                 "summary.quickStats.hostMemoryUsage",
                 "summary.vm", "summary.runtime.host", "datastore",
                 "summary.config.memorySizeMB", "summary.config.numCpu"]

data_properties = ["summary.capacity", "summary.freeSpace", "summary.uncommitted",
                   "summary.name", "host", "vm", "summary.datastore"]
host_properties = ["name", "summary.quickStats.overallCpuUsage", "summary.host",
                   "summary.quickStats.overallMemoryUsage", "summary.hardware.memorySize",
                   "summary.hardware.cpuMhz",  "summary.hardware.numCpuCores",
                   "summary.runtime.bootTime", "summary.runtime.powerState"]
