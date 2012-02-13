import os
import re
import subprocess
import types
from yum.plugins import PluginYumExit, TYPE_CORE, TYPE_INTERACTIVE

requires_api_version = '2.3'
plugin_type = (TYPE_CORE, TYPE_INTERACTIVE)

def is_int(s):
    return re.match("^[\d]+$", s)  is not None


def parse_host(host):
    """  Parse string to host list
    
    :param host such as "fe[1-9].example.com"
    :return a host list
    """
    ret = []
    m = re.search("\[([a-z\d\-,]+)\]", host)
    if m is None:
        ret.append(host)
    else:
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

def config_hook(conduit):
    parser = conduit.getOptParser()
    parser.add_option('', '--host', dest='host',
        default='', help="run yum on remote host")

def args_hook(conduit):
    args = conduit.getArgs()
    host_list = []
    rargs = []
    last = 0
    user = os.environ["USER"]
    if "SUDO_USER" in os.environ:
        user = os.environ["SUDO_USER"]
    for arg in args:
        if arg == "--host":
            last = 1
        else:
            if last == 1:
                host_list.append(arg)
                last = 0
            else:
                rargs.append(arg)
    
    host_list = parse_host_list(host_list)
    
    total = 0
    succ = 0
    fail_list = []
    succ_list = []
    for h in host_list:
        remote_cmd = "sudo /usr/bin/yum " +  " ".join(rargs)
        cmd = ["/usr/bin/ssh -t ", user + "@" +  h, remote_cmd]
        conduit.info(1, "====================================")
        conduit.info(1, "Command: <<<" + " ".join(cmd) + ">>>")
        sts = subprocess.call(" ".join(cmd),  shell = True)
        total += 1
        if sts == 0:
            succ += 1
            succ_list.append(h)
        else:
            fail_list.append(h)

    if len(host_list) > 0:
        conduit.info(2, "Summary:")
        conduit.info(2, " total: " + str(total) + " hosts")
        conduit.info(2, " succ : " + str(succ) + " hosts")
        if len(succ_list) > 0:
            conduit.info(2, " succ_list:")
            for h in succ_list:
                conduit.info(2, "   " + h)
        if len(fail_list) > 0:
            conduit.info(2, " fail_list:")
            for h in fail_list:
                conduit.info(2, "   " + h)
        raise PluginYumExit('Goodbye')

