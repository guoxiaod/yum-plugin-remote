#!/usr/bin/python


import re
from remote import parse_host, parse_host_list



def test_parse_host(host):
    print "================"
    print "Host: ", host
    print parse_host(host)

test_parse_host("fe[1-3].bj1.yongche.com")
test_parse_host("fe[1-3,12,14-15].bj1.yongche.com")
test_parse_host("fe[1-3,12,14-15].bj[1-3,10].yongche.com")
test_parse_host("[api,fe,db,xmpp]1.[bj,hz]1.yongche.com")
