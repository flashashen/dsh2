from cmd_node import *




#
#    Test match functions
#


def assert_match_result(result, expected_status):

    assert result.status != None, 'match status be one of pre-defined values'
    assert result.status == expected_status
    assert result.start != None and result.stop != None, 'start and stop must have a value in all cases. Use 0 as default'

    if result.status == MATCH_NONE:
        assert result.start == result.stop, 'MATCH_NONE must consume no input, ie, start should equal stop'
        assert not result.completions, 'MATCH_NONE should have no completions'

    elif result.status == MATCH_EMPTY:
        assert result.start == result.stop, 'MATCH_EMPTY must consume no input, ie, start should equal stop'

    elif result.status == MATCH_FRAGMENT:
        assert result.start == result.stop, 'MATCH_FRAGMENT must consume no input, ie, start should equal stop'

    elif result.status == MATCH_FULL:
        assert result.start < result.stop, 'MATCH_FULL must consume some input, ie, stop should be greater than start'
        assert not result.completions, 'MATCH_FULL should have no completions'


def assert_match_function_result_common(func, node, full_match):

    node.match = func.__get__(node, None)

    # test None and empty and consumed inputs return MATCH_EMPTY
    assert_match_result(node.match( None), MATCH_EMPTY)
    assert_match_result(node.match( None, 0), MATCH_EMPTY)
    assert_match_result(node.match( []), MATCH_EMPTY)
    assert_match_result(node.match( [], 0), MATCH_EMPTY)
    assert_match_result(node.match( ['dontcare'], 1), MATCH_EMPTY)

    # test fragment, full and extra as only input
    assert_match_result(node.match( [full_match[:-1]], 0), MATCH_FRAGMENT)
    assert_match_result(node.match( [full_match], 0), MATCH_FULL)
    assert_match_result(node.match( [full_match+'inhibitmatch'], 0), MATCH_NONE)
    assert_match_result(node.match( ['inhibitmatch'], 0), MATCH_NONE)

    # test fragment, full and extra in middle of input
    assert_match_result(node.match( ['dontcare1', 'dontcare2', full_match, 'dontcare3'], 2), MATCH_FULL)
    assert_match_result(node.match( ['dontcare1', 'dontcare2', full_match[:-1], 'dontcare3'], 2), MATCH_FRAGMENT)
    assert_match_result(node.match( ['dontcare1', 'dontcare2', full_match+'inhibitmatch', 'dontcare3'], 2), MATCH_NONE)



def test_match_against_name():
    assert_match_function_result_common(match_against_name, CmdNode('testcmd'), 'testcmd')



#
#   Test child status evaluation functions
#


def assert_eval_function(func, expected, statuses, error_message):
    result = func(statuses)
    assert result == expected, error_message


def test_choose_one_child():

    # completed
    assert_eval_function(eval_status_choose_one_child, STATUS_COMPLETED, [], 'choose one with no children should be completed')
    assert_eval_function(eval_status_choose_one_child, STATUS_COMPLETED, [STATUS_COMPLETED], 'choose one with no children should be completed')
    assert_eval_function(eval_status_choose_one_child, STATUS_COMPLETED, [STATUS_UNSATISFIED, STATUS_UNSATISFIED, STATUS_COMPLETED], 'choose one with a completed child and the rest unsatisfied should be completed')

    # satisfied
    assert_eval_function(eval_status_choose_one_child, STATUS_SATISFIED, [STATUS_SATISFIED], 'choose one with a satisfied child should be satisfied')
    assert_eval_function(eval_status_choose_one_child, STATUS_SATISFIED, [STATUS_UNSATISFIED, STATUS_UNSATISFIED, STATUS_SATISFIED], 'choose one with a satisfied child and the rest unsatisfied should be satisfied')

    # unsatisfied
    status = eval_status_choose_one_child([STATUS_UNSATISFIED])
    assert status == STATUS_UNSATISFIED, 'choose one with only an unsatisfied child should be unsatisfied'
    status = eval_status_choose_one_child([STATUS_EXCEEDED])
    assert status == STATUS_UNSATISFIED, 'choose one only a exceeded child should be unsatisfied'
    status = eval_status_choose_one_child([STATUS_UNSATISFIED, STATUS_UNSATISFIED, STATUS_EXCEEDED])
    assert status == STATUS_UNSATISFIED, 'choose one with any exceeded children should be unsatisfied'

    # exceeded
    status = eval_status_choose_one_child([STATUS_UNSATISFIED, STATUS_COMPLETED, STATUS_SATISFIED])
    assert status == STATUS_EXCEEDED, 'choose one with more than one satisfied or completed child should be exceeded'



def test_require_all_children():

    # completed
    status = eval_status_require_all_children([])
    assert status == STATUS_COMPLETED, 'require all with no children should be completed'
    status = eval_status_require_all_children([STATUS_COMPLETED])
    assert status == STATUS_COMPLETED, 'require all with only a completed child should be completed'
    status = eval_status_require_all_children([STATUS_COMPLETED, STATUS_COMPLETED, STATUS_COMPLETED])
    assert status == STATUS_COMPLETED, 'require all with all completed children should be completed'

    # satisfied
    status = eval_status_require_all_children([STATUS_SATISFIED])
    assert status == STATUS_SATISFIED, 'require all with only a satisfied child should be satisfied'
    status = eval_status_require_all_children([STATUS_SATISFIED, STATUS_SATISFIED, STATUS_COMPLETED])
    assert status == STATUS_SATISFIED, 'require all with all satisfied or completed children should be satisfied'

    # unsatisfied
    status = eval_status_require_all_children([STATUS_UNSATISFIED, STATUS_SATISFIED, STATUS_COMPLETED])
    assert status == STATUS_UNSATISFIED, 'require all with any unsatisfied children should be unsatisfied'
    status = eval_status_require_all_children([STATUS_UNSATISFIED, STATUS_SATISFIED])
    assert status == STATUS_UNSATISFIED, 'require all with any unsatisfied children should be unsatisfied'
    status = eval_status_require_all_children([STATUS_EXCEEDED, STATUS_COMPLETED])
    assert status == STATUS_UNSATISFIED, 'require all with any exceeded children should be unsatisfied'
    status = eval_status_require_all_children([STATUS_UNSATISFIED])
    assert status == STATUS_UNSATISFIED, 'require all only an unsatisfied child should be unsatisfied'

    # require all cannot be exceeded


def test_children_as_options():

    # completed
    status = eval_status_children_as_options([])
    assert status == STATUS_COMPLETED, 'options with no children should be completed'
    status = eval_status_children_as_options([STATUS_COMPLETED])
    assert status == STATUS_COMPLETED, 'options with a completed child should be completed'
    status = eval_status_children_as_options([STATUS_COMPLETED,STATUS_COMPLETED,STATUS_COMPLETED])
    assert status == STATUS_COMPLETED, 'options with all completed children should be completed'

    # satisfied
    status = eval_status_children_as_options([STATUS_UNSATISFIED, STATUS_UNSATISFIED, STATUS_UNSATISFIED])
    assert status == STATUS_SATISFIED , 'options with all un-satisfied children should still be satisfied'
    status = eval_status_children_as_options([STATUS_COMPLETED,STATUS_COMPLETED, STATUS_SATISFIED])
    assert status == STATUS_SATISFIED , 'options with all satisfied or completed children should be satisfied'

    # unsatisfied
    status = eval_status_children_as_options([STATUS_EXCEEDED])
    assert status == STATUS_UNSATISFIED, 'options with only an exceeded child should be unsatisfied'
    status = eval_status_children_as_options([STATUS_EXCEEDED , STATUS_COMPLETED, STATUS_COMPLETED])
    assert status == STATUS_UNSATISFIED , 'options with any exceeded children should be unsatisfied'

    # options cannot be exceeded


#
# def get_root():
#     p1 = CmdNode('ans')
#     p1.add_child(CmdNode('list'))
#     # p1.add_child(CmdNode('play'))
#     p1.add_child(play())
#     # p1.add_child(list())
#
#     # p1.add_child(CmdNode('list'))
#     # p1.children[0].add_child(CmdNode('app1_1', True))
#     # p1.children[0].add_child(CmdNode('app1_2', True))
#     # p1.children[0].add_tag('testtag')
#     # p1.add_rule_one_of('testtag')
#     return p1
#
#
# playbooks = ['ansiblize.yml',
#              'artifactory.yml']
#
# def play():
#     p = CmdNode('play')
#     for book in playbooks:
#         p.add_child(CmdNode(book))
#     return p
#
#
# def list():
#     p = CmdNode('list')
#     p.add_child(CmdNode('groups'))
#     p.add_child(CmdNode('hosts'))
#     p.add_child(CmdNode('playbooks'))
#     return p
#
#
# def test_resolve():
#     print get_root().children
#     res = get_root().complete('ans')
#     print res
