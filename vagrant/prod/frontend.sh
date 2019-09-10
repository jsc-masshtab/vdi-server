cd ../../frontend
sudo snap install node --channel 11/stable --classic
rm -rf node_modules
/snap/bin/npm install

# Somehow doesn't work with nohup... Therefore, should be the last script to execute
/snap/bin/npm run ng serve -- --host 0.0.0.0
