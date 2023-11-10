FROM tiangolo/uwsgi-nginx:python3.10
LABEL authors="Андрей Сильных"

ENV PYTYHONBUFFERED=1
RUN python -m pip install --upgrade pip
COPY ../requirements.txt ./requirements.txt
RUN python -m pip install -r requirements.txt