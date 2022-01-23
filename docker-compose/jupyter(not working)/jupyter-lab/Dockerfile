FROM jupyter/scipy-notebook:137a295ff71b

USER root

# APT packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    fonts-dejavu \
    tzdata \
    gfortran \
    gcc \
    scilab \
    pari-gp \
    libpari-dev \
    sagemath \
    sagemath-jupyter \
    libgmp-dev \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

USER $NB_UID

# Conda packages
# Sage conflicts with the latest jupyterhub, thus we must relax the pinning
RUN conda install --quiet --yes \
    'r-base=3.4.1' \
    'r-irkernel=0.8*' \
    'r-plyr=1.8*' \
    'r-devtools=1.13*' \
    'r-tidyverse=1.1*' \
    'r-shiny=1.0*' \
    'r-rmarkdown=1.8*' \
    'r-forecast=8.2*' \
    'r-rsqlite=2.0*' \
    'r-reshape2=1.4*' \
    'r-nycflights13=0.2*' \
    'r-caret=6.0*' \
    'r-rcurl=1.95*' \
    'r-crayon=1.3*' \
    'r-randomforest=4.6*' \
    'r-htmltools=0.3*' \
    'r-sparklyr=0.7*' \
    'r-htmlwidgets=1.0*' \
    'r-hexbin=1.27*' \
    'jupyterhub' \
#    'sage=8.*' \
    'julia=1.0*' && \
    conda clean -tipsy && \
    fix-permissions $CONDA_DIR

ENV CPATH=$CONDA_DIR/include

RUN pip install \
    pari_jupyter \
#    PySingular jupyter_kernel_singular \
    scilab-kernel && \
    fix-permissions $CONDA_DIR

# Fix SageMath kernel
USER root
RUN sed -i 's/"\/usr\/bin\/sage"/"env", "PATH=\/usr\/local\/sbin:\/usr\/local\/bin:\/usr\/sbin:\/usr\/bin:\/sbin:\/bin", "\/usr\/bin\/sage"/' /usr/share/jupyter/kernels/sagemath/kernel.json
USER $NB_UID

# Add conda env hook
COPY ./conda-activate.sh /usr/local/bin/before-notebook.d/