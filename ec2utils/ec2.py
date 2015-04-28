#
# ec2 utilities - somes copied from Nimrod
#

from urlparse import urlparse
from decorators import retry
#boto
import boto
from boto.ec2.regioninfo import RegionInfo
from boto.exception import EC2ResponseError
import sys
import time
# boto 2.34
def get_connection(label, key, secret, ec2_url, validation):
    """
    Create EC2 API connection
    @type   label: String
    @param  label: label

    @type   key: String
    @param  key: secret id

    @type   secret: String
    @param  secret: secret string

    @type   ec2_url: String
    @param  ec2_url: Ec2 Service URL

    @type   validation: Boolean
    @param  validation: 

    @rtype : Ec2 Connection
    @return: ec2 connection
    """
    url = urlparse(ec2_url)
    region = RegionInfo(name=label, endpoint=url.hostname)
    if url.scheme == 'https':
        secure = True
    else:
        secure = False
    if url.path == '' or url.path == '/':
        path = '/'
    else:
        path = url.path
    
    # Workaround: Boto 2.6.0 SSL cert validation breaks with Python < 2.7.3
    (major, minor, patchlevel) = sys.version_info[:3]
    if not validation or (major < 3 and (minor < 7 or (minor == 7 and patchlevel < 3))):
        conn = boto.connect_ec2(aws_access_key_id=key,
                                aws_secret_access_key=secret,
                                is_secure=secure,
                                region=region,
                                port=url.port,
                                path=path,
                                validate_certs=False)
    else:
        conn = boto.connect_ec2(aws_access_key_id=key,
                                aws_secret_access_key=secret,
                                is_secure=secure,
                                region=region,
                                port=url.port,
                                path=path)

    return conn

@retry(3)
def create_keypair(ec2conn, label):
    """Create an SSH keypair for accessing instances.
    @type   ec2conn: EC2 connection
    @param  ec2conn: EC2 connection

    @type   label: String
    @param  label: label

    @rtype Boolean
    @return True if succeed, False otherwise    
    """
    # Try to delete first (from previous run), then create
    try:
        del_keypair(ec2conn, label)
        kp = ec2conn.create_key_pair(label)
        return kp
    except EC2ResponseError,e:
        print t5exc.exception()
        return False

@retry(2)
def getcreate_sec_group(ec2conn, label=u'default'):
    """Get and possibly create if it does exist the EC2 security group described by label. Using ec2conn to talk to AWS.
    @type   ec2conn: EC2 connection
    @param  ec2conn: EC2 connection

    @type   label: String
    @param  label: label

    @rtype String
    @return security group    
    """
    try:
        secgroupdesc = unicode('n'+`int(time.time())`)
        secgroup = None
        for group in ec2conn.get_all_security_groups():
            if group.name == label:
                secgroup = group
                break
        if not secgroup:
            secgroup = ec2conn.create_security_group(label, secgroupdesc)
        return secgroup
    except EC2ResponseError, e:
        print t5exc.exception()
        return False

@retry(5)
def del_sec_group(ec2conn, label):
    """Delete the EC2 security group described by label. Using ec2conn to talk to AWS.
    @type   ec2conn: EC2 connection
    @param  ec2conn: EC2 connection

    @type   label: String
    @param  label: label

    @rtype Boolean
    @return True if succeed, False otherwise    
    """
    try:
        # returns True even when secgroup doesn't exist
        ec2conn.delete_security_group(label)
        return True
    except EC2ResponseError, e:
        print t5exc.exception()
        if parse_response_error(e, 'Code') == u'SecurityGroupNotFoundForProject':
            # secgroup might already be deleted so don't keep trying
            return True
        return False

@retry(5)
def del_keypair(ec2conn, label):
    """Delete the EC2 keypair described by label. Using ec2conn to talk to AWS.
    @type   ec2conn: EC2 connection
    @param  ec2conn: EC2 connection

    @type   label: String
    @param  label: label

    @rtype Boolean
    @return True if succeed, False otherwise    
    """
    try:
        # returns True even when keypair doesn't exist
        ec2conn.delete_key_pair(label)
        return True
    except EC2ResponseError,e:
        print t5exc.exception()
        return False

@retry(5)
def keypair_exists(ec2conn, label):
    """Checks if a keypair exists. Using ec2conn to talk to AWS.
    @type   ec2conn: EC2 connection
    @param  ec2conn: EC2 connection

    @type   label: String
    @param  label: label

    @rtype Boolean
    @return True if exists, False otherwise
    """
    try:
        kp = ec2conn.get_key_pair(label)
        if kp:
            return True
    except EC2ResponseError,e:
        print t5exc.exception()
    return False

@retry(3)
def get_ami(ec2conn, ami_id):
    """Get . Using ec2conn to talk to AWS.
    @type   ec2conn: EC2 connection
    @param  ec2conn: EC2 connection

    @type   label: String
    @param  label: label
    """
    try:
        ami = ec2conn.get_image(ami_id)
        return ami
    except EC2ResponseError,e:
        print t5exc.exception()
        return False

@retry(3)
def get_azs(ec2conn):
    """Get availability zones.
    @type   ec2conn: EC2 connection
    @param  ec2conn: EC2 connection

    @rtype   List 
    @return  availability zones
    """
    try:
        return ec2conn.get_all_zones()
    except EC2ResponseError,e:
        print t5exc.exception()
        return False


def get_az(ec2conn, az_name):
    """Get a specific availability zone.
    @type   ec2conn: EC2 connection
    @param  ec2conn: EC2 connection

    @type   az_name: String
    @param  az_name: availability zone name

    @rtype: 
    @return: availability zone information
    """
    azs = get_azs(ec2conn)
    for az in azs:
        if az.name == az_name:
            return az
    return None



def blockTillRunning(reservation, timeout):
    """Block still all instances in reservation are in running state.
    @type   reservation: EC2 reservation
    @param  reservation: EC2 reservation

    @type   timeout: int
    @param  timeout in seconds
    """
    # block till all instances are running or timeout
    # check the status of instances
    # some times out needed here
    start = time.time()
    stopChecking = False
    while stopChecking == False and (time.time() - start <= timeout ): 
        stopChecking = True
        for instance in reservation.instances:
            instance.update()
            if(instance.state != u'running'):
                stopChecking = False
        time.sleep(10)


def main(argv):
    """ for testing """
    conn = get_connection("", "", "", "")
    conn.launch_vms(conn, "", "", "", "", [''])

    
