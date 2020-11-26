FROM python:3.5-slim
WORKDIR /opt/veil-vdi/app
RUN apt-get update && apt-get install -y apt-utils
RUN apt-get install -y python3-dev python3-setuptools python-dev gcc python3-pip libsasl2-dev libldap2-dev libssl-dev
RUN pip install -U pip && pip install 'virtualenv==16.7.10' --force-reinstall && pip install pipenv
ADD backend/Pipfile .
ADD backend/veil_api_client-2.0.4-py3-none-any.whl .
RUN pipenv install --dev
