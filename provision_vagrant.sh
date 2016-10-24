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

# install mongodb

sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 614D985504A2163B
echo "deb http://repo.mongodb.org/apt/ubuntu \
	"$(lsb_release -sc)"/mongodb-org/3.1 multiverse" \
	| sudo tee /etc/apt/sources.list.d/mongodb-org-3.1.list

sudo apt-get update
sudo apt-get install -y mongodb-org-unstable



