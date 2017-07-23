import subprocess, sys, os, contextlib
from cmd_node import *



@contextlib.contextmanager
def given_dir(path):
    """
    Usage:
    >>> with given_dir(prj_base):
    ...   subprocess.call('project_script.sh')
    """
    if not path:
        yield

    starting_directory = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(starting_directory)


def execute_with_running_output(command, ctx):

    try:
        command = command.format(ctx=ctx)
        print('executing: {}\n'.format(command))
    except KeyError as e:
        print("Variable is missing from '{}': {}".format(command, str(e)))



    with given_dir(ctx['cmd_dir']):

        try:
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            # Poll process for new output until finished
            while True:
                nextline = process.stdout.readline()
                if nextline == '' and process.poll() is not None:
                    break
                sys.stdout.write(nextline)
                sys.stdout.flush()

            output = process.communicate()[0]
            exitCode = process.returncode

            if (exitCode == 0):
                return output
            else:
                raise Exception(command, exitCode, output)

        except subprocess.CalledProcessError as e:
            return e.output
        except Exception as ae:
            return ae.message




class CmdAns(CmdNode):


    def shell_cmd(self, ctx):
        # print ctx
        ctx['cmd_dir'] = '/Users/panelson/workspace/devops/playbooks'
        execute_with_running_output('ansible-playbook {ctx[playbook]}', ctx)


    def __init__(self):

        super(self.__class__, self).__init__('ans', self.shell_cmd)
        self.name = 'ans'
        self.children = []
        self.add_child(choose_value_for('playbook', *playbooks))




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

# def playbook():
#     p = CmdNode('playbook')
#     p.add_child(CmdNode(book))
#     return p