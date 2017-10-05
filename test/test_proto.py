from node import *
from resolver import *
from evaluators import *
import six


#
#    Test completions resolution
#


def test_resolve_sequence_hosts_duplicated():

    # root = one_of('root', 'choice1', 'choice2')
    # path = ResolutionPath(root)
    # resolve(path, ['root','invalid'], 0)
    #
    # assert path.status == STATUS_UNSATISFIED
    # assert path.match_result.completions == []

    root = CmdNode('ans', method_evaluate=require_all_children)
    root.add_children([choose_value_for('play', ['website.yml', 'appserver.yml']),
                       all_of('list', 'groups', 'hosts', 'playbooks') ])

    path = ResolutionPath(root)
    resolve(path, ['ans','list', 'groups', 'playbooks'], 0)
    assert path.match_result.completions == ['hosts']




def test_root_doesnt_resolve_if_children_cant_resolve():

    root = one_of('root', 'choice1', 'choice2')
    path = ResolutionPath(root)
    resolve(path, ['root','invalid'], 0)

    assert path.status == STATUS_UNSATISFIED
    assert path.match_result.completions == []



def test_full_and_fragment_siblings_same_prefix():

    root = one_of('root', 'prefix', 'prefix_and_suffix')
    path = ResolutionPath(root)
    resolve(path, ['root','prefix'], 0)

    # The root is satisfied since child 'prefix' is completed by the input
    assert path.status == STATUS_SATISFIED
    # Even though root is satisfied completions from 'prefix_and_suffix' child should be offered
    assert path.match_result.completions == ['prefix_and_suffix']



def test_resolve_sequence_all_one_one():

    # root = one_of('root', 'choice1', 'choice2')
    # path = ResolutionPath(root)
    # resolve(path, ['root','invalid'], 0)
    #
    # assert path.status == STATUS_UNSATISFIED
    # assert path.match_result.completions == []

    root = all_of('ans',
                  one_of('play', 'website.yml', 'appserver.yml'),
                  one_of('list', 'groups', 'hosts', 'playbooks') )

    path = ResolutionPath(root)
    resolve(path, ['ans','pl'], 0)
    assert path.status == STATUS_UNSATISFIED
    assert path.match_result.status == MATCH_FULL
    assert path.match_result.completions == ['play']

    path = ResolutionPath(root)
    resolve(path, ['ans','play'], 0)
    assert path.status == STATUS_UNSATISFIED
    assert path.match_result.status == MATCH_FULL
    assert path.match_result.completions == ['website.yml','appserver.yml']

    path = ResolutionPath(root)
    resolve(path, ['ans','play', 'website.yml'], 0)
    assert path.status == STATUS_UNSATISFIED
    assert path.match_result.status == MATCH_FULL
    assert path.match_result.completions == ['list']

    path = ResolutionPath(root)
    resolve(path, ['ans','play', 'website.yml', 'li'], 0)
    assert path.status == STATUS_UNSATISFIED
    assert path.match_result.status == MATCH_FULL
    assert path.match_result.completions == ['list']

    path = ResolutionPath(root)
    resolve(path, ['ans','play', 'website.yml', 'list'], 0)
    assert path.status == STATUS_UNSATISFIED
    assert path.match_result.status == MATCH_FULL
    assert path.match_result.completions == ['groups','hosts','playbooks']

    path = ResolutionPath(root)
    resolve(path, ['ans','play', 'website.yml', 'list', 'g'], 0)
    assert path.status == STATUS_UNSATISFIED
    assert path.match_result.status == MATCH_FULL
    assert path.match_result.completions == ['groups']

    path = ResolutionPath(root)
    resolve(path, ['ans','play', 'website.yml', 'list', 'groups'], 0)
    assert path.status == STATUS_COMPLETED
    assert path.match_result.status == MATCH_FULL
    assert path.match_result.completions == []


def test_execute():

    def test_cmd(ctx):
        print 'executing test cmd. play={}, list={}'.format(ctx['play'],ctx['list'])

    node = CmdNode('ans', method_execute=test_cmd, method_evaluate=require_all_children)
    node.add_children([choose_value_for('play', 'website.yml', 'appserver.yml'),
                       choose_value_for('list', 'groups', 'hosts', 'playbooks')])

    path = ResolutionPath(node)
    resolve(path, ['ans','play', 'website.yml', 'list', 'groups'], 0)

    ctx = {}
    execute(path, ctx)
    # print ctx

#
#    Test match functions
#


def assert_match_result(result, expected_status, expected_completions=None):

    assert result.status != None, 'match status be one of pre-defined values'
    assert result.status == expected_status
    assert result.start != None and result.stop != None, 'start and stop must have a value in all cases. Use 0 as default'

    if result.status == MATCH_NONE:
        assert result.start == result.stop, 'MATCH_NONE must consume no input, ie, start should equal stop'
        assert not result.completions, 'MATCH_NONE should have no completions'

    elif result.status == MATCH_EMPTY:
        assert result.start == result.stop, 'MATCH_EMPTY must consume no input, ie, start should equal stop'

    elif result.status == MATCH_FRAGMENT:
        assert result.start+1 == result.stop, 'MATCH_FRAGMENT must consume one input, ie, start+1 should equal stop'

    elif result.status == MATCH_FULL:
        assert result.start < result.stop, 'MATCH_FULL must consume some input, ie, stop should be greater than start'
        assert not result.completions, 'MATCH_FULL should have no completions'

    assert not expected_completions or expected_completions[result.status] == result.completions, 'completions did not match expected'


def assert_match_function_result_common(func, node, match_target, expected_completions=None):

    # node.match = func.__get__(node, None)

    # test None and empty and consumed inputs return MATCH_EMPTY
    assert_match_result(func( None), MATCH_EMPTY, expected_completions)
    assert_match_result(func( None, 0), MATCH_EMPTY, expected_completions)
    assert_match_result(func( []), MATCH_EMPTY, expected_completions)
    assert_match_result(func( [], 0), MATCH_EMPTY, expected_completions)
    assert_match_result(func( ['dontcare'], 1), MATCH_EMPTY, expected_completions)

    # test fragment, full and extra as only input
    assert_match_result(func( [match_target[:-1]], 0), MATCH_FRAGMENT, expected_completions)
    assert_match_result(func( [match_target], 0), MATCH_FULL, expected_completions)
    assert_match_result(func( [match_target+'inhibitmatch'], 0), MATCH_NONE, expected_completions)
    assert_match_result(func( ['inhibitmatch'], 0), MATCH_NONE, expected_completions)

    # test fragment, full and extra in middle of input
    assert_match_result(func( ['dontcare1', 'dontcare2', match_target, 'dontcare3'], 2), MATCH_FULL, expected_completions)
    assert_match_result(func( ['dontcare1', 'dontcare2', match_target[:-1], 'dontcare3'], 2), MATCH_FRAGMENT, expected_completions)
    assert_match_result(func( ['dontcare1', 'dontcare2', match_target+'inhibitmatch', 'dontcare3'], 2), MATCH_NONE, expected_completions)



def get_standard_completions(match_target):
    """
    mapping of match status to completion list for the standard case of simple matching
    and completing against a word

    :param match_target: The word/command/name to match against
    :return: dict of status:[completions]
    """
    return {
        MATCH_NONE: [],
        MATCH_EMPTY: [match_target],
        MATCH_FRAGMENT: [match_target],
        MATCH_FULL: []
    }



def test_match_string():
    node = CmdNode('testcmd')
    assert_match_function_result_common(get_matcher_exact_string(node.name), node, node.name, get_standard_completions(node.name) )



#
#   Test child status evaluation functions
#


def assert_eval_function(func, expected, statuses, error_message):
    result = func(statuses)
    assert result == expected, error_message


def test_choose_one_child():

    # completed
    assert_eval_function(choose_one_child, STATUS_COMPLETED, [], 'choose one with no children should be completed')
    assert_eval_function(choose_one_child, STATUS_COMPLETED, [STATUS_COMPLETED], 'choose one with no children should be completed')
    assert_eval_function(choose_one_child, STATUS_COMPLETED, [STATUS_UNSATISFIED, STATUS_UNSATISFIED, STATUS_COMPLETED], 'choose one with a completed child and the rest unsatisfied should be completed')

    # satisfied
    assert_eval_function(choose_one_child, STATUS_SATISFIED, [STATUS_SATISFIED], 'choose one with a satisfied child should be satisfied')
    assert_eval_function(choose_one_child, STATUS_SATISFIED, [STATUS_UNSATISFIED, STATUS_UNSATISFIED, STATUS_SATISFIED], 'choose one with a satisfied child and the rest unsatisfied should be satisfied')

    # unsatisfied
    status = choose_one_child([STATUS_UNSATISFIED])
    assert status == STATUS_UNSATISFIED, 'choose one with only an unsatisfied child should be unsatisfied'
    status = choose_one_child([STATUS_EXCEEDED])
    assert status == STATUS_UNSATISFIED, 'choose one only a exceeded child should be unsatisfied'
    status = choose_one_child([STATUS_UNSATISFIED, STATUS_UNSATISFIED, STATUS_EXCEEDED])
    assert status == STATUS_UNSATISFIED, 'choose one with any exceeded children should be unsatisfied'

    # exceeded
    status = choose_one_child([STATUS_UNSATISFIED, STATUS_COMPLETED, STATUS_SATISFIED])
    assert status == STATUS_EXCEEDED, 'choose one with more than one satisfied or completed child should be exceeded'



def test_require_all_children():

    # completed
    status = require_all_children([])
    assert status == STATUS_COMPLETED, 'require all with no children should be completed'
    status = require_all_children([STATUS_COMPLETED])
    assert status == STATUS_COMPLETED, 'require all with only a completed child should be completed'
    status = require_all_children([STATUS_COMPLETED, STATUS_COMPLETED, STATUS_COMPLETED])
    assert status == STATUS_COMPLETED, 'require all with all completed children should be completed'

    # satisfied
    status = require_all_children([STATUS_SATISFIED])
    assert status == STATUS_SATISFIED, 'require all with only a satisfied child should be satisfied'
    status = require_all_children([STATUS_SATISFIED, STATUS_SATISFIED, STATUS_COMPLETED])
    assert status == STATUS_SATISFIED, 'require all with all satisfied or completed children should be satisfied'

    # unsatisfied
    status = require_all_children([STATUS_UNSATISFIED, STATUS_SATISFIED, STATUS_COMPLETED])
    assert status == STATUS_UNSATISFIED, 'require all with any unsatisfied children should be unsatisfied'
    status = require_all_children([STATUS_UNSATISFIED, STATUS_SATISFIED])
    assert status == STATUS_UNSATISFIED, 'require all with any unsatisfied children should be unsatisfied'
    status = require_all_children([STATUS_EXCEEDED, STATUS_COMPLETED])
    assert status == STATUS_UNSATISFIED, 'require all with any exceeded children should be unsatisfied'
    status = require_all_children([STATUS_UNSATISFIED])
    assert status == STATUS_UNSATISFIED, 'require all only an unsatisfied child should be unsatisfied'

    # require all cannot be exceeded


def test_children_as_options():

    # completed
    status = children_as_options([])
    assert status == STATUS_COMPLETED, 'options with no children should be completed'
    status = children_as_options([STATUS_COMPLETED])
    assert status == STATUS_COMPLETED, 'options with a completed child should be completed'
    status = children_as_options([STATUS_COMPLETED,STATUS_COMPLETED,STATUS_COMPLETED])
    assert status == STATUS_COMPLETED, 'options with all completed children should be completed'

    # satisfied
    status = children_as_options([STATUS_UNSATISFIED, STATUS_UNSATISFIED, STATUS_UNSATISFIED])
    assert status == STATUS_SATISFIED , 'options with all un-satisfied children should still be satisfied'
    status = children_as_options([STATUS_COMPLETED,STATUS_COMPLETED, STATUS_SATISFIED])
    assert status == STATUS_SATISFIED , 'options with all satisfied or completed children should be satisfied'

    # unsatisfied
    status = children_as_options([STATUS_EXCEEDED])
    assert status == STATUS_UNSATISFIED, 'options with only an exceeded child should be unsatisfied'
    status = children_as_options([STATUS_EXCEEDED , STATUS_COMPLETED, STATUS_COMPLETED])
    assert status == STATUS_UNSATISFIED , 'options with any exceeded children should be unsatisfied'

    # options cannot be exceeded




def test_children_as_dir_listing():

    node = CmdNode('filecmd', child_get_func=get_children_method_dir_listing())
    path = ResolutionPath(node)
    resolve(path, ['filecmd', 'test'], 0)
    assert path.status == STATUS_UNSATISFIED
    assert 'test_proto.py' in path.match_result.completions

    # resolve(path, ['filecmd', 'test_proto.pyc'], 0)
    # assert path.status == STATUS_COMPLETED
    # assert path.match_result.status == MATCH_FULL


#
# def get_root():
#     p1 = CmdNode('ans', eval_func=choose_one_child)
#     p1.add_child(CmdNode('list'))
#     p1.add_child(CmdNode('play'))
#     # p1.add_child(play())
#     # p1.add_child(list())
#
#     # p1.add_child(CmdNode('list'))
#     # p1.children[0].add_child(CmdNode('app1_1', True))
#     # p1.children[0].add_child(CmdNode('app1_2', True))
#     # p1.children[0].add_tag('testtag')
#     # p1.add_rule_one_of('testtag')
#     return p1



#
# def node_play():
#     p = CmdNode('play', )
#     for book in playbooks:
#         p.add_child(CmdNode(book))
#     return p
#
#
# def node_list():
#     p = CmdNode('list')
#     p.add_child(CmdNode('groups'))
#     p.add_child(CmdNode('hosts'))
#     p.add_child(CmdNode('playbooks'))
#     return p

#
# def test_resolve():
#     print get_root().children
#     res = get_root().complete('ans')
#     print res




import yaml, flange, jsonschema
with open('../schema.yml') as f:
    DSH_SCHEMA = yaml.load(f)
with open('example.yml') as f:
    DSH_EXAMPLE = yaml.load(f)

MODULE_NAME = __name__.replace('.','/')



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
#         return CmdNode(key, context=ctx, method_execute=get_executor_shell(val))
#
#     # command can be a list of commands (nesting allowed)
#     elif isinstance(val, list):
#         root = CmdNode(key, context=ctx)
#         for i,c in enumerate(val):
#             root.add_child(create_cmd_node(key+'_'+str(i+1)),val)
#         return root
#
#     # command can be an dict with keys {do,help,env}
#     elif isinstance(val, dict):
#         root = CmdNode(key, context=ctx)
#         root.add_child(create_cmd_node(key+'_do',val, ctx=val['vars']))
#         # for do in val['do']:
#         #     if isinstance(val, six.string_types):
#         #         return CmdNode(key, context=ctx, method_execute=get_executor_shell(val))
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
# def get_instance(data):
#     rootCmd = CmdNode('root')
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
# DSH_FLANGE_PLUGIN = {'cmdctx': {
#         'type': 'FLANGE.TYPE.PLUGIN',
#         'schema': 'python://{}.dsh_schema'.format(MODULE_NAME),
#         'factory': 'python://{}.get_instance'.format(MODULE_NAME)
#     }
# }

def test_dsh_schema():

    # First make sure the example conforms to the schema
    jsonschema.validate(DSH_EXAMPLE, DSH_SCHEMA)

    # Then, check that flange discovers the example as in instance of the model
    f = flange.from_file('example.yml',root_ns='root',)
    f.register('cmdctx', DSH_SCHEMA)
    assert f.get('root', 'cmdctx')


def test_flange_config_model_registration():
    # The initial data contains the test plugin registation
    f = flange.Flange(data = DSH_FLANGE_PLUGIN, root_ns='prj', file_patterns=['.cmd.yml'], base_dir='~/workspace', file_search_depth=2)
    assert f.get('dsh', 'cmdctx')

