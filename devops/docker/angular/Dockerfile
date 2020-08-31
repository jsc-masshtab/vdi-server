FROM node:10-alpine
ENV PATH=$PATH:/home/node/app/node_modules/.bin
WORKDIR /home/node/app
RUN chown -R node: /home/node/app
ADD frontend/package.json .
ADD frontend/package-lock.json .
USER node
RUN npm install
