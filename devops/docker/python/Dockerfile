FROM python:3.5.5-slim-stretch
WORKDIR /opt/veil-vdi/app
RUN apt-get update && apt-get install -y python3-dev python3-setuptools python-dev gcc python3-pip libsasl2-dev libldap2-dev libssl-dev sudo
COPY devops/deb/veil-broker-backend/root/usr/sbin/* /usr/sbin/
COPY devops/docker/python/tests_entry_point.sh /usr/sbin/tests_entry_point.sh
COPY devops/docker/python/systemctl /usr/sbin/systemctl
RUN chmod 777 /usr/sbin/systemctl
ADD backend/*requirements.txt ./
RUN pip install -r requirements.txt && pip install -r dev-requirements.txt

