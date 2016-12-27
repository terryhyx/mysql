import os
import sys
import cx_Oracle
import argparse
import re

class OraMetrics():
    def __init__(self, user, passwd, sid):
        import cx_Oracle
        self.user = user
        self.passwd = passwd
        self.sid = sid
        self.connection = cx_Oracle.connect( self.user , self.passwd , self.sid )
        cursor = self.connection.cursor()
        cursor.execute("select HOST_NAME from v$instance")
        for hostname in cursor:
            self.hostname = hostname[0]

    def waitclassstats(self, user, passwd, sid):
        cursor = self.connection.cursor()
        cursor.execute("""
        select n.wait_class, round(m.time_waited/m.INTSIZE_CSEC,3) AAS
        from   v$waitclassmetric  m, v$system_wait_class n
        where m.wait_class_id=n.wait_class_id and n.wait_class != 'Idle'
        union
        select  'CPU', round(value/100,3) AAS
        from v$sysmetric where metric_name='CPU Usage Per Sec' and group_id=2
        union select 'CPU_OS', round((prcnt.busy*parameter.cpu_count)/100,3) - aas.cpu
        from
            ( select value busy
                from v$sysmetric
                where metric_name='Host CPU Utilization (%)'
                and group_id=2 ) prcnt,
                ( select value cpu_count from v$parameter where name='cpu_count' )  parameter,
                ( select  'CPU', round(value/100,3) cpu from v$sysmetric where metric_name='CPU Usage Per Sec' and group_id=2) aas
        """)
        for wait in cursor:
            wait_name = wait[0]
            wait_value = wait[1]
            print "oracle_wait_class,host=%s,db=%s,wait_class=%s wait_value=%s" % (self.hostname, sid,re.sub(' ', '_', wait_name), wait_value )

    def waitstats(self, user, passwd, sid):
        cursor = self.connection.cursor()
        cursor.execute("""
    select
    n.wait_class wait_class,
        n.name wait_name,
        m.wait_count cnt,
        round(10*m.time_waited/nullif(m.wait_count,0),3) avgms
    from v$eventmetric m,
        v$event_name n
    where m.event_id=n.event_id
    and n.wait_class <> 'Idle' and m.wait_count > 0 order by 1 """)
        for wait in cursor:
         wait_class = wait[0]
         wait_name = wait[1]
         wait_cnt = wait[2]
         wait_avgms = wait[3]
         print "oracle_wait_event,host=%s,db=%s,wait_class=%s,wait_event=%s count=%s,latency=%s" % (self.hostname, sid,re.sub(' ', '_', wait_class),re.sub(' ', '_', wait_name)
, wait_cnt,wait_avgms)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--user', help="Username", required=True)
    parser.add_argument('-p', '--passwd', required=True)
    parser.add_argument('-s', '--sid', help="SID", required=True)

    args = parser.parse_args()

    stats = OraMetrics(args.user, args.passwd, args.sid)
    stats.waitclassstats(args.user, args.passwd, args.sid)
    stats.waitstats(args.user, args.passwd, args.sid)
