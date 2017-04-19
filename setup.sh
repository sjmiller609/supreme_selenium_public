!#/bin/bash
sudo apt-get install -y python3-pip
pip3 install selenium
sudo apt-get install -y docker.io
sudo groupadd docker
sudo gpasswd -a ${USER} docker
sudo service docker restart
sudo docker pull selenium/standalone-chrome-debug:3.0.1-germanium
exec sudo su -l $USER
