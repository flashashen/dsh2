import subprocess, sys, traceback

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

def __return_child_result(ctx, matched_input, child_results):
    print('testing __return_child_result ..')
    return child_results.values()[0]

def get_executor_return_child_result_value():
    return __return_child_result



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
    return lambda ctx, matched_input, child_results: ' '.join(matched_input[:])



def get_executor_shell_cmd(command, return_output=False):
    """
   Return an executor(context) method that executes a shell command
   :param command:  command to be given to default system shell
   :return: executor method. closure on execute_with_running_output(command, ctx)
   """
    def execute_shell_cmd(ctx, matched_input, child_results):

        # the command is the given, static command string plus any extra input
        cmd_string = ' '.join([command] + matched_input[1:])

        # do the replacements of {{var}} style vars.
        #   m.group()  ->  {{var}}
        #   m.group(1) ->  var
        #
        if child_results or ctx:
            import re
            p = re.compile(r'{{(\w*)}}')
            matches = re.finditer(p, cmd_string)
            if matches:
                for m in matches:
                    # arguments provided by child nodes take precedence
                    if child_results and m.group(1) in child_results:
                        cmd_string = cmd_string.replace(m.group(), child_results[m.group(1)])
                    # next take values from context
                    if ctx and m.group(1) in ctx:
                        cmd_string = cmd_string.replace(m.group(), ctx[m.group(1)])

        # try:
        #     cmd_string = cmd_string.format(ctx=args)
        #     print('executing: {}\n'.format(cmd_string))
        # except KeyError as e:
        #     print("Variable is missing from '{}': {}".format(command, str(e)))


        # return the output
        if return_output:
            import StringIO
            output = StringIO.StringIO()
            if execute_with_running_output(cmd_string, child_results, ctx, output) == 0:
                return output.getvalue().split('\n')
            else:
                raise ValueError(output.getvalue())

        # return the exit code
        else:
            return execute_with_running_output(cmd_string, child_results, ctx)

    return execute_shell_cmd
    # return lambda ctx, matched_input, child_results: sys.stdout.write('test shell output')



def execute_with_running_output(command, args=None, env=None, out=None):


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
            # print(nextline)
            out.write(str(nextline))
            out.flush()

        output = process.communicate()[0]
        exitCode = process.returncode

        if (exitCode == 0):
            out.write(output)
        # else:
        #     raise Exception(command, exitCode, output)

    except subprocess.CalledProcessError as e:
        out.write(e.output)
    except Exception as ae:
        traceback.print_exc(file=out)

    return exitCode



