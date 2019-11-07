# Build instructions for a GPUDB docker file.
FROM centos:7
MAINTAINER Chad Juliano <cjuliano@kinetica.com>

WORKDIR /root

# Install some basics
RUN yum -y update && yum install -y \
    openssh-client \
    openssh-server \
    vim \
    nc \
    git \
    java-1.8.0-openjdk

# Install python 3.6
RUN yum -y groupinstall development
RUN yum -y install https://centos7.iuscommunity.org/ius-release.rpm
RUN yum -y install python36u \
    python36u-pip \
    python36u-devel
RUN pip3.6 install --upgrade pip

# install ML components
RUN pip3 install \
    numpy \
    pandas \
    matplotlib \
    sklearn \
    scipy \
    plotly \
    tensorflow

RUN pip3 install http://download.pytorch.org/whl/cpu/torch-0.4.0-cp36-cp36m-linux_x86_64.whl
RUN pip3 install torchvision

# this can be overriden but will default to latest version supported
ARG GPUDB_PKG=gpudb-intel-license-7.0.9.0.20191102010945.ga-0.el7.x86_64.rpm

# install package and dependencies
COPY $GPUDB_PKG .
RUN yum install -y ./$GPUDB_PKG
RUN rm $GPUDB_PKG

RUN ldconfig
EXPOSE 5601 8080 8181 8082 8088 9191 9292 9193

# install jupyterlab
RUN pip3 install jupyter
RUN pip3 install jupyterlab
EXPOSE 8888

# setup jupyter user
RUN useradd --create-home --gid users --comment 'Jupyter User' jupyter
RUN su - jupyter -c 'jupyter lab --generate-config'

# set password (password is 'kinetica')
COPY --chown=jupyter:users config/jupyter_notebook_config.json /home/jupyter/.jupyter/

# install kinetica API
RUN pip3 install gpudb

# install pyodbc
RUN yum -y install unixODBC-devel
RUN pip3.6 install pyodbc
RUN /bin/cp -f /opt/gpudb/connectors/odbc/etc/odbcinst.ini /etc
RUN /bin/cp -f /opt/gpudb/connectors/odbc/etc/odbc.ini /etc

# Install PDF export support (experimental)
#RUN yum -y install pandoc
#RUN yum -y install \
#    texlive \
#    texlive-latex \
#    texlive-xetex \
#    texlive-adjustbox \
#    texlive-upquote

# install nodejs+jupyter-widgets extension
RUN curl -L -o ./nodesource-release-el7-1.noarch.rpm  'https://rpm.nodesource.com/pub_8.x/el/7/x86_64/nodesource-release-el7-1.noarch.rpm'
RUN yum -y install ./nodesource-release-el7-1.noarch.rpm
RUN yum -y clean all
RUN yum -y install nodejs
RUN npm i npm@latest -g
RUN jupyter labextension install @jupyter-widgets/jupyterlab-manager

# clean up
RUN yum clean all

# install UDF API
RUN unzip /opt/gpudb/downloads/gpudb-udf-api-python.zip
RUN cd ./gpudb-udf-api-python && python3.6 setup.py install

# install start scripts
COPY config/lib_config_functions.sh .
COPY config/start-jupyter.sh .
COPY config/start-gpudb.sh .
COPY config/gpudb-docker.sh .
RUN chmod +x *.sh

ENTRYPOINT ["/root/gpudb-docker.sh"]
