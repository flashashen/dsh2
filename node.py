import sys, subprocess, six, os
from api import *
from matchers import *
from executors import *
import evaluators


def get_children_method_dir_listing():
    import glob
    return lambda self, ctx: [CmdNode(p) for p in glob.glob('*')]



def choose_value_for(name, *choices):
    node = CmdNode(name, method_evaluate=evaluators.choose_one_child)
    for choice in choices:
        def f(ctx):
            ctx[name] = str(name)
        node.add_child(CmdNode(choice, method_execute=f))
    # node.add_children(choices)
    return node


def one_of(name, *choices):
    node = CmdNode(name, method_evaluate=evaluators.choose_one_child)
    node.add_children(choices)
    return node

def all_of(name, *choices):
    node = CmdNode(name, method_evaluate=evaluators.require_all_children)
    node.add_children(choices)
    return node

def options(name, *options):
    node = CmdNode(name, method_evaluate=evaluators.children_as_options)
    node.add_children(options)
    return node




class CmdNode(object):

    def __init__(self,
                 name,
                 method_execute=None,
                 method_match=None,
                 method_evaluate=None,
                 child_get_func=None,
                 context=None):

        self.name = name
        self.context = context if context else {}

        self.execute = method_execute if method_execute else lambda ctx: None
        self.match = method_match if method_match else get_matcher_exact_string(name)
        self.evaluate = method_evaluate if method_evaluate else evaluators.choose_one_child

        if child_get_func:
            self.get_children = child_get_func.__get__(self, CmdNode)
        else:
            self.get_children = self.__get_static_children
            self.__children = []



    def __repr__(self):
            return "<CmdNode:{} children={}>".format(self.name, str(self.__children))

    # def execute(self, str_input):
    #     print "execute {} called on '{}'".format(self.name, str_input)

    def get_children(self):
        return self.__children




    # The add children methods no longer belong here since children are not necessarily
    # a static list anymore. They could instead be put into a list and contained in a
    # closure that returns them

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



# class CmdOption(CmdNode):




#
#
#   Flange setup
#
#



def create_cmd_node(key, val, ctx):
    """
    handles "#/definitions/type_command"

    :param key:
    :param val:
    :param ctx:
    :return:
    """
    # command can be specified by a simple string
    if isinstance(val, six.string_types):
        return CmdNode(key, context=ctx, method_execute=get_executor_shell(val))

    # command can be a list of commands (nesting allowed)
    elif isinstance(val, list):
        root = CmdNode(key, context=ctx)
        for i,c in enumerate(val):
            root.add_child(create_cmd_node(key+'_'+str(i+1)),val)
        return root

    # command can be an dict with keys {do,help,env}
    elif isinstance(val, dict):
        root = CmdNode(key, context=ctx)
        root.add_child(create_cmd_node(key+'_do',val, ctx=val['vars']))
        # for do in val['do']:
        #     if isinstance(val, six.string_types):
        #         return CmdNode(key, context=ctx, method_execute=get_executor_shell(val))
        #     elif isinstance(do, list):
        #         root.add_child(create_cmd_node('do',val))
        #     else:
        #         raise ValueError("value of 'do' in command configuration must be a string of a list. type is {}".format(type(do)))
        return root

    else:
        raise ValueError("value of command {} must be a string, list, or dict. type is {}".format(key, type(val)))



def get_instance(data):
    rootCmd = CmdNode('root')
    for key,val in data.iteritems():
        ctx = {}
        if key == 'dsh':
            pass
        elif key == 'ns':
            print 'ns', val
        elif key == 'vars':
            ctx = val
            print 'vars', val
        elif key == 'context':
            print 'contexts', val
        else:
            rootCmd.add_child(create_cmd_node(key,val, ctx))
    return rootCmd




import yaml
with open(os.path.join(os.path.dirname(os.path.realpath(__file__)),'schema.yml')) as f:
    DSH_SCHEMA = yaml.load(f)

MODULE_NAME = __name__.replace('.','/')


def dsh_schema():
    return DSH_SCHEMA


DSH_FLANGE_PLUGIN = {'cmdctx': {
    'type': 'FLANGE.TYPE.PLUGIN',
    'schema': 'python://{}.dsh_schema'.format(MODULE_NAME),
    'factory': 'python://{}.get_instance'.format(MODULE_NAME)
}}