FROM ubuntu
RUN apt-get update && apt-get install -y --no-install-recommends software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && apt-get install -y --no-install-recommends python3.8-minimal && \
    apt-get install -y --no-install-recommends libgl1-mesa-glx && \
    apt-get install -y --no-install-recommends python3-pip && rm -rf /var/lib/apt/lists/* && \
    ln -s /usr/bin/pip3 /usr/bin/pip && ln -s /usr/bin/python3.8 /usr/bin/python && pip3 install virtualenv
ENV HOME=/home/lpr
COPY broker ${HOME}/broker/
COPY helper ${HOME}/helper/
COPY misc ${HOME}/misc/
COPY requirement ${HOME}/requirement/
COPY src ${HOME}/src/
COPY storage ${HOME}/storage/
COPY ["environment.env", "install-package.sh","main.py", "run.sh", "classes.txt", "yolo-obj.cfg", "yolo-obj_final.weights", "${HOME}/"]
WORKDIR ${HOME}
RUN chmod +x install-package.sh && chmod +x run.sh && ./install-package.sh