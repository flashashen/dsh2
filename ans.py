from proto import Proto


def get_proto():
    p1 = Proto('ans')
    p1.add_child(play())
    p1.add_child(list())

    p1.add_child(Proto('list'))
    # p1.children[0].add_child(Proto('app1_1', True))
    # p1.children[0].add_child(Proto('app1_2', True))
    # p1.children[0].add_tag('testtag')
    # p1.add_rule_one_of('testtag')
    return p1


playbooks = ['ansiblize.yml',
             'artifactory.yml',
             'batchapi.yml',
             'buildgui.yml',
             'buildserver.yml',
             'cfg2html.yml',
             'chordate.yml',
             'confluence.yml',
             'deploy_dms.yml',
             'deploy_pycardholder.yml',
             'deploy_www_readydebit_com.yml',
             'dms.yml',
             'docker.yml',
             'graylog.yml',
             'java.yml',
             'jenkins.yml',
             'jira.yml',
             'linux.yml',
             'mongo.yml',
             'mysql.yml',
             'mysqlclient.yml',
             'nagios.yml',
             'newdockerready.yml',
             'nrpe.yml',
             'openreports.yml',
             'paul.yml',
             'pyreworks.yml',
             'randy.yml',
             'rd-app.yml',
             'rd-cip.yml',
             'rd-collect_configs.yml',
             'rd-db.yml',
             'rd-sftp.yml',
             'rd-web.yml',
             'rd_deploy_www_readydebit_com.yml',
             'ready_cron_runner_only.yml',
             'ready_cron_tabs_only.yml',
             'ready_graylog_collector.yml',
             'run_role.yml',
             'setup_user.yml',
             'sire4.yml',
             'sire5.yml',
             'sire6.yml',
             'site.yml',
             'stash.yml',
             'tcpdump.yml',
             'teamcity-agent.yml',
             'teamcity.yml',
             'tom.yml',
             'upgrade_artifactory.yml',
             'upgrade_stash.yml',
             'yum.yml']

def play():
    p = Proto('play')
    for book in playbooks:
        p.add_child(Proto(book))
    return p

def list():
    p = Proto('list')
    p.add_child(Proto('groups'))
    p.add_child(Proto('hosts'))
    p.add_child(Proto('playbooks'))
    return p