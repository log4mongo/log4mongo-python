#!/usr/bin/env bash
export DEBIAN_FRONTEND=noninteractive

sudo locale-gen "en_US.UTF-8"
sudo dpkg-reconfigure locales

echo "LC_ALL=en_US.UTF-8" >> /etc/environment
echo "LANG=en_US.UTF-8" >> /etc/environment

PACKAGES="python-dev python3-dev build-essential"


apt-get update
apt-get install -y ${PACKAGES}

if [ ! -f  /usr/local/bin/pip ]; then
    wget https://bootstrap.pypa.io/get-pip.py
	sudo python get-pip.py
fi

if [ ! -f  /usr/local/bin/pip3 ]; then
	sudo python3 get-pip.py
fi


PYTHON_PACKAGES="pymongo>=2.8 pexpect coverage unittest2 \
virtualenvwrapper"

sudo pip3 install ${PYTHON_PACKAGES}
sudo pip install ${PYTHON_PACKAGES}

sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 68818C72E52529D4
sudo echo "deb http://repo.mongodb.org/apt/ubuntu bionic/mongodb-org/4.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.0.list

sudo apt-get update
sudo apt-get install -y mongodb-org
