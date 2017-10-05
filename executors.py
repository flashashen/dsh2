import subprocess, sys, os, contextlib

#
#   Executor(context) methods.
#
#
#
#
#   ctx['method_obj']       callabe method object
#   ctx['method_kargs']     dictionary of kwargs
#
#



def get_executor_python(method=None):
    """
    Return a executor(context) method that executes a python method against keyword
    arguments found in the context

    :param method: The method to call. If None, then the method object will be expected in ctx['method_obj']
    :return: executor method. closure on executor_python_method(method, args, kwargs)
    """
    return lambda ctx: executor_python_method(method, [], ctx['method_kwargs'])

def executor_python_method(method, args=None, ctx=None):
    method(*args, **ctx)



#
# def get_executor_add_kwarg(key, value):
#     """
#     Return an executor(context) method takes a given key, value and adds them to
#     the given context in the expected spot for method kwargs. This is intended for
#     command argument nodes whose purpose is just to put an argument into the context
#
#     :param key:
#     :param value:
#     :return: executor method. closure on executor_name_to_context(ctx, key, value)
#     """
#     return lambda ctx: executor_name_to_context(ctx['method_kwargs'], key, value)
#
# def get_executor_add_to_context(key, value=''):
#     """
#     Return an executor(context) method that simply adds a given key, value to the resolver/execution context
#     :param key:
#     :param value:
#     :return: executor method. closure on executor_name_to_context(ctx, key, value)
#     """
#     return lambda ctx: executor_name_to_context(ctx, key, value)
#
# def executor_name_to_context(ctx, name, value):
#     ctx[name] = value




def get_executor_shell(command):
    """
   Return an executor(context) method that executes a shell command
   :param command:  command to be given to default system shell
   :return: executor method. closure on execute_with_running_output(command, ctx)
   """
    return lambda ctx: execute_with_running_output(command, ctx)

def execute_with_running_output(command, ctx=None):

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


