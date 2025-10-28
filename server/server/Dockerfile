FROM debian:bullseye-slim
EXPOSE 5000
RUN apt-get update && apt-get install -y wget libgomp1 zip unzip
# setup miniconda
ENV CONDA_DIR /opt/conda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-py310_25.7.0-2-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda
ENV PATH=$CONDA_DIR/bin:$PATH
COPY ./requirements.txt /code/requirements.txt
# accept conda license
RUN conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
RUN conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
# install dependencies
RUN conda install -yv --file /code/requirements.txt -c bioconda -c conda-forge
# create volume
WORKDIR /code
# setup app & run server
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]
