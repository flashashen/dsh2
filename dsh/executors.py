from __future__ import print_function
import subprocess, sys, traceback, six, os
import api
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
    print('testing __return_child_result ..')
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
    print(method, args)
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
   :return: executor method. closure on execute_with_running_output(command, ctx)
   """

    return lambda match_result, child_results: execute_shell_cmd(
        command,
        match_result.matched_input()[1:]
            if match_result.matched_input() and name == match_result.matched_input()[0]
            else match_result.matched_input()[:],
        match_result.input_remainder(),
        child_results,
        ctx,
        return_output)
    # return lambda ctx, matched_input, child_results: sys.stdout.write('test shell output')


import re
VAR_FORMAT_PATTERN = re.compile(r'{{(\w*)}}')

def __format(target, sources=[]):

    # do the replacements of {{var}} style vars.
    #   m.group()  ->  {{var}}
    #   m.group(1) ->  var
    #
    while True:
        replacements = 0
        varmatches = re.finditer(VAR_FORMAT_PATTERN, target)
        if varmatches:
            for m in varmatches:
                for src in sources:
                    # If the matching key is found in the source, make the substitution
                    if src and m.group(1) in src:
                        target = target.replace(m.group(), src[m.group(1)])
                        replacements += 1
        if replacements == 0:
            break


    return target



def execute_shell_cmd(command, node_args, free_args, argvars, env=None, return_output=True):


    # print('execute_shell_cmd:  {}'.format(command))
    # print('execute_shell_cmd:  {}\n\tnode_args: {}\n\tfree_args: {}\n\tenv: {} '.format(command, node_args, free_args, env))


    cmd_string = __format(
        ' '.join([command] + node_args[:] + free_args[:]),
        [argvars, env])


    cmdenv = os.environ.copy()
    if env:
        cmdenv.update(env)

    # return the output
    if return_output:
        try:
            from StringIO import StringIO
        except ImportError:
            from io import StringIO
        output = StringIO()
        if execute_with_running_output(cmd_string, cmdenv, output) == 0:
            return output.getvalue().split('\n')
        else:
            raise ValueError(output.getvalue())

    # return the exit code
    else:
        return execute_with_running_output(cmd_string, cmdenv, line_prefix='')




def execute_with_running_output(command, env=None, out=None, line_prefix=''):


    # filter non string env vars
    if env:
        cmdenv = {k: v for k, v in env.items() if isinstance(v, six.string_types)}
    else:
        cmdenv = {}


    exitCode = 0

    try:
        # with given_dir(ctx['cmd_dir']):
        if not out:
            out = sys.stdout
            subprocess.check_call(command, shell=True, env=cmdenv)
        else:
            p = subprocess.Popen(command, shell=True, env=cmdenv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            output, err = p.communicate()
            exitCode = p.returncode
            out.write(output)


    except subprocess.CalledProcessError as e:
        out.write(e.output)
        out.flush()
        raise api.NodeExecutionFailed(e)
    # except Exception as ae:
    #     traceback.print_exc(file=out)

    return exitCode



