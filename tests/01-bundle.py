#!/usr/bin/env python3

import os
import re
import unittest

import yaml
import amulet


class TestBundle(unittest.TestCase):
    bundle_file = os.path.join(os.path.dirname(__file__), '..', 'bundle-local.yaml')

    @classmethod
    def setUpClass(cls):
        # classmethod inheritance doesn't work quite right with
        # setUpClass / tearDownClass, so subclasses have to manually call this
        cls.d = amulet.Deployment(series='trusty')
        with open(cls.bundle_file) as f:
            bun = f.read()
        bundle = yaml.safe_load(bun)
        cls.d.load(bundle)
        cls.d.setup(timeout=1800)
        cls.d.sentry.wait_for_messages({
            'plugin': 'Ready (HDFS & YARN)',
            'namenode': [
                'Ready (3 DataNodes, HA active, with automatic fail-over)',
                'Ready (3 DataNodes, HA standby, with automatic fail-over)',
            ]
        }, timeout=1800)
        for unit_name, unit_status in cls.d.sentry.get_status()['namenode'].items():
            if 'active' in unit_status['workload-status']['message']:
                cls.hdfs_active = cls.d.sentry.unit[unit_name]
            else:
                cls.hdfs_standby = cls.d.sentry.unit[unit_name]
        cls.yarn = cls.d.sentry['resourcemanager'][0]
        cls.slaves = cls.d.sentry['slave']
        cls.client = cls.d.sentry['client'][0]
        cls.plugins = cls.d.sentry['plugin']

    def test_components(self):
        """
        Confirm that all of the required components are up and running.
        """
        hdfs, retcode = self.hdfs_active.run("pgrep -a java")
        yarn, retcode = self.yarn.run("pgrep -a java")
        slave, retcode = self.slaves[0].run("pgrep -a java")
        client, retcode = self.client.run("pgrep -a java")

        # .NameNode needs the . to differentiate it from SecondaryNameNode
        assert '.NameNode' in hdfs, "NameNode not started"
        assert '.NameNode' not in yarn, "NameNode should not be running on resourcemanager"
        assert '.NameNode' not in slave, "NameNode should not be running on slave"
        assert '.NameNode' not in client, "NameNode should not be running on client"

        assert 'ResourceManager' in yarn, "ResourceManager not started"
        assert 'ResourceManager' not in hdfs, "ResourceManager should not be running on namenode"
        assert 'ResourceManager' not in slave, "ResourceManager should not be running on slave"
        assert 'ResourceManager' not in client, "ResourceManager should not be running on client"

        assert 'JobHistoryServer' in yarn, "JobHistoryServer not started"
        assert 'JobHistoryServer' not in hdfs, "JobHistoryServer should not be running on namenode"
        assert 'JobHistoryServer' not in slave, "JobHistoryServer should not be running on slave"
        assert 'JobHistoryServer' not in client, "JobHistoryServer should not be running on client"

        assert 'NodeManager' in slave, "NodeManager not started"
        assert 'NodeManager' not in yarn, "NodeManager should not be running on resourcemanager"
        assert 'NodeManager' not in hdfs, "NodeManager should not be running on namenode"
        assert 'NodeManager' not in client, "NodeManager should not be running on client"

        assert 'DataNode' in slave, "DataServer not started"
        assert 'DataNode' not in yarn, "DataNode should not be running on resourcemanager"
        assert 'DataNode' not in hdfs, "DataNode should not be running on namenode"
        assert 'DataNode' not in client, "DataNode should not be running on client"

    def test_hdfs_dir(self):
        """
        Validate admin few hadoop activities on HDFS cluster.
            1) This test validates mkdir on hdfs cluster
            2) This test validates change hdfs dir owner on the cluster
            3) This test validates setting hdfs directory access permission on the cluster

        NB: These are order-dependent, so must be done as part of a single test case.
        """
        output, retcode = self.client.run("su hdfs -c 'hdfs dfs -mkdir -p /user/ubuntu'")
        assert retcode == 0, "Created a user directory on hdfs FAILED:\n{}".format(output)
        output, retcode = self.client.run("su hdfs -c 'hdfs dfs -chown ubuntu:ubuntu /user/ubuntu'")
        assert retcode == 0, "Assigning an owner to hdfs directory FAILED:\n{}".format(output)
        output, retcode = self.client.run("su hdfs -c 'hdfs dfs -chmod -R 755 /user/ubuntu'")
        assert retcode == 0, "seting directory permission on hdfs FAILED:\n{}".format(output)

    def test_yarn_mapreduce_exe(self):
        """
        Validate yarn mapreduce operations:
            1) validate mapreduce execution - writing to hdfs
            2) validate successful mapreduce operation after the execution
            3) validate mapreduce execution - reading and writing to hdfs
            4) validate successful mapreduce operation after the execution
            5) validate successful deletion of mapreduce operation result from hdfs

        NB: These are order-dependent, so must be done as part of a single test case.
        """
        jar_file = '/usr/lib/hadoop/share/hadoop/mapreduce/hadoop-mapreduce-examples-*.jar'
        tests_jar_file = '/usr/lib/hadoop/share/hadoop/common/hadoop-common-*-tests.jar'

        test_steps = [
            ('teragen',      "su ubuntu -c 'hadoop jar {} teragen  10000 /user/ubuntu/teragenout'".format(jar_file)),
            ('mapreduce #1', "su hdfs -c 'hdfs dfs -ls /user/ubuntu/teragenout/_SUCCESS'"),
            ('terasort',     "su ubuntu -c 'hadoop jar {} terasort /user/ubuntu/teragenout /user/ubuntu/terasortout'".
                format(jar_file)),
            ('mapreduce #2', "su hdfs -c 'hdfs dfs -ls /user/ubuntu/terasortout/_SUCCESS'"),
            ('test lzo', "su ubuntu -c 'hadoop jar {} org.apache.hadoop.io.TestSequenceFile -seed 0 \
                -count 1000 -compressType RECORD xxx -codec org.apache.hadoop.io.compress.LzoCodec \
                -check'".format(tests_jar_file)),
            ('cleanup #1',   "su hdfs -c 'hdfs dfs -rm -r /user/ubuntu/teragenout'"),
            ('cleanup #2',   "su hdfs -c 'hdfs dfs -rm -r /user/ubuntu/terasortout'"),
        ]
        for name, step in test_steps:
            output, retcode = self.client.run(step)
            assert retcode == 0, "{} FAILED:\n{}".format(name, output)

    def _hdfs_write_file(self):
        test_steps = [
            ('create_file', "su ubuntu -c 'echo test-file-contents > /tmp/testfile'"),
            ('write_file',  "su ubuntu -c 'hdfs dfs -put /tmp/testfile'"),
        ]
        for name, step in test_steps:
            output, retcode = self.client.run(step)
            assert retcode == 0, "{} FAILED:\n{}".format(name, output)

    def _hdfs_read_file(self):
        output, retcode = self.client.run("su ubuntu -c 'hdfs dfs -cat testfile'")
        assert retcode == 0, "HDFS READ FILE FAILED ({}): {}".format(retcode, output)
        self.assertIn('test-file-contents', output)

    def test_create_file(self):
        self._hdfs_write_file()
        self._hdfs_read_file()

    def _do(self, unit, action):
        unit_name = unit.info['unit_name']
        action_id = self.d.action_do(unit_name, action)
        return self.d.action_fetch(action_id)  # wait for action to complete
        # Bug in amulet: if an action doesn't set any values, there's no
        # way to detect success / failure / timeout.  Even if it does set
        # a value, there's no way to distinguish action failure from timeout.

    def test_failover(self):
        """
        Confirm that automatic fail-over is working for the NameNode.
        """
        self._do(self.hdfs_active, 'stop-namenode')
        self.d.sentry.wait_for_messages({
            'namenode': [
                'Ready (3 DataNodes, HA degraded down (missing: standby), with automatic fail-over)',
                'Ready (3 DataNodes, HA degraded active (missing: standby), with automatic fail-over)',
            ]
        }, timeout=1800)
        self._hdfs_read_file()
        self._do(self.hdfs_active, 'start-namenode')
        self.d.sentry.wait_for_messages({
            'namenode': [
                'Ready (3 DataNodes, HA active, with automatic fail-over)',
                'Ready (3 DataNodes, HA standby, with automatic fail-over)',
            ]
        }, timeout=1800)
        (self.hdfs_active, self.hdfs_standby) = (self.hdfs_standby, self.hdfs_active)
        self._hdfs_read_file()

    def test_upgrade(self):
        for service in ('namenode', 'resourcemanager', 'slave', 'plugin'):
            # the newest supported version is the default, so test by
            # "upgrading" to a lower version
            self.d.configure(service, {'hadoop_version': '2.7.1'})
        self._do(self.hdfs_active, 'prepare-upgrade')
        try:
            # wait for upgrade image to complete
            for i in amulet.helpers.timeout_gen(5*60):
                if yaml.load(self._do(self.hdfs_active, 'query').get('ready', 'false')):
                    break
        except amulet.helpers.TimeoutError:
            self.fail('Timed out waiting for upgrade image')
        self._do(self.hdfs_standby, 'upgrade')
        self._do(self.hdfs_active, 'upgrade')
        self._do(self.yarn, 'upgrade')
        for plugin in self.plugins:
            self._do(plugin, 'upgrade')
        self._do(self.slaves[0], 'upgrade')
        self._do(self.slaves[1], 'upgrade')
        # skip third slave to test partial upgrade
        self.d.sentry.wait_for_messages({
            'namenode': [
                'Ready (3 DataNodes, HA active, with automatic fail-over)',
                'Ready (3 DataNodes, HA standby, with automatic fail-over)',
            ],
            'resourcemanager': 'Ready (3 NodeManagers)',
            'plugin': 'Ready (HDFS & YARN)',
            'slave': [
                'Ready (DataNode & NodeManager)',
                'Ready (DataNode & NodeManager)',
                re.compile(r"Spec mismatch with (NameNode|ResourceManager): "
                           "{'hadoop': '2.7.2'}"
                           " != "
                           "{'hadoop': '2.7.1'}"),
            ],
        }, timeout=1800)
        # finish upgrade
        self._do(self.slaves[2], 'upgrade')
        self.d.sentry.wait_for_messages({
            'slave': 'Ready (DataNode & NodeManager)',
        }, timeout=1800)
        # test downgrade on plugin
        self.d.configure('plugin', {'hadoop_version': '2.7.2'})
        self._do(self.plugins[0], 'downgrade')  # revert back to original version
        self.d.sentry.wait_for_messages({
            'plugin': {re.compile(r"Spec mismatch with (NameNode|ResourceManager): "
                                  "{'hadoop': '2.7.2'}"
                                  " != "
                                  "{'hadoop': '2.7.1'}")},
        }, timeout=1800)
        # re-upgrade plugin
        self.d.configure('plugin', {'hadoop_version': '2.7.1'})
        self._do(self.plugins[0], 'downgrade')  # revert back to new version
        self.d.sentry.wait_for_messages({
            'plugin': 'Ready (HDFS & YARN)',
        }, timeout=1800)
        self._do(self.hdfs_active, 'finalize')
        self._hdfs_read_file()


if __name__ == '__main__':
    unittest.main()
