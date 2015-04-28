A tool for easy querying information for ec2 services

Requirements:
-------------
* python-pip.noarch
* git
* python 2.6 preferred

Installation:
------------
* git clone https://github.com/hoangnguyen177/ec2_utilities.git
* cd ec2_utilities
* sudo python setup.py install

Usage:
-------
* download ec2 credentials, unzip and cd to that folder
* source ec2rc.sh 
--> ec2utilities relies on the environment variables set by this ec2rc.sh
* to list image
    ec2utils -i
