import subprocess, sys, os, contextlib
from node import *


from executors import execute_with_running_output

class CmdAns(CmdNode):


    def shell_cmd(self, matched_result, ctx):
        # print ctx
        ctx['cmd_dir'] = '/Users/panelson/workspace/devops/playbooks'
        execute_with_running_output('ansible-playbook {ctx[playbook]}', ctx)


    def __init__(self):

        super(self.__class__, self).__init__('ans', self.shell_cmd)
        self.name = 'ans'
        self.children = []
        self.add_child(node_choose_value_for('playbook', playbooks))




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
