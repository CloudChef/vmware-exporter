# vmware-exporter
Prometheus exporter integrated with consul for VMWare vCenter. It collects information about individul VM, hosts, datastores, resource pools. In the future, vSAN and NSX components will also be supported.

## Collectors:


Name     | Descripton
---------|----------------------
`vmware_host_boot_timestamp_seconds` | VMWare Host boot time in seconds
`vmware_host_memory_max`          | VMWare Host Memory Max availability in Mbytes
`vmware_host_cpu_usage`           | VMWare Host CPU usage in Mhz
`vmware_host_power_state`          | VMWare Host Power state (On / Off)
`vmware_host_memory_usage`         | VMWare Host Memory usage in Mbytes
`vmware_host_cpu_max`             | VMWare Host CPU max availability in Mhz
`vmware_datastore_uncommited_size`   | VMWare Datastore uncommitted in bytes
`vmware_datastore_vms`            | VMWare Virtual Machines number using this datastore
`vmware_datastore_freespace_size`    | VMWare Datastore freespace in bytes
`vmware_datastore_hosts`          |  VMWare Hosts number using this datastore
`vmware_datastore_capacity_size`    | VMWare Datasore capacity in bytes
`vmware_datastore_provisoned_size`   | VMWare Datastore provisoned in bytes
`vmware_vm_power_state`          | VMWare VM Power state (On / Off)
`vmware_vm_guest_disk_capacity`    | VMWare VM guest disk capacity
`vmware_vm_guest_disk_free_space`   | VMWare VM guest disk free space
`vmware_vm_max_memory_usage`       | VMWare VM max memory usage
`vmware_vm_compressed_memory`      | VMWare VM compressed memory
`vmware_vm_host_memory_usage`     | VMWare VM host memory usage
`vmware_vm_guest_memory_usage`     | VMWare VM guest memory usage
`vmware_vm_shared_memory`          | VMWare VM shared memory
`vmware_vm_swapped_memory`         | VMWrre VM swapped memory
`vmware_vm_ballooned_memory`       | VMWare VM ballooned memory
`vmware_vm_consumed_overhead_memory` | VMWare VM consumed overhead memory
`vmware_vm_overall_cpu_usage`      | VMWare VM overall cpu usage
`vmware_vm_max_cpu_usage`          | VMWare VM max cpu usage
`vmware_vm_overall_cpu_demand`      | VMWare VM overall cpu demand
`vmware_vm_num_cpu`              | VMWare Number of processors in the virtual machine 
`vmware_vm_boot_timestamp_seconds`   | VMWare VM boot time in seconds
`vmware_vm_storage_uncommitted`    | VMWare VM storage uncommitted
`vmware_vm_storage_committed_and_uncommitted` | VMWare VM storage of committed and uncommitted
`vmware_vm_storage_unshared`      | VMWare VM storage unshared
`vmware_vm_memory_size_mb`         | VMWare VM memory size in MB
`vmware_vm_snapshots`             | VMWare vm number of snapshots


## Usage
- Monitor VMWares which registered on consul service.
- Monitor vms which registered on consul service.

- Vmware registered info:

			consul path: /v1/kv/cmp/cloud_entry/vsphere  #Defined in constants.py
			Formatter:
               {
				    "cloud_entry_id": "5d909776-d54c-433e-a212-38068d4e90e3",
				    "password": "a83c9514c91e5735a9c70dc0d00cbad4",
				    "port": "443",
				    "host": "192.168.1.10",
				    "username": "administrator@vsphere.local",
				    "status": "RUNNING",
				    "labels": {
				        "cloud_entry_id": "5d909776-d54c-433e-a212-38068d4e90e3"
				    }
			}

- Vms registered info:

			consul path: /v1/kv/cmp/resource/vms
			Formatter:
    			{
				    "monitor_source_type": "none",
				    "cloud_entry_id": "09aac4ff-81c3-4978-a337-c300fd290564",
				    "name": "WindowsServer_01",
				    "external_id": "vm-2678",
			}
				
#### Performance:
- Use PropertyCollector of Pyvmomi for vm filtering.
- Monitor message of 1000 vms can be got in 15s.


#### Installation:
- cd vmware_exporter
- sh scripts/install\_vmware_exporter.sh


#### Launch Service:
systemctl start cloudchef-vmware-exporter


#### Verification:
The prometheus metrics will be exposed on http://localhost:9272/metrics


### Prometheus configuration

Prometheus configuration file: 
```
  - job_name: 'smartcmp-cloudentry-monitor'
    static_configs:
      - targets: ['127.0.0.1:9272']
```

## References
Python modules:
- https://github.com/vmware/pyvmomi
- http://twistedmatrix.com/trac

The initial code is mainly inspired from:
- https://www.robustperception.io/writing-a-jenkins-exporter-in-python/
- https://github.com/vmware/pyvmomi-community-samples
- https://github.com/jbidinger/pyvmomi-tools

## License

See LICENSE file
