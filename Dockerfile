FROM python:3
ENV PYTHONUNBUFFERED=1
WORKDIR /app/
ADD requirements.txt /app
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip pip install -r requirements.txt
ADD . /app
#RUN chmod +x /app/docker/web/docker-entrypoint.sh
