'''

@author: Frank
'''

import sys, os, os.path
from zstacktestagent import testagent
from zstacklib.utils import log
from zstacklib.utils import linux
import zstacklib.utils.iptables as iptables

log.configure_log('/var/log/zstack/zstack-testagent.log')
logger = log.get_logger(__name__)

def main():
    usage = 'usage: python -c "from  zstacktestagent import zstacktestagentdaemon; zstacktestagentdaemon.main()" start|stop|restart'
    if len(sys.argv) != 2 or not sys.argv[1] in ['start', 'stop', 'restart']:
        print usage
        sys.exit(1)

    pidfile = '/var/run/zstack/zstacktestagent.pid'
    dirname = os.path.dirname(pidfile)
    if not os.path.exists(dirname):
        os.makedirs(dirname, 0755)
    
    try:
        iptables.insert_single_rule_to_filter_table('-A INPUT -p tcp -m tcp --dport 9393 -j ACCEPT')
        cmd = sys.argv[1]
        agentdaemon = testagent.TestAgentDaemon(pidfile)
        if cmd == 'start':
            agentdaemon.start()
        elif cmd == 'stop':
            agentdaemon.stop()
        elif cmd == 'restart':
            agentdaemon.restart()
        
        sys.exit(0)
    except Exception:
        logger.warning(linux.get_exception_stacktrace())
        sys.exit(1)
