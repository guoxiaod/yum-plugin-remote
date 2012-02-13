import subprocess
import os
from yum.plugins import PluginYumExit, TYPE_CORE, TYPE_INTERACTIVE

requires_api_version = '2.3'
plugin_type = (TYPE_CORE, TYPE_INTERACTIVE)


def parse_host(host):
	ret = []
	for h in host:
		ret.append(h)
	return ret

def config_hook(conduit):
	parser = conduit.getOptParser()
	parser.add_option('', '--host', dest='host',
		default='', help="run on remote host")

def args_hook(conduit):
	args = conduit.getArgs()
	host = []
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
				host.append(arg)
				last = 0
			else:
				rargs.append(arg)
	
	host = parse_host(host)
	
	for h in host:
		cmd = "/usr/bin/ssh -t " + user + "@" +  h + " sudo /usr/bin/yum " +  " ".join(rargs)
		subprocess.call(cmd,  shell = True )
	
	if len(host) > 0:
		raise PluginYumExit('Goodbye')
