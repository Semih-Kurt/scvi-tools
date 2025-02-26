Installation
------------

Prerequisites
~~~~~~~~~~~~~~

scvi-tools can be installed via conda or pip. If you don't know which to choose, we recommend conda for beginner users.

conda prerequisites
###################

1. Install Conda. We typically use the Miniconda_ Python distribution. Use Python version >=3.7.

2. Create a new conda environment::

    conda create -n scvi-env python=3.7

3. Activate your environment::

    source activate scvi-env

pip prerequisites
#################

1. Install Python_, we prefer the `pyenv <https://github.com/pyenv/pyenv/>`_ version management system, along with `pyenv-virtualenv <https://github.com/pyenv/pyenv-virtualenv/>`_.

2. Install PyTorch_. If you have an Nvidia GPU, be sure to install a version of PyTorch that supports it -- scvi-tools runs much faster with a discrete GPU.

.. _Miniconda: https://conda.io/miniconda.html
.. _Python: https://www.python.org/downloads/
.. _PyTorch: http://pytorch.org


Conda
~~~~~

::

    conda install scvi-tools -c conda-forge

Pip
~~~

::

    pip install scvi-tools

Through pip with packages to run notebooks. This installs scanpy, etc.::

    pip install scvi-tools[tutorials]

Nightly version - clone this repo and run::

    pip install .

Development
~~~~~~~~~~~

For development - clone this repo and run::

    pip install -e ".[dev,docs]"

R
~

scvi-tools can be called from R via Reticulate.

This is only recommended for basic functionality (getting the latent space, normalized expression, differential expression). For more involved analyses with scvi-tools, we highly recommend using it from Python.

The easiest way to install scvi-tools for R is via conda.

1. Install Conda Prerequisites (see above).
2. Install Reticulate::

    install.packages("reticulate")

3. Then in your R code::

    library(reticulate)
    use_condaenv("scvi-env", required=TRUE)

.. _Reticulate: https://rstudio.github.io/reticulate/
