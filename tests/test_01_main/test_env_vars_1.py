import time

import docker
import pytest
import requests

from ..utils import CONTAINER_NAME, get_logs, get_nginx_config, stop_previous_container

client = docker.from_env()


@pytest.mark.parametrize(
    "image,response_text",
    [
        (
            "tiangolo/uwsgi-nginx:python2.7",
            "Hello World from a default Nginx uWSGI Python 2.7 app in a Docker container (default)",
        ),
        (
            "tiangolo/uwsgi-nginx:python2.7-alpine3.7",
            "Hello World from a default Nginx uWSGI Python 2.7 app in a Docker container in Alpine (default)",
        ),
        (
            "tiangolo/uwsgi-nginx:python2.7-alpine3.8",
            "Hello World from a default Nginx uWSGI Python 2.7 app in a Docker container in Alpine (default)",
        ),
        (
            "tiangolo/uwsgi-nginx:python3.5",
            "Hello World from a default Nginx uWSGI Python 3.5 app in a Docker container (default)",
        ),
        (
            "tiangolo/uwsgi-nginx:python3.6",
            "Hello World from a default Nginx uWSGI Python 3.6 app in a Docker container (default)",
        ),
        (
            "tiangolo/uwsgi-nginx:python3.6-alpine3.7",
            "Hello World from a default Nginx uWSGI Python 3.6 app in a Docker container in Alpine (default)",
        ),
        (
            "tiangolo/uwsgi-nginx:python3.6-alpine3.8",
            "Hello World from a default Nginx uWSGI Python 3.6 app in a Docker container in Alpine (default)",
        ),
        (
            "tiangolo/uwsgi-nginx:python3.7",
            "Hello World from a default Nginx uWSGI Python 3.7 app in a Docker container (default)",
        ),
        # (
        #     "tiangolo/uwsgi-nginx:python3.7-alpine3.7",
        #     "Hello World from a default Nginx uWSGI Python 3.7 app in a Docker container in Alpine (default)",
        # ),
        # (
        #     "tiangolo/uwsgi-nginx:python3.7-alpine3.8",
        #     "Hello World from a default Nginx uWSGI Python 3.7 app in a Docker container in Alpine (default)",
        # ),
    ],
)
def test_env_vars_1(image, response_text):
    stop_previous_container(client)
    container = client.containers.run(
        image,
        name=CONTAINER_NAME,
        environment={
            "UWSGI_CHEAPER": 3,
            "UWSGI_PROCESSES": 8,
            "NGINX_MAX_UPLOAD": "1m",
            "NGINX_WORKER_PROCESSES": 2,
            "NGINX_WORKER_CONNECTIONS": 2048,
            "NGINX_WORKER_OPEN_FILES": 2048,
        },
        ports={"80": "8000"},
        detach=True,
    )
    nginx_config = get_nginx_config(container)
    assert "client_max_body_size 1m;" in nginx_config
    assert "worker_processes 2;" in nginx_config
    assert "listen 80;" in nginx_config
    assert "worker_connections 2048;" in nginx_config
    assert "worker_rlimit_nofile 2048;" in nginx_config
    assert "daemon off;" in nginx_config
    assert "listen 80;" in nginx_config
    assert "include uwsgi_params;" in nginx_config
    assert "uwsgi_pass unix:///tmp/uwsgi.sock;" in nginx_config
    time.sleep(3)
    logs = get_logs(container)
    assert "getting INI configuration from /app/uwsgi.ini" in logs
    assert "getting INI configuration from /etc/uwsgi/uwsgi.ini" in logs
    assert "ini = /app/uwsgi.ini" in logs
    assert "ini = /etc/uwsgi/uwsgi.ini" in logs
    assert "socket = /tmp/uwsgi.sock" in logs
    assert "chown-socket = nginx:nginx" in logs
    assert "chmod-socket = 664" in logs
    assert "hook-master-start = unix_signal:15 gracefully_kill_them_all" in logs
    assert "need-app = true" in logs
    assert "die-on-term = true" in logs
    assert "show-config = true" in logs
    assert "wsgi-file = /app/main.py" in logs
    assert "processes = 8" in logs
    assert "cheaper = 3" in logs
    assert "spawned uWSGI master process" in logs
    assert "spawned uWSGI worker 1" in logs
    assert "spawned uWSGI worker 2" in logs
    assert "spawned uWSGI worker 3" in logs
    assert "spawned uWSGI worker 4" not in logs
    assert 'running "unix_signal:15 gracefully_kill_them_all" (master-start)' in logs
    assert "success: nginx entered RUNNING state, process has stayed up for" in logs
    assert "success: uwsgi entered RUNNING state, process has stayed up for" in logs
    response: Response = requests.get("http://127.0.0.1:8000")
    assert response.status_code == 200
    assert response.text == response_text
    container.stop()
    container.remove()