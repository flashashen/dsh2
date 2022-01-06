import subprocess, sys, traceback, os, contextlib, io
from dsh import api
#
#   Executor(context) methods.
#
#
#
#


def get_executor_noop():
    return lambda match_result, child_results: None

def get_executor_return_child_results():
    return lambda match_result, child_results: child_results

def __return_child_result(match_result, child_results):
    return list(child_results.values())[0]

def get_executor_return_child_result_value():
    return __return_child_result



def get_executor_python(method=None):
    """
    Return an executor that executes a given python method with child node execution values as args

    :param method: The method to call
    :return: executor method. closure on executor_python_method(method, args, kwargs)
    """
    return lambda match_result, child_results: executor_python_method(method, child_results)

def executor_python_method(method, args=None):
    # print(method, args)
    if args:
        return method(**args)
    else:
        return method()



def get_executor_return_matched_input():
    """
    Return an executor that simply returns the node's matched input
    """
    return lambda match_result, child_results: ' '.join(match_result.matched_input()[:])





def get_executor_shell_cmd(name, command, return_output=True, ctx=None):
    """
   Return an executor(context) method that executes a shell command
   :param command:  command to be given to default system shell
   :return: executor method
   """

    return lambda match_result, child_results: execute_shell_cmd(
        command,
            match_result.matched_input()[1:]
                if match_result.matched_input() and name == match_result.matched_input()[0] else
            match_result.matched_input()[:],
        match_result.input_remainder(),
        child_results,
        ctx,
        return_output)
    # return lambda ctx, matched_input, child_results: sys.stdout.write('test shell output')





def execute_shell_cmd(command, node_args, free_args, argvars, env=None, return_output=True):


    cmd_string = api.__format(
        ' '.join([command] + node_args[:] + free_args[:]),
        [argvars, env])

    if api.verbose(env):
        print('execute_shell_cmd: {} against {}'.format(cmd_string, env))

    cmdenv = os.environ.copy()
    cmdenv.update(api.format_dict(env, argvars))

    # return the output
    if return_output:
        output = io.StringIO()
        if execute_with_running_output(cmd_string, cmdenv, output) == 0:
            return output.getvalue().split('\n')
        else:
            raise ValueError(output.getvalue())

    # return the exit code
    else:
        return execute_with_running_output(cmd_string, cmdenv, line_prefix='')






@contextlib.contextmanager
def working_directory(path):
    """
    Usage:
    >>> with working_directory('~/project_home'):
    ...   subprocess.call('project_script.sh')
    """
    if not path:
        yield
    else:
        starting_directory = os.getcwd()
        try:
            os.chdir(os.path.abspath(os.path.expanduser(path)))
            yield
        finally:
            os.chdir(starting_directory)





def execute_with_running_output(command, env=None, out=None, line_prefix=''):


    # print('execute_with_running_output: {} in {}'.format(command, env))

    # filter non string env vars
    if env:
        cmdenv = {k: v for k, v in env.items() if isinstance(v, str)}
    else:
        cmdenv = {}


    exitCode = 1

    try:
        if (env.get(api.CTX_VAR_WORK_DIR)) and not env.get(api.CTX_VAR_SRC_DIR).endswith(env.get(api.CTX_VAR_WORK_DIR)):
            # if work directory is absolute, then os.path.join will take it as the path and ignore the src dir.
            # Otherwise the paths will be joined into one. For this reason, no check for absolute path is required.
            workdir = os.path.join(env.get(api.CTX_VAR_SRC_DIR), env.get(api.CTX_VAR_WORK_DIR))
        else:
            workdir = env.get(api.CTX_VAR_SRC_DIR)


        with working_directory(workdir):
            if not out:
                out = sys.stdout
                subprocess.check_call(command, shell=True, env=cmdenv)
            else:
                p = subprocess.Popen(command, shell=True, env=cmdenv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
                output, err = p.communicate()
                exitCode = p.returncode
                if output:
                    out.write(output)
                if exitCode != 0:
                    raise api.NodeExecutionFailed('command failed with status {}: {}'.format(exitCode, command))

    except subprocess.CalledProcessError as e:
        # out.write(e.output)
        # out.flush()
        raise api.NodeExecutionFailed(e)
    except Exception as ae:
        traceback.print_exc(file=out)


    return exitCode



