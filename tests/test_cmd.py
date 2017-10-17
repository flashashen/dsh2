from context import *

import six


def test_node_container():

    root = node.node_container('root')
    path = resolver.ResolutionPath(root)

    resolver.resolve(path, [], 0)
    assert path.status == api.STATUS_COMPLETED
    assert path.match_result.status == api.MATCH_FULL
    assert path.match_result.completions == []

    root.add_child('cmd_one').add_child('cmd_two')
    path = resolver.ResolutionPath(root)

    resolver.resolve(path, [''], 0)
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.completions == ['cmd_one', 'cmd_two']

    resolver.resolve(path, ['cmd_one', 'cmd_two'], 0)
    assert path.status == api.STATUS_COMPLETED
    assert path.match_result.completions == []

    resolver.resolve(path, ['cmd_'], 0)
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.completions == ['cmd_one', 'cmd_two']

    resolver.resolve(path, ['cmd_two'], 0)
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.completions == ['cmd_one']

    root.evaluate = evaluators.choose_one_child
    resolver.resolve(path, ['cmd_two'], 0)
    assert path.status == api.STATUS_COMPLETED
    assert path.match_result.completions == []




def test_all_of():

    root = node.node_root().all_of(['cmd_one', 'cmd_two'])
    path = resolver.ResolutionPath(root)

    resolver.resolve(path, ['cmd_one', 'cmd_two'], 0)
    assert path.status == api.STATUS_COMPLETED
    assert path.match_result.completions == []

    resolver.resolve(path, ['cmd_two'], 0)
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.completions == ['cmd_one']


def test_one_of():

    root = node.node_root().one_of(['cmd_one', 'cmd_two'])
    path = resolver.ResolutionPath(root)

    resolver.resolve(path, ['cmd'], 0)
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.completions == ['cmd_one', 'cmd_two']

    resolver.resolve(path, ['cmd_two'], 0)
    assert path.status == api.STATUS_COMPLETED
    assert path.match_result.completions == []




def test_nested_containers():

    root = node.node_container()
    path = resolver.ResolutionPath(root)
    root.all_of(['cmd_one', node.CmdNode('cmd_two').one_of(['opt1', 'opt2'])])

    resolver.resolve(path, ['cmd_one', 'cmd_two', 'opt1'])
    assert path.status == api.STATUS_COMPLETED
    assert path.match_result.completions == []

    resolver.resolve(path, ['cmd_one', 'cmd_two', 'op'])
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.completions == ['opt1', 'opt2']

    resolver.resolve(path, ['cmd_two', 'op'])
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.completions == ['opt1', 'opt2']

    resolver.resolve(path, ['cmd_two', 'opt1'])
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.completions == ['cmd_one']



def test_peer_containers():

    root = node.node_container()
    path = resolver.ResolutionPath(root)
    root.all_of(['cmd_one', 'cmd_two'])
    root.one_of(['cmd_three', 'cmd_four'])

    resolver.resolve(path, [''], 0)
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.completions == ['cmd_one', 'cmd_two', 'cmd_three', 'cmd_four']

    resolver.resolve(path, ['cmd_one', 'cmd_two', 'cmd_four'], 0)
    assert path.status == api.STATUS_COMPLETED
    assert path.match_result.completions == []

    resolver.resolve(path, ['cmd_one', 'cmd_two'], 0)
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.completions == ['cmd_three', 'cmd_four']

    resolver.resolve(path, ['cmd_three'], 0)
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.completions == ['cmd_one', 'cmd_two']


    # run(node.node_root().add_child(node.CmdNode('cmd')), 'f')


def test_node_argument():
    assert resolver.run(node.node_argument('arg'), 'arg somefreevalue') == 'somefreevalue'
    assert resolver.run(node.node_root().add_child(node.node_argument('arg')), 'arg somefreevalue') == 'somefreevalue'




def test_node_options():

    root = node.CmdNode('root', method_evaluate=evaluators.require_all_children).options(['opt1', 'opt2']).add_child('cmd')
    path = resolver.ResolutionPath(root)

    resolver.resolve(path, ['root'], 0)
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.completions == ['opt1', 'opt2', 'cmd']

    resolver.resolve(path, ['root', 'cmd'], 0)
    assert path.status == api.STATUS_SATISFIED
    assert path.match_result.completions == ['opt1', 'opt2']

    resolver.resolve(path, ['root', 'opt1'], 0)
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.completions == ['opt2', 'cmd']

    # After the first option is supplied and then followed by a non-option
    # the second option should be presented as a completion
    resolver.resolve(path, ['root', 'cmd', 'opt1'], 0)
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
    do = node.node_python(
        'do',
        test_method,
        required,
        optional,
        options)
    path = resolver.ResolutionPath(do)

    resolver.resolve(path, ['do'], 0)
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.completions == ['-a', '-b', 'arg1', 'arg2']

    resolver.resolve(path, ['do', 'arg1'], 0)
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.completions == []

    # resolver.resolve(path, ['do', 'arg1', 'val1'], 0)
    # assert path.status == api.STATUS_UNSATISFIED
    # assert path.match_result.completions == ['arg2', '-a', '-b']





def test_resolve_sequence_hosts_duplicated():

    # root = one_of('root', 'choice1', 'choice2')
    # path = ResolutionPath(root)
    # resolver.resolve(path, ['root','invalid'], 0)
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

    path = resolver.ResolutionPath(root)
    resolver.resolve(path, ['ans','list', 'groups', 'playbooks'], 0)
    assert path.match_result.completions == ['hosts']




def test_root_doesnt_resolve_if_children_cant_resolve():

    root = node.CmdNode('root').one_of(['choice1', 'choice2'])
    path = resolver.ResolutionPath(root)
    resolver.resolve(path, ['root','invalid'], 0)

    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.completions == []



def test_full_and_fragment_siblings_same_prefix():

    root = node.CmdNode('root').one_of(['prefix', 'prefix_and_suffix'])
    path = resolver.ResolutionPath(root)
    resolver.resolve(path, ['root','prefix'], 0)

    # The root is satisfied since child 'prefix' is completed by the input
    assert path.status == api.STATUS_SATISFIED
    # Even though root is satisfied completions from 'prefix_and_suffix' child should be offered
    assert path.match_result.completions == ['prefix_and_suffix']



def test_resolve_sequence_all_one_one():

    # root = one_of('root', 'choice1', 'choice2')
    # path = ResolutionPath(root)
    # resolver.resolve(path, ['root','invalid'], 0)
    #
    # assert path.status == api.STATUS_UNSATISFIED
    # assert path.match_result.completions == []

    root = node.CmdNode('ans').all_of(
                  [node.CmdNode('play').one_of(['website.yml', 'appserver.yml']),
                   node.CmdNode('list').one_of(['groups', 'hosts', 'playbooks'])])

    path = resolver.ResolutionPath(root)
    resolver.resolve(path, ['ans','pl'], 0)
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.status == api.MATCH_FULL
    assert path.match_result.completions == ['play']

    path = resolver.ResolutionPath(root)
    resolver.resolve(path, ['ans','play'], 0)
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.status == api.MATCH_FULL
    assert path.match_result.completions == ['website.yml','appserver.yml']

    path = resolver.ResolutionPath(root)
    resolver.resolve(path, ['ans','play', 'website.yml'], 0)
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.status == api.MATCH_FULL
    assert path.match_result.completions == ['list']

    path = resolver.ResolutionPath(root)
    resolver.resolve(path, ['ans','play', 'website.yml', 'li'], 0)
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.status == api.MATCH_FULL
    assert path.match_result.completions == ['list']

    path = resolver.ResolutionPath(root)
    resolver.resolve(path, ['ans','play', 'website.yml', 'list'], 0)
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.status == api.MATCH_FULL
    assert path.match_result.completions == ['groups','hosts','playbooks']

    path = resolver.ResolutionPath(root)
    resolver.resolve(path, ['ans','play', 'website.yml', 'list', 'g'], 0)
    assert path.status == api.STATUS_UNSATISFIED
    assert path.match_result.status == api.MATCH_FULL
    assert path.match_result.completions == ['groups']

    path = resolver.ResolutionPath(root)
    resolver.resolve(path, ['ans','play', 'website.yml', 'list', 'groups'], 0)
    assert path.status == api.STATUS_COMPLETED
    assert path.match_result.status == api.MATCH_FULL
    assert path.match_result.completions == []


def test_execute():

    def test_cmd(ctx, match_result, child_results):
        print 'executing test cmd. play={}, list={}'.format(child_results['play'], child_results['list'])

    n = node.CmdNode('ans', method_execute=test_cmd, method_evaluate=evaluators.require_all_children)
    n.add([node.node_choose_value_for('play', ['website.yml', 'appserver.yml']),
                       node.node_choose_value_for('list', ['groups', 'hosts', 'playbooks'])])

    path = resolver.ResolutionPath(n)
    resolver.resolve(path, ['ans','play', 'website.yml', 'list', 'groups'], 0)

    ctx = {}
    resolver.execute(path, ctx)
    # print ctx

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

    n = node.CmdNode('filecmd', child_get_func=node.get_children_method_dir_listing())
    path = resolver.ResolutionPath(n)

    resolver.resolve(path, ['filecmd', 'tests'], 0)
    assert path.status == api.STATUS_COMPLETED

    resolver.resolve(path, ['filecmd', 'te'], 0)
    assert path.status == api.STATUS_UNSATISFIED
    assert 'tests' in path.match_result.completions


    # resolver.resolve(path, ['filecmd', 'test_proto.pyc'], 0)
    # assert path.status == api.STATUS_COMPLETED
    # assert path.match_result.status == api.MATCH_FULL


#
# def get_root():
#     p1 = node.CmdNode('ans', eval_func=choose_one_child)
#     p1.add_child(node.CmdNode('list'))
#     p1.add_child(node.CmdNode('play'))
#     # p1.add_child(play())
#     # p1.add_child(list())
#
#     # p1.add_child(node.CmdNode('list'))
#     # p1.children[0].add_child(node.CmdNode('app1_1', True))
#     # p1.children[0].add_child(node.CmdNode('app1_2', True))
#     # p1.children[0].add_tag('testtag')
#     # p1.add_rule_one_of('testtag')
#     return p1



#
# def node.node_play():
#     p = node.CmdNode('play', )
#     for book in playbooks:
#         p.add_child(node.CmdNode(book))
#     return p
#
#
# def node.node_list():
#     p = node.CmdNode('list')
#     p.add_child(node.CmdNode('groups'))
#     p.add_child(node.CmdNode('hosts'))
#     p.add_child(node.CmdNode('playbooks'))
#     return p

#
# def test_resolver.resolve():
#     print get_root().children
#     res = get_root().complete('ans')
#     print res





from executors import get_executor_shell
#
#
# def create_cmd_node(key, val, ctx):
#     """
#     handles "#/definitions/type_command"
#
#     :param key:
#     :param val:
#     :param ctx:
#     :return:
#     """
#     # command can be specified by a simple string
#     if isinstance(val, six.string_types):
#         return node.CmdNode(key, context=ctx, method_execute=get_executor_shell(val))
#
#     # command can be a list of commands (nesting allowed)
#     elif isinstance(val, list):
#         root = node.CmdNode(key, context=ctx)
#         for i,c in enumerate(val):
#             root.add_child(create_cmd_node(key+'_'+str(i+1)),val)
#         return root
#
#     # command can be an dict with keys {do,help,env}
#     elif isinstance(val, dict):
#         root = node.CmdNode(key, context=ctx)
#         root.add_child(create_cmd_node(key+'_do',val, ctx=val['vars']))
#         # for do in val['do']:
#         #     if isinstance(val, six.string_types):
#         #         return node.CmdNode(key, context=ctx, method_execute=get_executor_shell(val))
#         #     elif isinstance(do, list):
#         #         root.add_child(create_cmd_node('do',val))
#         #     else:
#         #         raise ValueError("value of 'do' in command configuration must be a string of a list. type is {}".format(type(do)))
#         return root
#
#     else:
#         raise ValueError("value of command {} must be a string, list, or dict. type is {}".format(key, type(val)))
#
#
#
# def get_node(data):
#     rootCmd = node.CmdNode('root')
#     for key,val in data.iteritems():
#         ctx = {}
#         if key == 'dsh':
#             pass
#         elif key == 'ns':
#             print 'ns', val
#         elif key == 'vars':
#             ctx = val
#             print 'vars', val
#         elif key == 'context':
#             print 'contexts', val
#         else:
#             rootCmd.add_child(create_cmd_node(key,val, ctx))
#     return rootCmd
#
#
#
# DSH_FLANGE_PLUGIN = {'dshnode': {
#         'type': 'FLANGE.TYPE.PLUGIN',
#         'schema': 'python://{}.dsh_schema'.format(MODULE_NAME),
#         'factory': 'python://{}.get_node'.format(MODULE_NAME)
#     }
# }
