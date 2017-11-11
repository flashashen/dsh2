from context import *


def test_node_container():

    root = node.node_container('root')

    path = root.resolve([])
    assert path.status == api.STATUS_COMPLETED
    assert path.match_result.status == api.MATCH_FULL
    assert path.match_result.completions == []

    root.add_child('cmd_one').add_child('cmd_two')
    path = root.resolve([''])
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.completions == ['cmd_one', 'cmd_two']

    path = root.resolve(['cmd_one', 'cmd_two'])
    assert path.status == api.STATUS_COMPLETED
    assert path.match_result.completions == []

    path = root.resolve(['cmd_'])
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.completions == ['cmd_one', 'cmd_two']

    path = root.resolve(['cmd_two'])
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.completions == ['cmd_one']

    root.evaluate = evaluators.choose_one_child
    path = root.resolve(['cmd_two'])
    assert path.status == api.STATUS_COMPLETED
    assert path.match_result.completions == []




def test_all_of():

    root = node.node_root().all_of(['cmd_one', 'cmd_two'])

    path = root.resolve(['cmd_one', 'cmd_two'])
    assert path.status == api.STATUS_COMPLETED
    assert path.match_result.completions == []

    path = root.resolve(['cmd_two'])
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.completions == ['cmd_one']


def test_one_of():

    root = node.node_root().one_of(['cmd_one', 'cmd_two'])
    path = root.resolve(['cmd'])
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.completions == ['cmd_one', 'cmd_two']

    path = root.resolve(['cmd_two'])
    assert path.status == api.STATUS_COMPLETED
    assert path.match_result.completions == []




def test_nested_containers():

    root = node.node_container()
    root.all_of(['cmd_one', node.CmdNode('cmd_two').one_of(['opt1', 'opt2'])])

    path = root.resolve(['cmd_one', 'cmd_two', 'opt1'])
    assert path.status == api.STATUS_COMPLETED
    assert path.match_result.completions == []

    path = root.resolve(['cmd_one', 'cmd_two', 'op'])
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.completions == ['opt1', 'opt2']

    path = root.resolve(['cmd_two', 'op'])
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.completions == ['opt1', 'opt2']

    path = root.resolve(['cmd_two', 'opt1'])
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.completions == ['cmd_one']



def test_peer_containers():

    root = node.node_container()
    root.all_of(['cmd_one', 'cmd_two'])
    root.one_of(['cmd_three', 'cmd_four'])

    path = root.resolve([''])
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.completions == ['cmd_one', 'cmd_two', 'cmd_three', 'cmd_four']

    path = root.resolve(['cmd_one', 'cmd_two', 'cmd_four'])
    assert path.status == api.STATUS_COMPLETED
    assert path.match_result.completions == []

    path = root.resolve(['cmd_one', 'cmd_two'])
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.completions == ['cmd_three', 'cmd_four']

    path = root.resolve(['cmd_three'])
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.completions == ['cmd_one', 'cmd_two']


    # run(node.node_root().add_child(node.CmdNode('cmd')), 'f')


def test_node_argument():
    assert node.execute(node.node_argument('arg'), 'arg somefreevalue') == 'somefreevalue'



def test_node_options():

    root = node.CmdNode('root', method_evaluate=evaluators.require_all_children).options(['opt1', 'opt2']).add_child('cmd')

    path = root.resolve(['root'])
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.completions == ['opt1', 'opt2', 'cmd']

    path = root.resolve(['root', 'cmd'])
    assert path.status == api.STATUS_SATISFIED
    assert path.match_result.completions == ['opt1', 'opt2']

    path = root.resolve(['root', 'opt1'])
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.completions == ['opt2', 'cmd']

    # After the first option is supplied and then followed by a non-option
    # the second option should be presented as a completion
    path = root.resolve(['root', 'cmd', 'opt1'])
    assert path.status == api.STATUS_SATISFIED
    assert path.match_result.completions == ['opt2']


def test_node_python():

    def test_method(arg1, arg2, optional_arg=None, opt1=None, opt2=None):
        if not how:
            raise ValueError("arg1 missing")
        if not why:
            raise ValueError("arg2 missing")

    required = [node.node_argument('arg1'), node.node_argument('arg2')]
    optional = [node.node_argument('optional_arg')]
    options = ['-a', '-b']
    root = node.node_python(
        'do',
        test_method,
        required,
        optional,
        options)

    path = root.resolve(['do'])
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.completions == ['-a', '-b', 'arg1', 'arg2']

    path = root.resolve(['do', 'arg1'])
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.completions == []

    # path = root.resolve(['do', 'arg1', 'val1'])
    # assert path.status == api.STATUS_UNSATISFIED
    # assert path.match_result.completions == ['arg2', '-a', '-b']





def test_resolve_sequence_hosts_duplicated():

    # root = one_of('root', 'choice1', 'choice2')
    # path = ResolutionPath(root)
    # path = root.resolve(['root','invalid'])
    #
    # assert path.status == api.STATUS_UNSATISFIED
    # assert path.match_result.completions == []

    root = node.CmdNode('ans')

    # root.one_of(child='arg1',choices='val1,val1')
    # root.all_of('val1,val1')
    # root.require('env')
    # root.option('--H')


    root.all_of([
        node.CmdNode('play').one_of(['website.yml', 'appserver.yml']),
        node.CmdNode('list').all_of(['groups', 'hosts', 'playbooks'])
    ])

    path = root.resolve(['ans','list', 'groups', 'playbooks'])
    assert path.match_result.completions == ['hosts']




def test_root_doesnt_resolve_if_children_cant_resolve():

    root = node.CmdNode('root').one_of(['choice1', 'choice2'])
    path = root.resolve(['root','invalid'])

    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.completions == []



def test_full_and_fragment_siblings_same_prefix():

    root = node.CmdNode('root').one_of(['prefix', 'prefix_and_suffix'])
    path = root.resolve(['root','prefix'])

    # The root is satisfied since child 'prefix' is completed by the input
    assert path.status == api.STATUS_SATISFIED
    # Even though root is satisfied completions from 'prefix_and_suffix' child should be offered
    assert path.match_result.completions == ['prefix_and_suffix']



def test_resolve_sequence_all_one_one():

    # root = one_of('root', 'choice1', 'choice2')
    # path = ResolutionPath(root)
    # path = root.resolve(['root','invalid'])
    #
    # assert path.status == api.STATUS_UNSATISFIED
    # assert path.match_result.completions == []

    root = node.CmdNode('ans').all_of(
                  [node.CmdNode('play').one_of(['website.yml', 'appserver.yml']),
                   node.CmdNode('list').one_of(['groups', 'hosts', 'playbooks'])])


    path = root.resolve(['ans','pl'])
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.status == api.MATCH_FULL
    assert path.match_result.completions == ['play']


    path = root.resolve(['ans','play'])
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.status == api.MATCH_FULL
    assert path.match_result.completions == ['website.yml','appserver.yml']


    path = root.resolve(['ans','play', 'website.yml'])
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.status == api.MATCH_FULL
    assert path.match_result.completions == ['list']


    path = root.resolve(['ans','play', 'website.yml', 'li'])
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.status == api.MATCH_FULL
    assert path.match_result.completions == ['list']


    path = root.resolve(['ans','play', 'website.yml', 'list'])
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.status == api.MATCH_FULL
    assert path.match_result.completions == ['groups','hosts','playbooks']


    path = root.resolve(['ans','play', 'website.yml', 'list', 'g'])
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.status == api.MATCH_FULL
    assert path.match_result.completions == ['groups']


    path = root.resolve(['ans','play', 'website.yml', 'list', 'groups'])
    assert path.status == api.STATUS_COMPLETED
    assert path.match_result.status == api.MATCH_FULL
    assert path.match_result.completions == []



#
#    Test match functions
#


def assert_match_result(result, expected_status, expected_completions=None):

    assert result.status != None, 'match status be one of pre-defined values'
    assert result.status == expected_status
    assert result.start != None and result.stop != None, 'start and stop must have a value in all cases. Use 0 as default'

    if result.status == api.MATCH_NONE:
        assert result.start == result.stop, 'MATCH_NONE must consume no input, ie, start should equal stop'
        assert not result.completions, 'MATCH_NONE should have no completions'

    elif result.status == api.MATCH_EMPTY:
        assert result.start == result.stop, 'MATCH_EMPTY must consume no input, ie, start should equal stop'

    elif result.status == api.MATCH_FRAGMENT:
        assert result.start+1 == result.stop, 'MATCH_FRAGMENT must consume one input, ie, start+1 should equal stop'

    elif result.status == api.MATCH_FULL:
        assert result.start < result.stop, 'MATCH_FULL must consume some input, ie, stop should be greater than start'
        assert not result.completions, 'MATCH_FULL should have no completions'

    assert not expected_completions or expected_completions[result.status] == result.completions, 'completions did not match expected'


def assert_match_function_result_common(func, node, match_target, expected_completions=None):

    # node.match = func.__get__(node, None)

    # test None and empty and consumed inputs return MATCH_EMPTY
    assert_match_result(func( None), api.MATCH_EMPTY, expected_completions)
    assert_match_result(func( None, 0), api.MATCH_EMPTY, expected_completions)
    assert_match_result(func( []), api.MATCH_EMPTY, expected_completions)
    assert_match_result(func( [], 0), api.MATCH_EMPTY, expected_completions)
    assert_match_result(func( ['dontcare'], 1), api.MATCH_EMPTY, expected_completions)

    # test fragment, full and extra as only input
    assert_match_result(func( [match_target[:-1]], 0), api.MATCH_FRAGMENT, expected_completions)
    assert_match_result(func( [match_target], 0), api.MATCH_FULL, expected_completions)
    assert_match_result(func( [match_target+'inhibitmatch'], 0), api.MATCH_NONE, expected_completions)
    assert_match_result(func( ['inhibitmatch'], 0), api.MATCH_NONE, expected_completions)

    # test fragment, full and extra in middle of input
    assert_match_result(func( ['dontcare1', 'dontcare2', match_target, 'dontcare3'], 2), api.MATCH_FULL, expected_completions)
    assert_match_result(func( ['dontcare1', 'dontcare2', match_target[:-1], 'dontcare3'], 2), api.MATCH_FRAGMENT, expected_completions)
    assert_match_result(func( ['dontcare1', 'dontcare2', match_target+'inhibitmatch', 'dontcare3'], 2), api.MATCH_NONE, expected_completions)



def get_standard_completions(match_target):
    """
    mapping of match status to completion list for the standard case of simple matching
    and completing against a word

    :param match_target: The word/command/name to match against
    :return: dict of status:[completions]
    """
    return {
        api.MATCH_NONE: [],
        api.MATCH_EMPTY: [match_target],
        api.MATCH_FRAGMENT: [match_target],
        api.MATCH_FULL: []
    }



def test_match_string():
    n = node.CmdNode('testcmd')
    assert_match_function_result_common(matchers.get_matcher_exact_string(n.name), n, n.name, get_standard_completions(n.name) )



#
#   Test child status evaluation functions
#


def assert_eval_function(func, expected, statuses, error_message):
    result = func(statuses)
    assert result == expected, error_message


def test_choose_one_child():

    # completed
    assert_eval_function(evaluators.choose_one_child, api.STATUS_COMPLETED, [], 'choose one with no children should be completed')
    assert_eval_function(evaluators.choose_one_child, api.STATUS_COMPLETED, [api.STATUS_COMPLETED], 'choose one with no children should be completed')
    assert_eval_function(evaluators.choose_one_child, api.STATUS_COMPLETED, [api.STATUS_UNSATISFIED, api.STATUS_UNSATISFIED, api.STATUS_COMPLETED], 'choose one with a completed child and the rest unsatisfied should be completed')

    # satisfied
    assert_eval_function(evaluators.choose_one_child, api.STATUS_SATISFIED, [api.STATUS_SATISFIED], 'choose one with a satisfied child should be satisfied')
    assert_eval_function(evaluators.choose_one_child, api.STATUS_SATISFIED, [api.STATUS_UNSATISFIED, api.STATUS_UNSATISFIED, api.STATUS_SATISFIED], 'choose one with a satisfied child and the rest unsatisfied should be satisfied')

    # unsatisfied
    status = evaluators.choose_one_child([api.STATUS_UNSATISFIED])
    assert status == api.STATUS_UNSATISFIED, 'choose one with only an unsatisfied child should be unsatisfied'
    status = evaluators.choose_one_child([api.STATUS_EXCEEDED])
    assert status == api.STATUS_UNSATISFIED, 'choose one only a exceeded child should be unsatisfied'
    status = evaluators.choose_one_child([api.STATUS_UNSATISFIED, api.STATUS_UNSATISFIED, api.STATUS_EXCEEDED])
    assert status == api.STATUS_UNSATISFIED, 'choose one with any exceeded children should be unsatisfied'

    # exceeded
    status = evaluators.choose_one_child([api.STATUS_UNSATISFIED, api.STATUS_COMPLETED, api.STATUS_SATISFIED])
    assert status == api.STATUS_EXCEEDED, 'choose one with more than one satisfied or completed child should be exceeded'



def test_require_all_children():

    # completed
    status = evaluators.require_all_children([])
    assert status == api.STATUS_COMPLETED, 'require all with no children should be completed'
    status = evaluators.require_all_children([api.STATUS_COMPLETED])
    assert status == api.STATUS_COMPLETED, 'require all with only a completed child should be completed'
    status = evaluators.require_all_children([api.STATUS_COMPLETED, api.STATUS_COMPLETED, api.STATUS_COMPLETED])
    assert status == api.STATUS_COMPLETED, 'require all with all completed children should be completed'

    # satisfied
    status = evaluators.require_all_children([api.STATUS_SATISFIED])
    assert status == api.STATUS_SATISFIED, 'require all with only a satisfied child should be satisfied'
    status = evaluators.require_all_children([api.STATUS_SATISFIED, api.STATUS_SATISFIED, api.STATUS_COMPLETED])
    assert status == api.STATUS_SATISFIED, 'require all with all satisfied or completed children should be satisfied'

    # unsatisfied
    status = evaluators.require_all_children([api.STATUS_UNSATISFIED, api.STATUS_SATISFIED, api.STATUS_COMPLETED])
    assert status == api.STATUS_UNSATISFIED, 'require all with any unsatisfied children should be unsatisfied'
    status = evaluators.require_all_children([api.STATUS_UNSATISFIED, api.STATUS_SATISFIED])
    assert status == api.STATUS_UNSATISFIED, 'require all with any unsatisfied children should be unsatisfied'
    status = evaluators.require_all_children([api.STATUS_EXCEEDED, api.STATUS_COMPLETED])
    assert status == api.STATUS_UNSATISFIED, 'require all with any exceeded children should be unsatisfied'
    status = evaluators.require_all_children([api.STATUS_UNSATISFIED])
    assert status == api.STATUS_UNSATISFIED, 'require all only an unsatisfied child should be unsatisfied'

    # require all cannot be exceeded


def test__children_as_options():

    # completed
    status = evaluators.children_as_options([])
    assert status == api.STATUS_COMPLETED, 'options with no children should be completed'
    status = evaluators.children_as_options([api.STATUS_COMPLETED])
    assert status == api.STATUS_COMPLETED, 'options with a completed child should be completed'
    status = evaluators.children_as_options([api.STATUS_COMPLETED,api.STATUS_COMPLETED,api.STATUS_COMPLETED])
    assert status == api.STATUS_COMPLETED, 'options with all completed children should be completed'

    # satisfied
    status = evaluators.children_as_options([api.STATUS_UNSATISFIED, api.STATUS_UNSATISFIED, api.STATUS_UNSATISFIED])
    assert status == api.STATUS_SATISFIED , 'options with all un-satisfied children should still be satisfied'
    status = evaluators.children_as_options([api.STATUS_COMPLETED,api.STATUS_COMPLETED, api.STATUS_SATISFIED])
    assert status == api.STATUS_SATISFIED , 'options with all satisfied or completed children should be satisfied'

    # unsatisfied
    status = evaluators.children_as_options([api.STATUS_EXCEEDED])
    assert status == api.STATUS_UNSATISFIED, 'options with only an exceeded child should be unsatisfied'
    status = evaluators.children_as_options([api.STATUS_EXCEEDED , api.STATUS_COMPLETED, api.STATUS_COMPLETED])
    assert status == api.STATUS_UNSATISFIED , 'options with any exceeded children should be unsatisfied'

    # options cannot be exceeded




def test_children_as_dir_listing():

    root = node.CmdNode('filecmd', child_get_func=node.get_children_method_dir_listing('dsh/data'))

    path = root.resolve(['filecmd', 'schema.yml'])
    assert path.status == api.STATUS_COMPLETED

    path = root.resolve(['filecmd', 'schema'])
    assert path.status == api.STATUS_UNSATISFIED
    assert 'schema.yml' in path.match_result.completions



def test_shell_command():

    n = node.node_shell_command('testls', 'ls', True)
    assert os.path.pardir in n.execute(api.MatchResult.from_input('-a'), None)



def test_shell_command_var_substitution():

    # repeat the test with variable substitution in the command string
    n = node.node_shell_command('testvarsub', 'echo {{testvar}}', True, ctx={'testvar': 'test val'})
    assert 'test val' in n.execute(api.MatchResult.from_input('testvarsub'), None)



def test_shell_command_extra_input_var_substitution():

    # repeat the test with variable substitution in the command string
    n = node.node_shell_command('testvarsub', 'echo', True, ctx={'testvar': 'test val'})
    assert 'test val' in n.execute(api.MatchResult.from_input('testvarsub {{testvar}}'), None)


