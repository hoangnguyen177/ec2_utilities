#!/usr/bin/env python
import os
import ec2
import sys
import getopt
from tabulate import tabulate

def check_env_variables():
    if os.environ.get('EC2_ACCESS_KEY')==None \
    or os.environ.get('EC2_SECRET_KEY')==None \
    or os.environ.get('EC2_URL')==None:
        raise Exception('Environment Variables Not Set', 'Please run ec2rc.sh')

def create_ec2_connection(region):
    check_env_variables()
    _access_key = os.environ.get('EC2_ACCESS_KEY')
    _secret_key = os.environ.get('EC2_SECRET_KEY')
    _url = os.environ.get('EC2_URL')
    return ec2.get_connection(region, _access_key, _secret_key, _url, False)  
        

def list_ami_ids(connection):
    images = connection.get_all_images()
    _table_headers = ['ID', 'Name']
    _table_rows = [] 
    for image in images:
        _table_row=[image.id, image.name]
        _table_rows.append(_table_row)
    print tabulate(_table_rows, _table_headers)

def usage():
        print "To list images"
        print "ec2utils.py [--images/i]"

def main(argv):
    try:
        opts, args = getopt.getopt(sys.argv[1:], ':hi',
                     ["help", "images"])
    except getopt.GetoptError as err:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        try:
            conn = create_ec2_connection('NeCTAR')
        except Exception as detail:
            print "Problem creating ec2 connection:", detail
            sys.exit(2)
        if o in ("-i", "--images"):
            list_ami_ids(conn)
        conn.close()
if __name__ == '__main__':
    main(sys.argv[1:])             
