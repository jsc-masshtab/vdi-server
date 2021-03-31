FROM python:3.5-slim
WORKDIR /opt/veil-vdi/app
RUN apt-get update && apt-get install -y python3-dev python3-setuptools python-dev gcc python3-pip libsasl2-dev libldap2-dev libssl-dev sudo
COPY devops/deb/veil-broker-backend/root/usr/sbin/* /usr/sbin/
ADD backend/*requirements.txt ./
RUN pip install -r requirements.txt && pip install -r dev-requirements.txt
