#!/usr/bin/env python
# -*- python -*-
# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import argparse
import pytz
import ssl
import sys
import json
import base64
import logging
import requests
import copy
from Crypto.Cipher import AES

from datetime import datetime
import multiprocessing
from multiprocessing import Process

# Twisted
from twisted.web.server import Site, NOT_DONE_YET
from twisted.web.resource import Resource
from twisted.internet import reactor
from twisted.internet.task import deferLater

# VMWare specific imports
import pyVmomi
from pyVmomi import vim, vmodl
from pyVim import connect

# Prometheus specific imports
from prometheus_client.core import GaugeMetricFamily, _floatToGoString
import pchelper
import constants


class VMWareMetricsResource(Resource):
    """
    VMWare twisted ``Resource`` handling multi endpoints
    Only handle /metrics and /healthz path
    """
    isLeaf = True

    def __init__(self, args):
        self.consul_url = 'http://' + args.consul_url

    def get_vmwares(self):
        vmwares = dict()
        try:
            request_vmware_url = self.consul_url + constants.vmware_cloudentry_path
            logger.info('Begin to obtain message of vmwares from consul.')
            vmware_results = json.loads(
                requests.get(request_vmware_url).text)
            logger.info('Finished obtaining message of vmwares '
                        'from consul with data: {}'.format(vmware_results))
            for result in vmware_results:
                value_encoded = result.get('Value')
                if not value_encoded:
                    logger.warn('Get empty value from consul with key {}.'.format(
                        result.get('Key')))
                    continue
                value = json.loads(base64.b64decode(value_encoded))
                if value.get('status') != "RUNNING":
                    continue
                value['password'] = self.decrypt_password(value['password'])
                key = '_'.join([value['host'], value['username']])
                if vmwares.get(key):
                    vmwares[key].append(value)
                else:
                    vmwares[key] = [value]
            return vmwares
        except Exception as e:
            logger.error(
                'Get vmware message from consul failed: {}'.format(e.message))
            return vmwares

    def get_vms(self, cloud_entry_ids):
        try:
            vms = dict()
            request_vm_url = self.consul_url + constants.vmware_vms_path
            logger.info('Begin to obtain message of vms from consul.')
            vm_results = json.loads(
                requests.get(request_vm_url).text)
            logger.info('Finished obtaining message of vms '
                        'from consul with data length: {}'.format(len(vm_results)))
            for result in vm_results:
                if result['Value']:
                    value = json.loads(base64.b64decode(result['Value']))
                    if value.get('monitor_source_type') == 'hypervisor' \
                            and value.get('cloud_entry_id') in cloud_entry_ids:
                        vms[value['external_id']] = value
            return vms
        except Exception as e:
            logger.error("Get vms from consul failed: {}".format(e.message))
            return vms

    def decrypt_password(self, password):
        if not password:
            return None

        def unpad(s): return s[0:-ord(s[-1])]
        key = "keepsecret"
        cipher = AES.new(key)
        decrypted = unpad(cipher.decrypt(password.decode('hex')))
        return decrypted

    def render_GET(self, request):
        path = request.path.decode()
        request.setHeader("Content-Type", "text/plain; charset=UTF-8")
        if path == '/metrics':
            d = deferLater(reactor, 0, lambda: request)
            d.addCallback(self.concurrent_request)
            d.addErrback(self.errback, request)
            return NOT_DONE_YET
        elif path == '/healthz':
            request.setResponseCode(200)
            return 'Server is UP'.encode()
        else:
            request.setResponseCode(404)
            return '404 Not Found'.encode()

    def errback(self, failure, request):
        failure.printTraceback()
        request.processingFailed(failure)
        return None

    def concurrent_request(self, request):
        manager = multiprocessing.Manager()
        return_dict = manager.dict()
        vmwares = self.get_vmwares()
        for key in vmwares.keys():
            vmware = vmwares[key][0]
            si = self._vmware_connect(vmware)
            if not si:
                logger.error(
                    'Connect to vmware {} failed.'.format(vmware['host']))
                print("Error, connect to vmware {} failed.".format(
                    vmware['host']))
                continue
            target = vmware['host']
            cloud_entry_ids = []
            for value in vmwares[key]:
                cloud_entry_ids.append(value['cloud_entry_id'])
            process = Process(target=self.generate_latest_target,
                              args=(si, key, cloud_entry_ids, target, return_dict))
            process.start()
            process.join()

        result = []
        for key in return_dict.keys():
            result.extend(return_dict[key])
        if result != []:
            request.write(''.join(result).encode('utf-8'))
        request.finish()

    def _generate_output_text(self, metric):
        lines = []
        lines.append('# HELP {0} {1}'.format(
            metric.name, metric.documentation.replace('\\', r'\\').replace('\n', r'\n')))
        lines.append('\n# TYPE {0} {1}\n'.format(metric.name, metric.type))

        for name, labels, value in metric.samples:
            labelstr = ''
            if labels:
                labelstr = '{{{0}}}'.format(','.join(
                    ['{0}="{1}"'.format(
                        k, v.replace('\\', r'\\').replace('\n', r'\n').replace('"', r'\"'))
                     for k, v in sorted(labels.items())]))
            lines.append('{0}{1} {2}\n'.format(
                name, labelstr, _floatToGoString(value)))
        return lines

    def generate_latest_target(self, si, key, cloud_entry_ids, target, return_dict):
        output = []
        for metric in self.collect(si, cloud_entry_ids, target):
            text_lines = self._generate_output_text(metric)
            if text_lines:
                output.extend(text_lines)

        if output != []:
            return_dict[key] = output

    def collect(self, si, cloud_entry_ids, target):
        metric_list = constants.metric_list
        metrics = {}
        for key in metric_list.keys():
            metrics.update(metric_list[key])
        self.metrics = metrics

        logger.info("[{0}] [PID-{1}] Start collecting vcenter metrics for {2}".format(
            datetime.utcnow().replace(tzinfo=pytz.utc), os.getpid(), target))
        print("[{0}] [PID-{1}] Start collecting vcenter metrics for {2}".format(
            datetime.utcnow().replace(tzinfo=pytz.utc), os.getpid(), target))

        obj_types = {
            vim.VirtualMachine: constants.vm_properties,
            vim.HostSystem: constants.host_properties,
            vim.Datastore: constants.data_properties
        }

        for obj_type, properties in obj_types.items():
            view = self.get_container_view(si, obj_type=[obj_type])

            data = []
            if obj_type is vim.VirtualMachine:
                consul_vms = self.get_vms(cloud_entry_ids)
                if consul_vms:
                    data = pchelper.collect_properties(si, view_ref=view,
                                                       obj_type=obj_type,
                                                       path_set=properties,
                                                       include_mors=True,
                                                       vms=consul_vms)
            else:
                data = pchelper.collect_properties(si, view_ref=view,
                                                   obj_type=obj_type,
                                                   path_set=properties,
                                                   include_mors=True)

            if obj_type is vim.HostSystem:
                self._vmware_get_hosts(cloud_entry_ids, data)
            elif obj_type is vim.VirtualMachine:
                vm_counts, vm_ages = self._vmware_get_snapshots(data)
                self._vmware_get_vms(consul_vms, data)
            elif obj_type is vim.Datastore:
                self._vmware_get_datastores(cloud_entry_ids, data)

        vm_labels = constants.vm_labels
        sscount_metric_name = 'vmware_vm_snapshots'
        sstime_metric_name = 'vmware_vm_snapshot_timestamp_seconds'
        for v in vm_counts:
            label_values = []
            v_id = v['vm_id']
            consul_vm = consul_vms.get(v_id)
            for label in vm_labels:
                label_value = ''
                if label == 'server_type':
                    vm_value = consul_vm.get('resource_type', '')
                else:
                    vm_value = consul_vm.get(label, '')
                if vm_value:
                    label_value = vm_value
                if isinstance(label_value, list):
                    label_value = ','.join(str(e) for e in label_value)
                label_values.append(label_value)
            snapshot_count = v['snapshot_count']
            self.metrics[sscount_metric_name].add_metric(
                label_values, snapshot_count)

        for k in vm_ages:
            label_values = []
            consul_vm = consul_vms.get(k)
            for label in vm_labels:
                label_value = ''
                if label == 'server_type':
                    vm_value = consul_vm.get('resource_type', '')
                else:
                    vm_value = consul_vm.get(label, '')
                if vm_value:
                    label_value = vm_value
                if isinstance(label_value, list):
                    label_value = ','.join(str(e) for e in label_value)
                label_values.append(label_value)
            for v in vm_ages[k]:
                vm_snapshot_name = v['vm_snapshot_name'] if v['vm_snapshot_name'] else ''
                vm_snapshot_time = v['vm_snapshot_timestamp_seconds']
                self.metrics[sstime_metric_name].add_metric(label_values + [vm_snapshot_name],
                                                            vm_snapshot_time)

        logger.info("[{0}] [PID-{1}] Stop collecting vcenter metrics for {2}".format(
            datetime.utcnow().replace(tzinfo=pytz.utc), os.getpid(), target))
        print("[{0}] [PID-{1}] Stop collecting vcenter metrics for {2}".format(
            datetime.utcnow().replace(tzinfo=pytz.utc), os.getpid(), target))

        self._vmware_disconnect(si)

        for _, metric in self.metrics.items():
            yield metric

    def get_container_view(self, si, obj_type, container=None):
        if not container:
            container = si.content.rootFolder

        view_ref = si.content.viewManager.CreateContainerView(
            container=container,
            type=obj_type,
            recursive=True
        )
        return view_ref

    def _to_unix_timestamp(self, my_date):
        return ((my_date - datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds())

    def _vmware_connect(self, vmware, ignore_ssl=True):
        """
        Connect to Vcenter and get connection
        """
        context = None
        if ignore_ssl and hasattr(ssl, "_create_unverified_context"):
            context = ssl._create_unverified_context()

        try:
            logger.info(
                '[PID-{0}] Begin connecting to vmware {1}'.format(os.getpid(), vmware['host']))
            si = connect.Connect(vmware['host'],
                                 443,
                                 vmware['username'],
                                 vmware['password'],
                                 sslContext=context)
            logger.info(
                '[PID-{0}] Connect to vmware {1} successfully.'.format(os.getpid(), vmware['host']))
            return si
        except Exception as e:
            if isinstance(e, vmodl.MethodFault):
                logger.error(
                    "[PID-{0}] Caught vmodl fault when connect to vmware: {1}".format(os.getpid(), e.message))
            else:
                logger.error('[PID-{0}] Connection to vmware {1} failed: {2}'.format(
                    os.getpid(), vmware['host'], e.message))
            return None

    def _vmware_disconnect(self, si):
        """
        Disconnect from Vcenter
        """
        connect.Disconnect(si)

    def _vmware_list_snapshots_recursively(self, snapshots, vm):
        """
        Get snapshots from a VM list, recursively
        """
        snapshot_data = []
        for snapshot in snapshots:
            snap_timestamp = self._to_unix_timestamp(snapshot.createTime)
            snap_info = {
                'vm_id': str(vm["summary.vm"]).replace("'", "").split(":")[1],
                'vm_snapshot_name': vm["name"],
                'vm_snapshot_timestamp_seconds': snap_timestamp
            }
            snapshot_data.append(snap_info)
            snapshot_data += self._vmware_list_snapshots_recursively(
                snapshot.childSnapshotList, vm)
        return snapshot_data

    def _vmware_get_snapshots(self, data):
        """
        Get snapshots from all VM
        """
        snapshots_count_table = []
        snapshots_age_table = dict()

        for vm in data:
            if not vm or "snapshot" not in vm.keys():
                continue

            vm_id = vm['summary.vm']._moId

            snapshot_paths = self._vmware_list_snapshots_recursively(
                vm["snapshot.rootSnapshotList"], vm)
            for sn in snapshot_paths:
                sn['vm_name'] = vm["name"]
            # Add Snapshot count per VM
            snapshot_count = len(snapshot_paths)
            snapshot_count_info = {
                'vm_name': vm["name"],
                'vm_id': vm_id,
                'snapshot_count': snapshot_count
            }
            snapshots_count_table.append(snapshot_count_info)
            snapshots_age_table[vm_id] = snapshot_paths
        return snapshots_count_table, snapshots_age_table

    def _vmware_get_datastores(self, cloud_entry_ids, data):
        """
        Get Datastore information
        """
        for ds in data:
            # ds.RefreshDatastoreStorageInfo()
            ds_capacity = ds["summary.capacity"]
            ds_freespace = ds["summary.freeSpace"]
            if "summary.uncommitted" in ds.keys():
                ds_uncommitted = ds["summary.uncommitted"] if ds["summary.uncommitted"] else 0
            else:
                ds_uncommitted = 0
            ds_provisioned = ds_capacity - ds_freespace + ds_uncommitted
            datastore_id = str(ds["summary.datastore"]).replace(
                "'", "").split(":")[1]
            host_id = []
            for host in ds['host']:
                host_id.append(host.key._moId)
            host_id = ','.join(host_id)

            for cloud_entry_id in cloud_entry_ids:
                self.metrics['vmware_datastore_capacity_size'].add_metric(
                    [cloud_entry_id, ds["summary.name"], datastore_id, host_id], ds_capacity)
                self.metrics['vmware_datastore_freespace_size'].add_metric(
                    [cloud_entry_id, ds["summary.name"], datastore_id, host_id], ds_freespace)
                self.metrics['vmware_datastore_uncommited_size'].add_metric(
                    [cloud_entry_id, ds["summary.name"], datastore_id, host_id], ds_uncommitted)
                self.metrics['vmware_datastore_provisoned_size'].add_metric(
                    [cloud_entry_id, ds["summary.name"], datastore_id, host_id], ds_provisioned)
                self.metrics['vmware_datastore_hosts'].add_metric(
                    [cloud_entry_id, ds["summary.name"], datastore_id], len(ds["host"]))
                self.metrics['vmware_datastore_vms'].add_metric(
                    [cloud_entry_id, ds["summary.name"], datastore_id], len(ds["vm"]))

    def _vmware_get_vms(self, consul_vms, data):
        """
        Get VM information
        """
        perf_labels = constants.perf_labels
        vm_labels = constants.vm_labels
        for key in perf_labels.keys():
            self.metrics[key] = GaugeMetricFamily(key, key,
                                                  labels=vm_labels)

        for vm in data:
            power_state = 1 if vm['summary.runtime.powerState'] == 'poweredOn' else 0
            consul_vm = consul_vms.get(vm['summary.vm']._moId)
            label_values = []
            for label in vm_labels:
                if label == 'server_type':
                    label_value = consul_vm.get('resource_type', '')
                else:
                    label_value = consul_vm.get(label, "")
                if isinstance(label_value, list):
                    label_value = ','.join(str(e) for e in label_value)
                label_values.append(label_value if label_value else '')
            self.metrics['vmware_vm_power_state'].add_metric(
                label_values, power_state)

            if 'summary.config.numCpu' in vm:
                num_cpu = vm['summary.config.numCpu']
                self.metrics['vmware_vm_num_cpu'].add_metric(
                    label_values, num_cpu)

            if power_state:
                boot_time = vm.get('summary.runtime.bootTime')
                if boot_time:
                    value = self._to_unix_timestamp(boot_time)
                    self.metrics['vmware_vm_boot_timestamp_seconds'].add_metric(
                        label_values, value)
                disk_infoes = vm.get('guest.disk')
                if disk_infoes:
                    for i in range(len(disk_infoes)):
                        capacity = float(disk_infoes[i].capacity)
                        free_space = float(disk_infoes[i].freeSpace)
                        disk_path = disk_infoes[i].diskPath
                        capacity_key = 'vmware_vm_guest_disk_capacity_0' + \
                            str(i)
                        free_space_key = 'vmware_vm_guest_disk_free_space_0' + \
                            str(i)
                        disk_values = copy.copy(label_values)
                        disk_values.append(disk_path if disk_path else '')

                        self.metrics[capacity_key] = GaugeMetricFamily(capacity_key,
                                                                       capacity_key,
                                                                       labels=vm_labels + ['disk_path'])
                        self.metrics[free_space_key] = GaugeMetricFamily(free_space_key,
                                                                         free_space_key,
                                                                         labels=vm_labels + ['disk_path'])
                        self.metrics[capacity_key].add_metric(
                            disk_values, capacity)
                        self.metrics[free_space_key].add_metric(
                            disk_values, free_space)

                for k, v in perf_labels.items():
                    if not v:
                        committed = vm['summary.storage.committed']
                        uncommitted = vm['summary.storage.uncommitted']
                        value = float(committed + uncommitted)
                        self.metrics[k].add_metric(label_values, value)
                    else:
                        value = float(vm.get(v, 0))
                        self.metrics[k].add_metric(label_values, value)

    def _vmware_get_hosts(self, cloud_entry_ids, data):
        """
        Get Host (ESXi) information
        """
        for host in data:
            # Power state
            for cloud_entry_id in cloud_entry_ids:
                power_state = 1 if host["summary.runtime.powerState"] == 'poweredOn' else 0
                host_id = host['summary.host']._moId
                host_name = host['name']

                self.metrics['vmware_host_power_state'].add_metric(
                    [cloud_entry_id, host_name, host_id], power_state)

                if power_state:
                    # Uptime
                    if host["summary.runtime.bootTime"]:
                        boot_time = self._to_unix_timestamp(
                            host["summary.runtime.bootTime"])
                        self.metrics['vmware_host_boot_timestamp_seconds'].add_metric(
                            [cloud_entry_id, host_name, host_id], boot_time)

                    # CPU Usage (in Mhz)
                    cpu_usage = host["summary.quickStats.overallCpuUsage"]
                    self.metrics['vmware_host_cpu_usage'].add_metric(
                        [cloud_entry_id, host_name, host_id], cpu_usage)

                    cpu_core_num = host["summary.hardware.numCpuCores"]
                    cpu_total = host["summary.hardware.cpuMhz"] * cpu_core_num
                    self.metrics['vmware_host_cpu_max'].add_metric(
                        [cloud_entry_id, host_name, host_id], cpu_total)

                    # Memory Usage (in Mhz)
                    memory_usage = host["summary.quickStats.overallMemoryUsage"]
                    self.metrics['vmware_host_memory_usage'].add_metric(
                        [cloud_entry_id, host_name, host_id], memory_usage)

                    memory_max = float(
                        host["summary.hardware.memorySize"]) / 1024 / 1024
                    self.metrics['vmware_host_memory_max'].add_metric(
                        [cloud_entry_id, host_name, host_id], memory_max)


def main():
    parser = argparse.ArgumentParser(
        description='VMWare metrics exporter for Prometheus')
    parser.add_argument('-c', '--consul_url', dest='consul_url',
                        default='127.0.0.1:8500', help="Url to connect consul")
    parser.add_argument('-p', '--port', dest='port', type=int,
                        default=9272, help="HTTP port to expose metrics")

    args = parser.parse_args()

    # Start up the server to expose the metrics.
    root = Resource()
    root.putChild(b'metrics', VMWareMetricsResource(args))
    root.putChild(b'healthz', VMWareMetricsResource(args))

    factory = Site(root)
    logger.info("Starting web server on port {}".format(args.port))
    print("Starting web server on port {}".format(args.port))
    reactor.listenTCP(args.port, factory)
    reactor.run()


if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8')

    log_path = constants.log_path
    (dir_path, log_file) = os.path.split(log_path)
    if not os.path.exists(dir_path):
        os.system('mkdir ' + dir_path)

    logger = logging.getLogger(constants.APP_NAME)
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_path)
    formatter = logging.Formatter('%(asctime)s - %(name)s '
                                  '- %(levelname)s - %(message)s')
    logger = logging.getLogger(constants.APP_NAME)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    main()
