import sys, subprocess, six
from api import *
# from api import INPUT_MATCH 
from collections import defaultdict






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





def match_against_name(cmd_node, input_segments, start_index=None):
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
        return MATCH_RESULT(MATCH_EMPTY, start_index, start_index, [cmd_node.name])

    word = input_segments[start_index].strip()

    if cmd_node.name.startswith(word):
        if cmd_node.name == word:
            # Full match 'consumes' this word and provides no completions
            return MATCH_RESULT(MATCH_FULL, start_index, start_index+1, [])
        else:
            # Fragment match also 'consumes this word but also provides completions
            return MATCH_RESULT(MATCH_FRAGMENT, start_index, start_index+1, [cmd_node.name])

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



# 
# def completions(node, line):
#     return [p.completion_text for p in resolve_paths([ResolutionPath(node, line.split())])]








    #
    #
    # def do(self, segments):
    #
    #     print('do called on {}'.format(segments))
    #
    #     paths = resolve_paths([ResolutionPath(self, segments)])
    #     print '\n\ndo...\n', paths
    #
    #     # if len(matches.resolved) == 0:
    #     #     print 'No commands resovled'
    #     #     return
    #     #
    #     # if len(matches.resolved) > 1:
    #     #     print 'ambiguous command. These resovled: {}. executing first.'.format(matches.resolved)
    #     #
    #     #
    #     # matches.resolved[0].execute(" ".join(segments))
    #
    #
    # def complete(self, line):
    #     return self.resolve_line(line.split()).fragment


#
# class AllOf(CmdNode, object):
#
#     def __init__(self, name):
#         super(self.__class__, self).__init__(name)
#
#





class CmdNode(object):

    def __init__(self, name, cmd=None, match_func=match_against_name, eval_func=eval_status_choose_one_child):
        self.name = name
        self.children = []
        self.cmd = cmd

        # signature: MATCH_RESULT match(CmdNode, input, start)
        self.match = match_func.__get__(self, CmdNode)

        # signature: status evaluate(statuses)
        self.evaluate = eval_func


    def __repr__(self):
        return "<CmdNode:{} cmd={}, children=[{}]>".format(self.name,','.join(self.children))

    def execute(self, str_input):
        print "execute {} called on '{}'".format(self.name, str_input)


    def add_child(self, node):
        if node:
            self.children.append(node if isinstance(node, CmdNode) else CmdNode(node))

    def add_children(self, nodes):
        if isinstance(nodes, six.string_types):
            nodes = nodes.split()
        for node in nodes:
            self.add_child(node if isinstance(node,CmdNode) else CmdNode(str(node)))
