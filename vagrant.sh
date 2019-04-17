echo "Upgrade arch..."
pacman --noconfirm -Syu

echo "Installing packages..."
pacman --noconfirm -S --needed base-devel
pacman --noconfirm -S nodejs npm


echo "Running the frontend server..."
cd /vagrant/frontend
rm -rf /vagrant/frontend/node_modules
npm install
nohup npm run ng serve -- --host 0.0.0.0 &

echo "Setup finished"