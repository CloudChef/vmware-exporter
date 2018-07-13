# vmware-exporter
VMWare VCenter Exporter for Prometheus.

Get VMWare VCenter information:
- Current number of active snapshots
- Snapshot Unix timestamp creation date
- Datastore size and other stuff
- Basic Host metrics
- Basic registered VMs metrics

## Usage
- Vmware exporter monitor vmwares which register on consul. So you need to register vmwares info to consul first.
- Vmware exporter support filtering vms, only get filtered vms' monitoring info. So you need to register vms which need monitoring to consul.

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

#### Install and run:
sh scripts/install\_vmware_exporter.sh



#### Boot:
systemctl start cloudchef-vmware-exporter



#### Verify:
Visit Website: http://localhost:9272/metrics



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

## Current Status

- VCenter and ESXi 6 and 6.5 have been tested.
- VM information, Snapshot, Host and Datastore basic information is exported, i.e:

```
# HELP vmware_snapshots VMWare current number of existing snapshots
# TYPE vmware_snapshot_count gauge
vmware_snapshot_timestamp_seconds{vm_name="My Super Virtual Machine"} 2.0
# HELP vmware_snapshot_timestamp_seconds VMWare Snapshot creation time in seconds
# TYPE vmware_snapshot_timestamp_seconds gauge
vmware_snapshot_age{vm_name="My Super Virtual Machine",vm_snapshot_name="Very old snaphot"} 1478146956.96092
vmware_snapshot_age{vm_name="My Super Virtual Machine",vm_snapshot_name="Old snapshot"} 1478470046.975632
# HELP vmware_datastore_capacity_size VMWare Datasore capacity in bytes
# TYPE vmware_datastore_capacity_size gauge
vmware_datastore_capacity_size{ds_name="ESX1-LOCAL"} 67377299456.0
# HELP vmware_datastore_freespace_size VMWare Datastore freespace in bytes
# TYPE vmware_datastore_freespace_size gauge
vmware_datastore_freespace_size{ds_name="ESX1-LOCAL"} 66349694976.0
# HELP vmware_datastore_uncommited_size VMWare Datastore uncommitted in bytes
# TYPE vmware_datastore_uncommited_size gauge
vmware_datastore_uncommited_size{ds_name="ESX1-LOCAL"} 0.0
# HELP vmware_datastore_provisoned_size VMWare Datastore provisoned in bytes
# TYPE vmware_datastore_provisoned_size gauge
vmware_datastore_provisoned_size{ds_name="ESX1-LOCAL"} 1027604480.0
# HELP vmware_datastore_hosts VMWare Hosts number using this datastore
# TYPE vmware_datastore_hosts gauge
vmware_datastore_hosts{ds_name="ESX1-LOCAL"} 1.0
# HELP vmware_datastore_vms VMWare Virtual Machines number using this datastore
# TYPE vmware_datastore_vms gauge
vmware_datastore_vms{ds_name="ESX1-LOCAL"} 0.0
# HELP vmware_host_power_state VMWare Host Power state (On / Off)
# TYPE vmware_host_power_state gauge
vmware_host_power_state{host_name="esx1.company.com"} 1.0
# HELP vmware_host_cpu_usage VMWare Host CPU usage in Mhz
# TYPE vmware_host_cpu_usage gauge
vmware_host_cpu_usage{host_name="esx1.company.com"} 2959.0
# HELP vmware_host_cpu_max VMWare Host CPU max availability in Mhz
# TYPE vmware_host_cpu_max gauge
vmware_host_cpu_max{host_name="esx1.company.com"} 28728.0
# HELP vmware_host_memory_usage VMWare Host Memory usage in Mbytes
# TYPE vmware_host_memory_usage gauge
vmware_host_memory_usage{host_name="esx1.company.com"} 107164.0
# HELP vmware_host_memory_max VMWare Host Memory Max availability in Mbytes
# TYPE vmware_host_memory_max gauge
vmware_host_memory_max{host_name="esx1.company.com"} 131059.01953125
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

