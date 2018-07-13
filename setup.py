from setuptools import setup
import vmware_exporter

setup(
    name='vmware_exporter',
    version='2.0',
    author='CloudChef',
    description='VMWare VCenter Exporter for Prometheus',
    keywords=['VMWare', 'VCenter', 'Prometheus'],
    packages=['vmware_exporter'],
    include_package_data=True,
    install_requires=open('requirements.txt').readlines()
)
