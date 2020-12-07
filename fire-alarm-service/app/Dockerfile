# fa - fire alarm
# docker build -t fai .
# docker run --ipc=host --pid=host --device=/dev/fz_s_webcam:/dev/fz_s_webcam:rwm --name fac fai


FROM python:3.8.5-slim-buster

RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list
RUN apt update
RUN apt install -y build-essential libssl-dev libffi-dev python-dev vim procps

RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pip -U
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install requests flask flask_cors cffi

WORKDIR /app
RUN mkdir fz_sdk
RUN mkdir ./fz_sdk/fz_ipc
COPY ./fz_sdk/fz_ipc/*.py ./fz_sdk/fz_ipc/
WORKDIR /app/fz_sdk/fz_ipc
RUN python fz_signal_utils.py

WORKDIR /app

COPY take_picture_tool.c .
RUN gcc -o take_picture_tool.out take_picture_tool.c


COPY ./*.py ./
COPY ./fz_sdk/fz_sdk.py ./fz_sdk/

ENV RUN_OPTIONS="--ipc=host --pid=host --device=/dev/fz_s_webcam:/dev/fz_s_webcam:rwm"

ENTRYPOINT [ "python", "app.py" ]
