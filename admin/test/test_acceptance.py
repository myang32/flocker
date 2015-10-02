# Copyright Hybrid Logic Ltd.  See LICENSE file for details.
"""
Tests for ``admin.acceptance``.
"""

from io import BytesIO
from uuid import UUID

from zope.interface.verify import verifyObject
from twisted.trial.unittest import SynchronousTestCase

from ..acceptance import (
    IClusterRunner, ManagedRunner, generate_certificates,
    journald_json_formatter, DISTRIBUTIONS,
)

from flocker.ca import RootCredential
from flocker.provision import PackageSource
from flocker.provision._install import ManagedNode
from flocker.acceptance.testtools import DatasetBackend


class ManagedRunnerTests(SynchronousTestCase):
    """
    Tests for ``ManagedRunner``.
    """
    def test_interface(self):
        """
        ``ManagedRunner`` provides ``IClusterRunner``.
        """
        runner = ManagedRunner(
            node_addresses=[b'192.0.2.1'],
            package_source=PackageSource(
                version=b"",
                os_version=b"",
                branch=b"",
                build_server=b"",
            ),
            distribution=b'centos-7',
            dataset_backend=DatasetBackend.zfs,
            dataset_backend_configuration={},
        )
        self.assertTrue(
            verifyObject(IClusterRunner, runner)
        )


class GenerateCertificatesTests(SynchronousTestCase):
    """
    Tests for ``generate_certificates``.
    """
    def test_cluster_id(self):
        """
        The certificates generated are for a cluster with the given identifier.
        """
        cluster_id = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
        node = ManagedNode(
            address=b"192.0.2.17", distribution=DISTRIBUTIONS[0],
        )
        certificates = generate_certificates(cluster_id, [node])
        root = RootCredential.from_path(certificates.directory)
        self.assertEqual(
            cluster_id,
            UUID(root.organizational_unit),
        )


JOURNAL_EXPORT = """\
__CURSOR=s=594775da71df472aad0b9e82b11d9b60;i=21eb0be;b=9e3cd98e74c64baf98e890be18b48a51;m=118bd4606ee;t=5211d3d0ee825;x=af65e1fe269327a5
__REALTIME_TIMESTAMP=1443784345708581
__MONOTONIC_TIMESTAMP=1205766325998
_BOOT_ID=9e3cd98e74c64baf98e890be18b48a51
SYSLOG_IDENTIFIER=python
_TRANSPORT=journal
_PID=357
_UID=0
_GID=0
_COMM=flocker-dataset
_EXE=/opt/flocker/bin/python2.7
_CMDLINE=/opt/flocker/bin/python /usr/sbin/flocker-dataset-agent --journald
_CAP_EFFECTIVE=1fffffffff
_SYSTEMD_CGROUP=/system.slice/flocker-dataset-agent.service
_SYSTEMD_UNIT=flocker-dataset-agent.service
_SYSTEMD_SLICE=system.slice
_SELINUX_CONTEXT=system_u:system_r:unconfined_service_t:s0
_MACHINE_ID=e57865069fb84f47b13e9efdda683ea9
_HOSTNAME=some-host-2
MESSAGE={"some": "json"}
_SOURCE_REALTIME_TIMESTAMP=1443784345708225

__CURSOR=s=594775da71df472aad0b9e82b11d9b60;i=21eb0bf;b=9e3cd98e74c64baf98e890be18b48a51;m=118bd46083c;t=5211d3d0ee973;x=7a0d894521d6a41a
__REALTIME_TIMESTAMP=1443784345708915
__MONOTONIC_TIMESTAMP=1205766326332
_BOOT_ID=9e3cd98e74c64baf98e890be18b48a51
SYSLOG_IDENTIFIER=python
_TRANSPORT=journal
_PID=357
_UID=0
_GID=0
_COMM=flocker-contain
_EXE=/opt/flocker/bin/python2.7
_CMDLINE=/opt/flocker/bin/python /usr/sbin/flocker-container-agent --journald
_CAP_EFFECTIVE=1fffffffff
_SYSTEMD_CGROUP=/system.slice/flocker-container-agent.service
_SYSTEMD_UNIT=flocker-container-agent.service
_SYSTEMD_SLICE=system.slice
_SELINUX_CONTEXT=system_u:system_r:unconfined_service_t:s0
_MACHINE_ID=e57865069fb84f47b13e9efdda683ea9
_HOSTNAME=some-host-1
MESSAGE={"other": "values"}
_SOURCE_REALTIME_TIMESTAMP=1443784345708314
"""

class JournaldJSONFormatter(SynchronousTestCase):
    """
    Tests for ``journald_json_formatter``.
    """
    def test_converted(self):
        output = BytesIO()
        converter = journald_json_formatter(output)
        for line in JOURNAL_EXPORT.splitlines():
            converter(line)

        self.assertEqual(
            [dict(
                some="json",
                _HOSTNAME="some-host-2",
                _SYSTEMD_UNIT="flocker-dataset-agent.service",
            ),
             dict(
                 other="values",
                 _HOSTNAME="some-host-1",
                 _SYSTEMD_UNIT="flocker-container-agent.service",
             ),
         ],
            list(loads(line) for line in output.getvalue().splitlines()),
        )
