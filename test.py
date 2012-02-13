#!/usr/bin/python


import re
import os
from remote import parse_host, parse_host_list, ssh_command


class TestClass:
    def info(self, level, msg):
        print msg

def test_ssh_command(user, host, command):
    ssh_command(TestClass(), user, host, command)



def test_parse_host(host):
    print "================"
    print "Host: ", host
    print parse_host(host)

#test_parse_host("fe[1-3].bj1.yongche.com")
#test_parse_host("fe[1-3,12,14-15].bj1.yongche.com")
#test_parse_host("fe[1-3,12,14-15].bj[1-3,10].yongche.com")
#test_parse_host("[api,fe,db,xmpp]1.[bj,hz]1.yongche.com")


test_ssh_command(os.environ["USER"], "192.168.1.226", "sudo yum install x")
test_ssh_command(os.environ["USER"], "192.168.1.227", "sudo yum install x")
