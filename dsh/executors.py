import subprocess, sys, os, contextlib, traceback

#
#   Executor(context) methods.
#
#
#
#


def get_executor_noop():
    return lambda ctx, matched_input, child_results: None

def get_executor_return_child_results():
    return lambda ctx, matched_input, child_results: child_results

def get_executor_return_child_result_value():
    return lambda ctx, matched_input, child_results: child_results.values()[0]



def get_executor_python(method=None):
    """
    Return an executor that executes a given python method with child node execution values as args

    :param method: The method to call
    :return: executor method. closure on executor_python_method(method, args, kwargs)
    """
    return lambda ctx, matched_input, child_results: executor_python_method(method, child_results)

def executor_python_method(method, args=None):
    print(method, args)
    if args:
        return method(**args)
    else:
        return method()



def get_executor_return_matched_input():
    """
    Return an executor that simply returns the node's matched input
    """
    return lambda ctx, matched_input, child_results: matched_input



def get_executor_shell_cmd(command, return_output=False):
    """
   Return an executor(context) method that executes a shell command
   :param command:  command to be given to default system shell
   :return: executor method. closure on execute_with_running_output(command, ctx)
   """
    def execute_shell_cmd(command, return_output, ctx, matched_input, child_results):

        # return the output
        if return_output:
            import StringIO
            output = StringIO.StringIO()
            if execute_with_running_output(' '.join([command, matched_input]), child_results, ctx, output) == 0:
                return output.getvalue().split('\n')
            else:
                raise ValueError(output.getvalue())

        # return the exit code
        else:
            return execute_with_running_output(' '.join([command, matched_input]), child_results, ctx)

    return lambda ctx, matched_input, child_results: execute_shell_cmd(command, return_output, ctx, matched_input, child_results)



def execute_with_running_output(command, args=None, env=None, out=None):

    try:
        command = command.format(ctx=args)
        print('executing: {}\n'.format(command))
    except KeyError as e:
        print("Variable is missing from '{}': {}".format(command, str(e)))


    # with given_dir(ctx['cmd_dir']):
    if not out:
        out = sys.stdout

    exitCode = 0
    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
        # Poll process for new output until finished
        while True:
            nextline = process.stdout.readline()
            if not nextline and process.poll() is not None:
                break
            out.write(str(nextline))
            out.flush()

        output = process.communicate()[0]
        exitCode = process.returncode

        if (exitCode == 0):
            out.write(output)
        else:
            raise Exception(command, exitCode, output)

    except subprocess.CalledProcessError as e:
        out.write(e.output)
    except Exception as ae:
        traceback.print_exc()

    return exitCode



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


