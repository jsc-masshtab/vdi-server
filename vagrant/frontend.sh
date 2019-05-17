cd /vagrant/frontend/
rm -rf node_modules
npm install

pkill npm
# Somehow doesn't work with nohup... Therefore, should be the last script to execute
npm run ng serve -- --host 0.0.0.0
