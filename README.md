# vmware-exporter
Prometheus exporter for Vmware hosts, integrated with consul for vsphere and vms registering.

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
- Vmware exporter monitor vmwares which integrated with, need to register vmwares info to consul first.
- Vmware exporter support filtering vms, only monitor vms' registered on consul.

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

#### Installation:
- cd vmware_exporter
- sh scripts/install\_vmware_exporter.sh



#### Launch Service:
systemctl start cloudchef-vmware-exporter



#### Verify:
The prometheus metrics will be exposed on http://localhost:9272/metrics



### Prometheus configuration

You can use the following parameters in prometheus configuration file. The `params` section is used to manage multiple login/passwords.

```
  - job_name: 'vmware_vcenter'
    metrics_path: '/metrics'
    static_configs:
      - targets:
        - 'vcenter.company.com
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: localhost:9272

  - job_name: 'vmware_esx'
    metrics_path: '/metrics'
    file_sd_configs:
      - files:
        - /etc/prometheus/esx.yml
    params:
      section: [esx]
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: localhost:9272
```

## References

The VMWare exporter uses theses libraries:
- [pyVmomi](https://github.com/vmware/pyvmomi) for VMWare connection and filter
- Prometheus [client_python](https://github.com/prometheus/client_python) for Prometheus supervision
- [Twisted](http://twistedmatrix.com/trac/) for http server

The initial code is mainly inspired from:
- https://www.robustperception.io/writing-a-jenkins-exporter-in-python/
- https://github.com/vmware/pyvmomi-community-samples
- https://github.com/jbidinger/pyvmomi-tools

## License

See LICENSE file
