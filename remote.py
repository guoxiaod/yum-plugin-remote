import os
import re
import subprocess
import types
import pexpect
import getpass
import pxssh
import sys

sys.path.insert(0, "/usr/share/yum-cli")

from yumcommands import YumCommand

from yum.plugins import PluginYumExit, TYPE_CORE, TYPE_INTERACTIVE

requires_api_version = '2.3'
plugin_type = (TYPE_CORE, TYPE_INTERACTIVE)
password = None

""" just make the usage show ssh command """
class SshCommand(YumCommand):
    def getNames(self):
        return ['ssh']

    def getUsage(self):
        return ("PACKAGE...")

    def getSummary(self):
        return ("Run command on remote server")

    def doCheck(self, base, basecmd, extcmds):
        pass

    def doCommand(self, base, basecmd, extcmds):
        return 0, ["ok"]

def is_int(s):
    return re.match("^[\d]+$", s)  is not None
    
def ssh_command(conduit, user, host, command):
    """ Run command on remote host
    :param conduit
    :param user 
    :param host
    :command
    :return exitstatus
    """
    global password
    ret = 0
    conduit.info(2, "[remote] ======================================")
    try: 
        cmd = "/usr/bin/ssh -t -l %s %s %s"%(user, host, command)
        conduit.info(2, "[remote] %s@%s>%s "%(user, host, command))
        p = pexpect.spawn(cmd, maxread = 512)
        # donot show the password
        p.setecho(False)
        # make all the output display
        p.logfile = sys.stdout
        retry = 3
        while True:
            idx = p.expect(["(?i)are you sure you want to continue connecting",  # ssh host
                        "(?is)Sorry, try again\..*\[sudo\] password for", # sudo
                        "(?i)permission denied", # ssh host
                        "(?i)(?:password)|(?:passphrase for key)",  # ssh host
                        "(?i)terminal type", 
                        "(?i)connection closed by remote host",
                        pexpect.EOF,
                        pexpect.TIMEOUT,
                        "(?i)Is this ok \[y\/N\]:",
                        ], timeout = 3600)
                
            if idx == 0: # ssh host
                p.sendline("yes")

            elif idx == 1: # sudo retry
                if retry > 0:
                    password = getpass.getpass("")
                    p.logfile = None
                    p.sendline(password)
                    p.logfile = sys.stdout
                else:
                    p.close()
                    ret = p.exitstatus
                    raise Exception("Permission deny for %s@%s!"%(user, host))
                    break
                retry -= 1

            elif idx == 2: # permission deny
                p.close()
                ret = p.exitstatus
                raise Exception("Permission deny for %s@%s!"%(user, host))
                break

            elif idx == 3: # password
                if password is None:
                    password = getpass.getpass("")

                # cann't display the password
                p.logfile = None
                p.sendline(password)
                p.logfile = sys.stdout


            elif idx == 4: # terminal type
                p.sendline("ansi")

            elif idx == 5 or idx == 6:
                p.close()
                ret = p.exitstatus
                break

            elif idx == 7:
                p.close()
                ret = p.exitstatus
                raise Exception("Timeout!")
                break

            elif idx == 8:
                p.sendline("y")

            else:
                p.close()
                ret = p.exitstatus
                raise Exception("Unexpected response for %s@%s!"%(user, host))
                break

    except Exception, e:
        conduit.info(2, "[remote] " + str(e))
    conduit.info(2, "[remote] ======================================")

    return ret

def parse_host(host):
    """  Parse string to host list
    
    :param host such as "fe[1-9].example.com"
    :return a host list
    """
    ret = []
    m = re.search("\[([a-z\d\-,]+)\]", host)
    if host != "" and m is None:
        ret.append(host)
    elif host != "":
        match = m.group(0)
        item_list = m.group(1).split(",")
        for item in item_list:
            from_to = item.split("-")
            if len(from_to) == 1 or (len(from_to) == 2 and from_to[1] == ''):
                ret.extend(parse_host(host.replace(match, from_to[0])))
            else:
                if is_int(from_to[0]) and is_int(from_to[1]):
                    for i in range(int(from_to[0]), int(from_to[1]) + 1):
                        ret.extend(parse_host(host.replace(match, str(i))))
        
    return ret

def parse_host_list(host_list):
    """  Use parse_host to parse a host list
    
    :param host_list such as ["fe[1-9].example.com", "[fe,db]1.example.com"]
    :return a host list
    """
    ret = []
    if type(host_list) is tuple or type(host_list) is list:
        for host in host_list:
            ret.extend(parse_host(host))
    elif type(host_list) is str:
        ret.extend(parse_host(host_list))
    return ret

def print_summary(conduit, host_list, succ_list, fail_list):

    conduit.info(2, "[remote] Summary:")
    conduit.info(2, "[remote]  total: " + str(len(host_list)) + " hosts")
    conduit.info(2, "[remote]  succ : " + str(len(succ_list)) + " hosts")
    conduit.info(2, "[remote]  fail : " + str(len(fail_list)) + " hosts")
    if len(succ_list) > 0:
        conduit.info(2, "[remote] succ_list:")
        for h in succ_list:
            conduit.info(2, "[remote]   " + h)
    if len(fail_list) > 0:
        conduit.info(2, "[remote] fail_list:")
        for h in fail_list:
            conduit.info(2, "[remote]   " + h)

def config_hook(conduit):
    parser = conduit.getOptParser()
    parser.add_option('', '--host', dest='host',
        default='', help="remote servers which we will run command on")

    parser.add_option('', '--host-file', dest='host_file',
        default='', help="like --host, but the servers should be in a file per line")
    
    parser.add_option('', '--user', dest='user',
        default='', help="if specific, we will run command on remote servers as user")

    conduit._base.registerCommand(SshCommand())

def args_hook(conduit):
    args = conduit.getArgs()

    user = os.environ["USER"]
    if "SUDO_USER" in os.environ:
        user = os.environ["SUDO_USER"]

    cmd = None
    filter_args = []
    host_list = []

    # yum -a -b --host=h1 install yyy yyy --host=h2 -c -d
    for arg in args:
        if cmd == None and arg[0] != "-":
            cmd = arg
            # if cmd is 'ssh', clear the args before 'ssh' and continue
            if cmd == "ssh":
                filter_args = []
                continue

        if arg[0:7] == "--host=":
            host_list.append(arg[7:])
        elif arg[0:12] == "--host-file=":
            file = arg[12:]
            try:
                host_list.extend([line.strip() for line in open(file, "r")])
            except:
                print "File '%s' not exists!" % (file)
                sys.exit()

        elif arg[0:7] == "--user=":
            user = arg[7:] or user
        else:
            filter_args.append(arg)
            
    host_list = parse_host_list(host_list)

    # only if len(host_list) > 0, we should run command on remote host
    if len(host_list) > 0:

        fail_list = []
        succ_list = []
        remote_cmd = " ".join(filter_args)
        
        if cmd != "ssh":
            remote_cmd = "sudo /usr/bin/yum " + remote_cmd

        for host in host_list:
            sts = ssh_command(conduit, user, host, remote_cmd)
            if sts == 0:
                succ_list.append(host)
            else:
                fail_list.append(host)

        if cmd != "ssh":
            print_summary(conduit, host_list, succ_list, fail_list)

        raise PluginYumExit('Goodbye!')
    elif cmd == "ssh":
        raise PluginYumExit("You must specific --host option")

