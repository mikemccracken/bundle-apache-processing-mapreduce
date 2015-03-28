## Overview

The Apache Hadoop software library is a framework that allows for the
distributed processing of large data sets across clusters of computers
using a simple programming model.

It is designed to scale up from single servers to thousands of machines,
each offering local computation and storage. Rather than rely on hardware
to deliver high-avaiability, the library itself is designed to detect
and handle failures at the application layer, so delivering a
highly-availabile service on top of a cluster of computers, each of
which may be prone to failures.

This bundle provides a complete deployment of the core components of the
[Apache Hadoop 2.4.1](http://hadoop.apache.org/docs/r2.4.1/)
platform to perform distributed data analytics at scale.  Deploying this
bundle gives you a fully configured and connected Apache Hadoop cluster
on any supported cloud, which can be easily scaled to meet workload demands.


## Deploying this bundle

In this deployment, the HDFS master, YARN master, compute nodes, and
HDFS SecondaryNameNode are deployed on separate machines.

    juju quickstart apache-core-batch-processing

This starts with two compute nodes.  To add additional compute nodes, simply
use `juju add-unit`.  For example, to add two additional compute nodes (bringing
the total to four):

    juju add-unit compute-slave -n 2


## Deploying in Network-Restricted Environments

The Apache Hadoop charms can be deployed in environments with limited network
access. To deploy in this environment, you will need a local mirror to serve
the packages and resources required by these charms.

### Mirroring Packages

You can setup a local mirror for apt packages using squid-deb-proxy.
For instructions on configuring juju to use this, see the
[Juju Proxy Documentation](https://juju.ubuntu.com/docs/howto-proxies.html).

### Mirroring Resources

In addition to apt packages, the Apache Hadoop charms require a few binary
resources, which are normally hosted on Launchpad. If access to Launchpad
is not available, the `jujuresources` library makes it easy to create a mirror
of these resources:

    sudo pip install jujuresources
    juju resources fetch --all apache-hadoop-client/resources.yaml -d /tmp/resources
    juju resources serve -d /tmp/resources

This will fetch all of the resources needed by this charm and serve them via a
simple HTTP server. You can then set the `resources_mirror` config option to
have the charm use this server for retrieving resources.

You can fetch the resources for all of the Apache Hadoop charms
(`apache-hadoop-hdfs-master`, `apache-hadoop-yarn-master`,
`apache-hadoop-compute-slave`, `apache-hadoop-client`, etc) into a single
directory and serve them all with a single `juju resources serve` instance.

## Contact Information

[bigdata-dev@canonical.com](mailto:bigdata-dev@canonical.com)


## Resources
- [Apache Hadoop](http://hadoop.apache.org/) home page
- [Apache Hadoop bug tracker](http://hadoop.apache.org/issue_tracking.html)
- [Apache Hadoop mailing lists](http://hadoop.apache.org/mailing_lists.html)
- [Apache Hadoop Juju Charms](http://jujucharms.com/?text=apache-hadoop)
- [Juju mailing list](https://lists.ubuntu.com/mailman/listinfo/juju)
- [Juju community](https://jujucharms.com/community)

