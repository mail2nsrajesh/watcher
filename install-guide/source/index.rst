===================================
Infrastructure Optimization service
===================================

.. toctree::
   :maxdepth: 2

   get_started.rst
   install.rst
   verify.rst
   next-steps.rst

The Infrastructure Optimization service (watcher) provides
flexible and scalable resource optimization service for
multi-tenant OpenStack-based clouds.

Watcher provides a complete optimization loop including
everything from a metrics receiver, complex event processor
and profiler, optimization processor and an action plan
applier. This provides a robust framework to realize a wide
range of cloud optimization goals, including the reduction
of data center operating costs, increased system performance
via intelligent virtual machine migration, increased energy
efficiency—and more!

watcher also supports a pluggable architecture by which custom
optimization algorithms, data metrics and data profilers can be
developed and inserted into the Watcher framework.

check the documentation for watcher optimization strategies at
https://docs.openstack.org/developer/watcher/strategies

check watcher glossary at
https://docs.openstack.org/developer/watcher/glossary.html


This chapter assumes a working setup of OpenStack following the
`OpenStack Installation Tutorial
<https://docs.openstack.org/project-install-guide/ocata/>`_.
