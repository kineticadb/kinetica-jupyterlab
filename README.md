# Kinetica JupyterLab Test Environment

## Overview

This repository contains an integrated environment that integrates CentOS 7, Kinetica, [JupyterLab][JUPYTERLAB],
and Python 3.6 for the purpose of accelerating development of ML Models that leverage Kinetica.

It has the following Python 3.6 libraries for integrating ML libraries with Kinetica:

* [Kinetica Python API](https://www.kinetica.com/docs/6.2/tutorials/python_guide.html)
* [Kinetica UDF API](https://www.kinetica.com/docs/6.2/udf/python/writing.html)
* [PyODBC](https://github.com/mkleehammer/pyodbc/wiki/Getting-started)

It also has the following libraries for ML model development:

* [Pandas](http://pandas.pydata.org/pandas-docs/stable/dsintro.html)
* [PyTorch](https://jhui.github.io/2018/02/09/PyTorch-Basic-operations)
* [SciPy](https://docs.scipy.org/doc/scipy/reference)
* [SkLearn](http://scikit-learn.org/stable/documentation.html)
* [MatPlotLib](https://matplotlib.org/contents.html)
* [TensorFlow](https://www.tensorflow.org/tutorials)

Example Notebooks are provided that demonstrate:

 * Connectivity between Pandas Dataframes and Kinetica with ODBC and the native API.
 * ML models including an SVD recommender.

[JUPYTERLAB]: <http://jupyterlab.readthedocs.io/en/stable>

*Important: The Kinetica Intel build does not give GPU accelerated performance and should be used for
development purposes only.*

## Mounted volumes

| Host Location | Mount point |
| :--- | :--- |
| `kinetica-jupyterlab/notebooks` | `/opt/notebooks` |
| `kinetica-jupyterlab/docker/share` | `/opt/share` |

The `notebooks` mount contains the directory JupyterLab will be the home directory when it starts up.
The `share` directory contains configuration and database persist files.

## Example Notebooks

Example notebooks are located in `notebooks/Examples` that document and demonstrate interaction of JupyterLab
with Kinetica.

| Notebook File | Description |
| :--- | :--- |
| ex_kapi_io.ipynb | Load/Save Pandas Dataframes with the Kinetica REST API. |
| ex_kodbc_io.ipynb | Load/Save Pandas Dataframes with the Kinetica ODBC. |
| ex_kudf_io.ipynb | Create/Execute a UDF to calculate sum-of-squares. |
| ex_kudf_lr.ipynb | Create/Execute a UDF to calculate linear regression with distributed inferencing. |
| ex_widget_lorenz.ipynb | Example of real-time refresh of calculation with widgets. |

To run the examples access **JupyterLab** at <http://localhost:8888> with password **kinetica**.

From within JupyterLab you should see an [Examples](notebooks/Examples) directory.
Open this directory and you will see the example notebooks each with their own documentation.
To run a notebook, select __Run->Run All Cells__.

## KJIO Utility Library

A set of utility functions collectively called **Kinetica Jupyter I/O** are located in `notebooks/KJIO`
to simplify the task of interacting with Kinetica from notebooks. The example notebooks demonstrate their
functionality.

| Script | Description |
| :--- | :--- |
| [kapi_io.py](notebooks/KJIO/kapi_io.py) | Load and save Dataframes to/from Kinetica tables. |
| [kmodel_io.py](notebooks/KJIO/kmodel_io.py) | Load and save ML models with a Kinetica table. |
| [kodbc_io.py](notebooks/KJIO/kodbc_io.py) | Interact with tables using ODBC. |
| [kudf_io.py](notebooks/KJIO/kudf_io.py) | Functions to simplify creation and execution of UDF's. |

## Pulling from DockerHub

In this section we will use **docker-compose** to pull the [kinetica/kinetica-jupyterlab][DOCKERHUB]
image from DockerHub.
If you don't want to build the image as outlined in the next section then you can pull it from dockerhub.

[DOCKERHUB]: <https://hub.docker.com/r/kinetica/kinetica-jupyterlab/>

Open a shell to the Docker directory and invoke `docker-compose pull`. This will download about 7GB of data
so make sure you have a solid internet connection.

```
[~/Local/workspace/kinetica-jupyterlab (master)]$ cd docker/
[~/Local/workspace/kinetica-jupyterlab/docker (master)]$ docker-compose pull
Pulling gpudb ... done
```

You can use the `docker image` command below to confirm your image was downloaded successfully.

```
[~/Local/workspace/kinetica-jupyterlab/docker (master)]$ docker image list
REPOSITORY                     TAG                 IMAGE ID            CREATED             SIZE
kinetica/kinetica-jupyterlab   7.1                 54641137324d        3 hours ago         9.64GB
centos                         7                   49f7960eb7e4        7 weeks ago         200MB

```

## Building

*Note: You can skip this section if you prefer to pull the image from DockerHub.*

To build the image you will need to download a Kinetica 7.x RPM from the [RPM download site][RPM_DOWNLOAD].
Copy the RPM to the directory containing the build files.

```sh
[~/Local/workspace/kinetica-jnb/docker]$ ls -l
total 1967576
-rw-r--r--  1 chadjuliano  staff   2.6K Nov  6 12:21 Dockerfile-jupyterlab-7.x
drwxr-xr-x  7 chadjuliano  staff   224B Oct 14 09:30 config/
-rw-r--r--@ 1 chadjuliano  staff   566B Nov  6 11:45 docker-compose.yml
-rw-r--r--@ 1 chadjuliano  staff   952M Nov  4 05:26 gpudb-intel-license-7.0.9.0.20191102010945.ga-0.el7.x86_64.rpm
drwxr-xr-x  7 chadjuliano  staff   224B Nov  6 12:46 share/

```

Edit `Dockerfile-jupyterlab-7.x` and update the `GPUDB_PKG` parameter with the name of your RPM and build
the image with `docker-compose build`.

```
[~/kinetica-jupyterlab/docker  (master)]$ docker-compose build
Building gpudb
Step 1/34 : FROM centos:7
 ---> 49f7960eb7e4
Step 2/34 : MAINTAINER Chad Juliano <cjuliano@kinetica.com>
 ---> Using cache
 ---> 49812a2e0e26
[...]
```

[RPM_DOWNLOAD]: <http://repo.kinetica.com/yum/7.1/CentOS/7/x86_64/>

## License Configuration

The database is configured to start automatically but for this to succeed a license key must be configured.
Edit `docker/share/conf/gpudb.conf`, uncomment the line with `license_key` and add your key.

```
# The license key to authorize running.
license_key = {your key}
```

*Note: If the key is invalid then the container startup will fail.*

## Starting the Container

Start the image with `docker-compose up`. The combined log output of Kinetica and JupyterLab will be
displayed in the console.

```
[~/kinetica-jupyterlab/docker (master)]$ docker-compose up
Creating network "docker_default" with the default driver
Creating gpudb-jupyterlab-6.x ... done
Attaching to gpudb-jupyterlab-6.x
[...]
gpudb-jupyterlab-6.x | 2018-07-25 23:45:04.516 INFO  (2494,5923,r0/gpudb_sl_shtbl )
d0a1758a319b Utils/GaiaHTTPUtils.h:161 - JobId:1011;
call_gaia_internal endpoint: /show/table completed in: 0.00193 s
```

If you want a bash prompt in the container, open up another console and run the below command.

```
[~/kinetica-jupyterlab/docker (master)]$ docker-compose exec gpudb /bin/bash
[root@d0a1758a319b ~]# su - gpudb
Last login: Wed Jul 25 23:44:11 UTC 2018
[gpudb@d0a1758a319b ~]$
```

To stop the container, use the `docker-compose down` command.

```
[~/kinetica-jupyterlab/docker (master)]$ docker-compose down
Stopping gpudb-jupyterlab-6.x ... done
Removing gpudb-jupyterlab-6.x ... done
Removing network docker_default
```

To access **Kinetica** GAdmin use <http://localhost:8080/gadmin> and login with **admin/admin**.

To access **JupyterLab** open <http://localhost:8888> and enter password **kinetica**.

## See also

* [DockerHub Image](https://hub.docker.com/r/kinetica/kinetica-jupyterlab)
* [Project Jupyter Home](http://jupyter.org)
* [JupyterLab Documentation](http://jupyterlab.readthedocs.io/en/latest/)
* [IPython Documentation](https://ipython.readthedocs.io/en/stable/index.html)
