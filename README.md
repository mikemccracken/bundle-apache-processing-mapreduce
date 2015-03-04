## Overview

This bundle deploys the Apache Hadoop platform in various configurations,
including single-node, single-master, and scalable.

**What is Apache Hadoop?**

The Apache Hadoop software library is a framework that allows for the
distributed processing of large data sets across clusters of computers
using a simple programming model.

It is designed to scale up from single servers to thousands of machines,
each offering local computation and storage. Rather than rely on hardware
to deliver high-avaiability, the library itself is designed to detect
and handle failures at the application layer, so delivering a
highly-availabile service on top of a cluster of computers, each of
which may be prone to failures.

Apache Hadoop 2.4.1 consists of significant improvements over the previous stable
release (hadoop-1.x).

Here is a short overview of the improvments to both HDFS and MapReduce.

 - **HDFS Federation**
   In order to scale the name service horizontally, federation uses multiple
   independent Namenodes/Namespaces. The Namenodes are federated, that is, the
   Namenodes are independent   and don't require coordination with each other.
   The datanodes are used as common storage for blocks by all the Namenodes.
   Each datanode registers with all the Namenodes in the cluster.   Datanodes
   send periodic heartbeats and block reports and handles commands from the
   Namenodes.

   More details are available in the HDFS Federation document:
   <http://hadoop.apache.org/docs/r2.4.1/hadoop-project-dist/hadoop-hdfs/Federation.html>

 - **MapReduce NextGen aka YARN aka MRv2**
   The new architecture introduced in hadoop-0.23, divides the two major functions of the
   JobTracker: resource management and job life-cycle management into separate components.
   The new ResourceManager manages the global assignment of compute resources to
   applications and the per-application ApplicationMaster manages the application‚
   scheduling and coordination.
   An application is either a single job in the sense of classic MapReduce jobs or a DAG of
   such jobs.

   The ResourceManager and per-machine NodeManager daemon, which manages the user
   processes on   that machine, form the computation fabric.

   The per-application ApplicationMaster is, in effect, a framework specific
   library and is tasked with negotiating resources from the ResourceManager and
   working with the NodeManager(s) to execute and monitor the tasks.

   More details are available in the YARN document:
   <http://hadoop.apache.org/docs/r2.4.1/hadoop-yarn/hadoop-yarn-site/YARN.html>


### Recommended Deployment: Separate HDFS, YARN, and compute nodes

In this configuration, the HDFS master, YARN master, compute nodes, and
HDFS SecondaryNameNode are deployed on separate machines.
This gives the most robust deployment, with the best scalability::

    juju deployer -c bundles.yaml scalable

This starts with two compute nodes.  To add additional compute nodes, simply
use `juju add-unit`.  For example, to add two additional compute nodes (bringing
the total to four)::

    juju add-unit compute-slave -n 2


### Dense Deployment: Single master node

This configuration will save a couple of machines by co-locating the HDFS master,
YARN master, and HDFS SecondaryNameNode::

    juju deployer -c bundles.yaml single-master

You can still add units to the compute-slave to scale::

    juju add-unit compute-slave -n 2


### Test and Development Single-Node Deployment

This is In this configuration, all components run on the same machine.  This is **not**
recommended for production use and should only be used for testing or development::

    juju deployer -c bundles.yaml single-node

This configuration cannot scale.


### To deploy a Hadoop service with elasticsearch service::
    # deploy ElasticSearch locally:
    **juju deploy elasticsearch elasticsearch**
    # elasticsearch-hadoop.jar file will be added to LIBJARS path
    # Recommanded to use hadoop -libjars option to included elk jar file
    **juju add-unit -n elasticsearch**
    # deploy hive service by any senarios mentioned above
    # associate Hive with elasticsearch
    **juju add-relation {hadoop master}:elasticsearch elasticsearch:client**


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
[Amir Sanjar](mailto:amir.sanjar@canonical.com)
[Cory Johns](mailto:cory.johns@canonical.com)
[Kevin Monroe](mailto:kevin.monroe@canonical.com)

## Resources
- [Apache Hadoop](http://hadoop.apache.org/) home page
- [Apache Hadoop bug tracker](http://hadoop.apache.org/issue_tracking.html)
- [Apache Hadoop mailing lists](http://hadoop.apache.org/mailing_lists.html)
- [Apache Hadoop Juju Charms](http://jujucharms.com/?text=apache-hadoop)
- [Juju mailing list](https://lists.ubuntu.com/mailman/listinfo/juju)
- [Juju community](https://jujucharms.com/community)

