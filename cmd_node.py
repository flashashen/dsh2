import sys, subprocess, six, os
from api import *
# from api import INPUT_MATCH 
from collections import defaultdict



def get_children_method_dir_listing():
    import glob
    return lambda self, ctx: [CmdNode(p) for p in glob.glob('*')]


def execute_func_add_self_name_value(self, ctx):
    if not self.name in ctx:
        ctx[self.name] = ''


def choose_value_for(name, *choices):
    node = CmdNode(name, function_evaluate_child_statuses=eval_status_choose_one_child)
    for choice in choices:
        def f(self, ctx):
            ctx[name] = str(self.name)
        node.add_child(CmdNode(choice, method_execute=f))
    # node.add_children(choices)
    return node


def one_of(name, *choices):
    node = CmdNode(name, function_evaluate_child_statuses=eval_status_choose_one_child)
    node.add_children(choices)
    return node

def all_of(name, *choices):
    node = CmdNode(name, function_evaluate_child_statuses=eval_status_require_all_children)
    node.add_children(choices)
    return node

def options(name, *options):
    node = CmdNode(name, function_evaluate_child_statuses=eval_status_children_as_options)
    node.add_children(options)
    return node




#
#
# def execute(self, cmds, args, print_to_console=True):
#
#     if 'local_dir' in self.__dict__ and self.local_dir:
#         od = os.getcwd()
#         os.chdir(self.local_dir)
#
#     try:
#
#         cmd_list = self.flatten_cmd(cmds, self.cfg_obj.cmd)
#
#         # print('\n')
#         output = None
#
#         for index, c in enumerate(cmd_list):
#
#             if isinstance(c, CmdProto):
#                 c.execute(args)
#             elif type(c) == types.MethodType:
#                 c(args)
#             else:
#                 # try:
#                 c = c.format(cfg=self.get_shell_cmd_context())
#                 # except:
#                 #     c = c.format(cfg=self.get_shell_cmd_context())
#                 print('executing: {}\n'.format(c))
#                 output = self.__execute_with_running_output(c)
#
#     except AttributeError as ae:
#         output = ae.message
#     except subprocess.CalledProcessError as e:
#         output = e.output
#
#     finally:
#         if 'local_dir' in self.__dict__ and self.local_dir:
#             os.chdir(od)
#
#     if output and print_to_console:
#         print output
#
#     return output

def __execute_with_running_output(command):
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
        #pass
        # print command, exitCode, output
        raise Exception(command, exitCode, output)





def match_against_name(self, input_segments, start_index=None):
    """
    Get a match status and stop,start indices of resovled input segments. Only a full match
    will return resolved indices. Indices are inclusive. This form of the match function, if 
    there is a full match, always returns a stop index of start+1 since it performs a simple, 
    single word match
    
    :param input_segments: split input
    :param start_index: Where to look in the input. Analagous to cursor position 
    :return: (MATCH_STATUS, (start_of_resolved, end_of_resolved)) 
    """
    if start_index == None:
        start_index = 0

    if input_segments == None or len(input_segments) <= start_index:
        # If nothing is given as the input, then it matches as MATCH_EMPTY, a special case of fragment
        return MATCH_RESULT(MATCH_EMPTY, start_index, start_index, [self.name])

    word = input_segments[start_index].strip()

    if self.name.startswith(word):
        if self.name == word:
            # Full match 'consumes' this word and provides no completions
            return MATCH_RESULT(MATCH_FULL, start_index, start_index+1, [])
        else:
            # Fragment match also 'consumes this word but also provides completions
            return MATCH_RESULT(MATCH_FRAGMENT, start_index, start_index+1, [self.name])

    return MATCH_RESULT_NONE(start_index)




def __count_statuses(statuses):
    # use defaultdict counting idiom
    status_counts = defaultdict(int)
    for status in statuses:
        status_counts[status] += 1
    # There are only four valid statuses
    assert len(status_counts) <= 4
    return status_counts



def eval_status_require_all_children(statuses):
    """
    Satisfied when all children in the list are satisfied.
    Completed when all children in the list are completed.

    :param list of children node:
    :return: node status based on status of children
    """
    if not statuses:
        return STATUS_COMPLETED

    status_counts = __count_statuses(statuses )

    if status_counts[STATUS_EXCEEDED] > 0:
        # Don't propogate as exceeded. The parent of an exceeded child will
        # just be un-satisfied since the parent itself is not really exceeded.
        return STATUS_UNSATISFIED
    elif status_counts[STATUS_UNSATISFIED] > 0:
        return STATUS_UNSATISFIED
    elif status_counts[STATUS_COMPLETED] == len(statuses):
        return STATUS_COMPLETED
    else:
        # All are satisfied, but not all completed.
        return STATUS_SATISFIED




def eval_status_choose_one_child(statuses):
    """
    Satisfied when exactly one child in the list is satisfied (completed implies satisfied).
    Completed when exactly one child in the list is satisfied and also is completed.

    :param list of children node:
    :return: node status based on status of children
    """
    if not statuses:
        return STATUS_COMPLETED

    status_counts = __count_statuses(statuses)

    if (status_counts[STATUS_COMPLETED] + status_counts[STATUS_SATISFIED]) > 1:
        return STATUS_EXCEEDED
    elif status_counts[STATUS_SATISFIED] == 1:
        return STATUS_SATISFIED
    elif status_counts[STATUS_COMPLETED] == 1:
        return STATUS_COMPLETED
    else:
        return STATUS_UNSATISFIED


def eval_status_children_as_options(statuses):
    """
    All children are optional. Initial status is SATISFIED since
    no children are required. Status becomes completed when every
    child is completed

    :param list of children node:
    :return: node status based on status of children
    """
    if not statuses:
        return STATUS_COMPLETED

    status_counts = __count_statuses(statuses)

    if status_counts[STATUS_EXCEEDED]:
        return STATUS_UNSATISFIED
    elif status_counts[STATUS_COMPLETED] == len(statuses):
        return STATUS_COMPLETED
    else:
        return STATUS_SATISFIED




class CmdNode(object):

    def __init__(self, name,
                 method_execute=execute_func_add_self_name_value,
                 function_match_input=match_against_name,
                 function_evaluate_child_statuses=eval_status_choose_one_child,
                 child_get_func=None):

        self.name = name

        # Bind given functions to provide behavior
        self.execute = method_execute.__get__(self, CmdNode)
        self.match = function_match_input.__get__(self, CmdNode)
        self.evaluate = function_evaluate_child_statuses

        if child_get_func:
            self.get_children = child_get_func.__get__(self, CmdNode)
        else:
            self.get_children = self.__get_static_children
            self.__children = []



    def __repr__(self):
            return "<CmdNode:{} cmd={}, children=[{}]>".format(self.name, self.cmd, str(self.__children))

    # def execute(self, str_input):
    #     print "execute {} called on '{}'".format(self.name, str_input)

    def get_children(self):
        return self.__children




    # The add children methods no longer belong here since children are necessarily list
    # a static list anymore. They could instead be put into a list and contained in a
    # closure the returns them

    def __get_static_children(self, ctx):
        return self.__children

    def add_child(self, node):

        try:
            len(self.__children)
        except:
            raise ValueError("add_child() cannot be called if a get_children method has been provided ")

        if node:
            self.__children.append(node if isinstance(node, CmdNode) else CmdNode(node))


    def add_children(self, nodes):

        if isinstance(nodes, six.string_types):
            nodes = nodes.split()
        for node in nodes:
            self.add_child(node if isinstance(node,CmdNode) else CmdNode(str(node)))

