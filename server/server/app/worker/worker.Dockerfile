FROM debian:bullseye-slim
EXPOSE 500 5555
RUN apt-get update && apt-get install -y wget libgomp1 zip unzip automake autoconf pkg-config autoconf-archive git build-essential dos2unix
# set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV EXECUTABLES_DIR=/code/app/worker
ENV CONDA_DIR=/opt/conda
ENV PATH=$CONDA_DIR/bin:$PATH
# setup miniconda & install dependencies
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-py310_25.7.0-2-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda
# accept conda license
RUN conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
RUN conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
# install dependencies
COPY requirements.txt /code/requirements.txt
RUN conda install -yv --file /code/requirements.txt -c bioconda -c conda-forge
# Setup work directory
WORKDIR /code/app/worker
COPY . .
# Windows uses an extra newline character '\r' which causes an error when copying scripts on a Windows platform. So convert to Unix format here
RUN dos2unix /code/app/worker/entrypoint.sh
# chmod start script which won't be in scripts directory
RUN chmod +x entrypoint.sh
# Remove dos2unix tools
RUN apt-get --purge remove -y dos2unix && rm -rf /var/lib/apt/lists/*
ENTRYPOINT ["./entrypoint.sh"]