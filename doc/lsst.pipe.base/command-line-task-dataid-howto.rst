.. _command-line-task-dataid-howto:

###########################################
Specifying data IDs with command-line tasks
###########################################

:ref:`Command-line tasks <using-command-line-tasks>` consume data and output new data products.
You can tell a command-line task exactly what data to process by passing data IDs to the task's :option:`--id` argument.
The task combines the data IDs you provide with the dataset types it expects to retrieve specific datasets for processing with the Butler.

This page describes how to use the :option:`--id` argument to select data for command-line task processing.
This documentation also applies to the :option:`--selectId` argument for many-to-one processing tasks.

.. _command-line-task-dataid-howto-about-dataid-keys:

About data ID keys
==================

Individual data IDs are composed of a set of keys and their values.
The set of keys that are included in a data ID depend on the dataset type and even the observatory package.
The important categories of data IDs are for exposures (generally, individual observations from an observatory) and coadds.

Exposure data IDs are typically described by ``visit`` (unique observation number), ``ccd`` (sensor in camera), ``filter``, ``field``, ``dateObs``, among other keys.
For example, the data ID keys and values for a Hyper Suprime-Cam exposure look like:

.. code-block:: text

   visit=903334 ccd=23 filter=HSC-R field=STRIPE82L pointing=533 dateObs=2013-06-17 taiObs=2016-06-17

Datasets related to coadds are typically described by the coadd's tract and patch location, and filter.
For example:

.. code-block:: text

   filter=HSC-R tract=0 patch=1,1

The following sections describe how to find and select data IDs on the command line.

.. _command-line-task-dataid-howto-show-data:

How to find data IDs available to a command-line task
=====================================================

Given an input Butler data repository at :option:`REPOPATH`, and optionally :ref:`a rerun <command-line-task-data-repo-howto>` given a :option:`--rerun` argument, you can discover available data and their data IDs with the :option:`--show DATA <--show>` command-line task argument:

.. code-block:: bash

   task.py REPOPATH --output output --id --show DATA ...

Each printed line is a data ID, composed of keys and values, for separate datasets.
For example:

.. code-block:: text

   id dataRef.dataId = {'taiObs': '2013-06-17', 'pointing': 533, 'visit': 903334, 'dateObs': '2013-06-17', 'filter': 'HSC-R', 'field': 'STRIPE82L', 'ccd': 23, 'expTime': 30.0}

.. tip::

   Use the :option:`--show DATA <--show>` argument in conjunction with the :option:`--id` argument (more on this below) to confirm what data is being selected.
   Running any command-line task with :option:`--show DATA <--show>` puts the task in a dry-run mode.

.. _command-line-task-dataid-howto-wildcard:

How to specify all available data IDs
=====================================

To process all data available in a Butler data repository (for a task's dataset type), use the :option:`--id` argument without specifying any data ID keys and values:

.. code-block:: bash

   task.py REPOPATH --output output --id

This mode acts like a wildcard glob of all available data IDs.

.. note::

   In general, command-line tasks do not need to work on single datasets.
   If the :option:`--id` argument resolves to multiple datasets, the command-line task will process each dataset as if you ran that command-line task multiple times on each dataset alone.

.. _command-line-task-dataid-howto-kv:

How to filter by data ID key-value pairs on the command line
============================================================

When you pass a data ID key-value pair to :option:`--id`, the command-line task selects datasets for processing that have matching data ID key-value pairs.
For example:

.. code-block:: bash

   task.py REPOPATH --output output --id filter=HSC-R

In this example, only datasets with data IDs that have a ``filter`` key equal to ``HSC-R`` are selected.

You include multiple data ID key-value pairs in the same :option:`--id` argument.
For example:

.. code-block:: bash

   task.py REPOPATH --output output --id filter=HSC-R tract=0

Now only datasets with data IDs that have both a ``filter`` key equal to ``HSR-R`` *and* a ``tract`` key equal to ``0`` are selected.

.. note::

   You generally never need to supply all keys for a data ID to :option:`--id`.
   Instead, think of :option:`--id` as a database query: you only need to include the necessary data ID key-value pairs to pare down the full collection of datasets in a Butler data repository to the ones you want to process with a command-line task.

.. _command-line-task-dataid-howto-or-syntax:

How to specify multiple discrete values (“^” syntax)
====================================================

To include multiple discrete values for a single data ID key, use the ``^`` operator:

.. code-block:: bash

   task.py REPOPATH --output output --id ccd=1^3^5

In this example, datasets are selected that have a ``ccd`` data ID key with values of 1, 3, or 5.

.. _command-line-task-dataid-howto-range-syntax:

How to specify ranges and strides (“..” and “:” syntax)
=======================================================

For data ID key values that are ordered sequences (such as visit numbers or CCD identifiers), you can use ``start..end`` syntax to select the whole range from the given start to the end (inclusive) points.
For example:

.. code-block:: bash

   task.py REPOPATH --output output --id ccd=1..5

In this example, datasets with ``ccd`` data ID keys with values 1, 2, 3, 4, or 5 are selected.

.. important::

   Unlike ranges in Python, both the start and end values are inclusive to the selected range.

You can also *stride* over a range with ``:stride`` syntax.
For example:

.. code-block:: bash

   task.py REPOPATH --output output --id ccd=1..5:2

This example selects datasets that have ``ccd`` data ID keys with values 1, 3, or 5.

Multiple strides can also be concatenated with ``^`` syntax.
For example:

.. code-block:: bash

   task.py REPOPATH --output output --id ccd=1..5^10..15

This example selects datasets that have ``ccd`` data ID keys with values of 1 though 5 and 10 through 15.

.. _command-line-task-dataid-howto-crossproduct:

About multiple values with multiple keys
========================================

If you specify multiple values for multiple data ID keys in a :option:`--id` argument, the cross product of all the key-value pairs is computed.
For example:

.. code-block:: bash

   task.py REPOPATH --output output --id filter=HSC-R visit=100..102 ccd=1^2

From that :option:`--id` argument, this set of data ID key-value pairs is computed:

.. code-block:: text

   filter=HSR-R visit=100 ccd=1
   filter=HSR-R visit=101 ccd=1
   filter=HSR-R visit=102 ccd=1
   filter=HSR-R visit=100 ccd=2
   filter=HSR-R visit=101 ccd=2
   filter=HSR-R visit=102 ccd=2

.. _command-line-task-dataid-howto-multi-arg:

How to use multiple :option:`--id` arguments
============================================

You may use multiple :option:`--id` arguments in the same command-line task invocation.
For each :option:`--id` argument a list of datasets is independently selected, and then these dataset lists are concatenated.
This feature is useful for selecting multiple datasets with more flexibility than the previously mentioned syntax affords.

For example:

.. code-block:: bash

   task.py REPOPATH --output output --id filter=HSC-R ccd=1^2 --id filter=HSC-I ccd=5

From those :option:`--id` arguments, these data ID key-value pairs are computed:

.. code-block:: text

   filter=HSC-R ccd=1
   filter=HSC-R ccd=2
   filter=HSC-I ccd=5

The first two data IDs are produced by the first :option:`--id` argument and the third data ID is produced by the second :option:`--id` argument.
