FROM python:3.5-slim
WORKDIR /opt/veil-vdi/app
RUN apt-get update && apt-get install -y apt-utils
RUN apt-get install -y python3-dev python3-setuptools python-dev gcc python3-pip libsasl2-dev libldap2-dev libssl-dev sudo
RUN pip install -U pip && pip install 'virtualenv==16.7.10' --force-reinstall && pip install pipenv
COPY devops/deb/veil-broker-backend/root/usr/sbin/* /usr/sbin/
ADD backend/Pipfile .
ADD backend/veil_api_client-2.2.1-py3-none-any.whl .
ADD backend/veil_aio_au-0.1.3-py3-none-any.whl .
RUN pipenv install --dev
