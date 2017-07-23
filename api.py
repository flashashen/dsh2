from collections import namedtuple

UNEVALUATED = 'UNEVALUATED'


MATCH_NONE = 'NONE'             # No Match
MATCH_EMPTY = 'EMPTY'           # Matched against empty input
MATCH_FRAGMENT = 'FRAGMENT'     # Matched input as a fragment against current node
MATCH_FULL = 'FULL'             # Matched input fully against current node

# STATUS_INITIAL = 'INITIAL'
STATUS_UNSATISFIED = 'UNSATISFIED'
STATUS_SATISFIED = 'SATISFIED'
STATUS_COMPLETED = 'COMPLETED'
STATUS_EXCEEDED = 'EXCEEDED'
STATUS_UNRESOLVED = 'UNRESOLVED'

MODE_COMPLETE = 'MODE_COMPLETE'
MODE_EXECUTE = 'MODE_EXECUTE'

#
#   Match
#
#   INPUT_MATCH = cmd_node.match(input_segments, start_index)
#
MATCH_RESULT = namedtuple('MATCH_RESULT', 'status start stop completions')

def MATCH_RESULT_NONE(start_index=0):
    return MATCH_RESULT(MATCH_NONE, start_index, start_index, [])


#
#   Evaluate
#

RESOLUTION = namedtuple('RESOLUTION', 'resolution_status, match_result, completions')


#
#       ordered_list_of_resolved_children = resolve(node, input, index)
#
#       if tail is unsatisfied, then only tail can produce completions
#
#




# RESOLUTION_NO_MATCH = RESOLUTION(STATUS_UNSATISFIED, MATCH_RESULT(MATCH_NONE, None), [])


#
#   (match_status, sat_status, start, stop, completions) resolve(input, start, mode)
#
#       case 1: simple choose one from list of words. no children involved. no eval needed.
#       case 2: two children which are case 1.
#           - sat_status delegates to children with a delegation function
#
#   match(input, start)
#   eval(child_statues)
#   complete(input, start)
#
#
#



# cmd.completions(input)
# cmd.executions(input)