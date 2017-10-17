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



#
# def get_executor_add_kwarg(key, value):
#     """
#     Return an executor(context) takes a given key, value and adds them to
#     the given context in the expected spot for method kwargs. This is intended for
#     command argument nodes whose purpose is just to put an argument into the context
#
#     :param key:
#     :param value:
#     :return: executor method. closure on executor_name_to_context(ctx, key, value)
#     """
#     return lambda ctx: executor_add_to_contex(ctx['method_kwargs'], key, value)
#
# def get_executor_return_key__child_value(key):
#     """
#     Return an executor(context) that simply adds a given key, value to the resolver/execution context
#     :param key:
#     :param value:
#     :return: executor method. closure on executor_name_to_context(ctx, key, value)
#     """
#     return lambda ctx, matched_input, child_results: {key: child_results.values()[0]}





def get_executor_shell(command):
    """
   Return an executor(context) method that executes a shell command
   :param command:  command to be given to default system shell
   :return: executor method. closure on execute_with_running_output(command, ctx)
   """
    return lambda ctx, matched_input, child_results: execute_with_running_output(command, ctx, child_results)


def execute_with_running_output(command, ctx=None, env=None):

    try:
        command = command.format(ctx=ctx)
        print('executing: {}\n'.format(command))
    except KeyError as e:
        print("Variable is missing from '{}': {}".format(command, str(e)))


    with given_dir(ctx['cmd_dir']):

        exitCode = 0
        try:
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
            # Poll process for new output until finished
            while True:
                nextline = process.stdout.readline()
                if not nextline and process.poll() is not None:
                    break
                sys.stdout.write(str(nextline))
                sys.stdout.flush()

            output = process.communicate()[0]
            exitCode = process.returncode

            if (exitCode == 0):
                print(output)
            else:
                raise Exception(command, exitCode, output)

        except subprocess.CalledProcessError as e:
            sys.stdout.write(e.output)
        except Exception as ae:
            traceback.print_exc(file=sys.stdout)

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


