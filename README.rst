

Lambda Perf Testing
=======================================

This is a fork of the following repos: https://github.com/epsagon/lambda-memory-performance-benchmark

Changes
-----
    * Removed the payload flag on the function.
    * Created multiple payload files of varied sizes (sm, md, lg).
    * Allowed it to iterate through all payloads into a merged csv file.
    * Removed alot of the console logging and just use the output results.csv file.
    * Removed unnessisary test serverless file.
    * Updating pricing to ireland/london values.



Setup
-----
.. code-block:: bash

    git clone git@github.com:lewisstevens1/lambda-perf-testing.git
    cd lambda-perf-testing/
    pip install -r requirements.txt
    python benchmark.py -f <function_name> -r <function_region> [--profile=<profile_name>]


Usage
-----

Basic run:

.. code-block:: bash

    python benchmark.py -f name-of-lambda -r eu-west-2


Export Example
--------------------------------

Chart:

.. image:: https://github.com/lewisstevens1/lambda-perf-testing/blob/master/fibonacci-function/performance_chart.png
