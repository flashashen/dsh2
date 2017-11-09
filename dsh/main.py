
import os, yaml, six
import flange
import shell
import node
import evaluators
import matchers





with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'schema.yml')) as f:
    DSH_SCHEMA = yaml.load(f)

def dsh_schema():
    return DSH_SCHEMA


DSH_FLANGE_PLUGIN = {'dshnode': {
    'type': 'FLANGE.TYPE.PLUGIN',
    'schema': 'python://dsh/main.dsh_schema',
    'factory': 'python://dsh/main.node_dsh_context'
}}





def node_dsh_cmd(key, val, ctx={}, usage=None):
    """
    handles "#/definitions/type_command"

    :param key:
    :param val:
    :param ctx:
    :return:
    """
    # command can be specified by a simple string
    if isinstance(val, six.string_types):
        root = node.CmdNode(key, context=ctx, usage=usage, method_evaluate=evaluators.require_all_children)
        n = node.node_shell_command(key+"_cmdstr", val, ctx=ctx, return_output=False)
        n.match = matchers.match_always_consume_no_input
        root.add_child(n)
        return root

    # command can be a list of commands (nesting allowed)
    elif isinstance(val, list):
        root = node.CmdNode(key, context=ctx, usage=usage, method_evaluate=evaluators.require_all_children)
        # add child cmds
        for i, c in enumerate(val):
            cn = node_dsh_cmd(key+'_'+str(i+1), c, ctx=ctx)
            root.add_child(cn)
            # swallow completions
            cn.match = matchers.match_always_consume_no_input
            # cn.evaluate = evaluators.require_all_children

        return root

    # command can be a dict with keys {do,help,env}
    elif isinstance(val, dict):
        root = node.CmdNode(key, context=ctx, method_evaluate=evaluators.require_all_children)

        newctx = ctx.copy()
        if 'vars' in val:
            newctx.update(val['vars'])

        cn = node_dsh_cmd(
            key+'_do_dict',
            val['do'],
            ctx=newctx)
        root.add_child(cn)
        # swallow completions
        cn.match = matchers.match_always_consume_no_input
        # cn.evaluate = evaluators.require_all_children

        return root

    else:
        raise ValueError("value of command {} must be a string, list, or dict. type is {}".format(key, type(val)))



def node_dsh_context(data, name=None, ctx={}):

    if name:
        # a named command is not the root
        rootCmd = node_shell(name, ctx)
    else:
        rootCmd = node.node_root('dsh')


    # the env/ctx for this context will be the parent plus any new vars defined
    # with new vars overwriting the old
    newctx = ctx.copy()
    if 'vars' in data:
        newctx.update(data['vars'])

    # Set namespace though nothing is done with it yet
    ns = data['ns'] if 'ns' in data else ''

    # Process the remaining keys
    for key, val in data.iteritems():
        if key in ['dsh', 'vars', 'ns']:
            pass
        elif key == 'contexts':
            for k, v in val.items():
                rootCmd.add_child(node_dsh_context(v, k, ctx=newctx))
        elif key == 'commands':
            for k, v in val.items():
                rootCmd.add_child(node_dsh_cmd(k, v, newctx))
        else:
            rootCmd.add_child(node_dsh_cmd(key, val, newctx))
    return rootCmd





def node_shell(name, ctx=None):

    snode = node.CmdNode(name, context=ctx)
    snode.execute = lambda match_result, child_results: execute_context(snode, match_result, child_results)
    return snode



def execute_context(snode, match_result, child_results):

    # If child node results are available, then this node is assumed to be
    # at the end of the input and will act as a interactive subcontext/shell
    matched_input = match_result.matched_input()
    if len(matched_input) == 1 and matched_input[0] == snode.name and not match_result.input_remainder():
        cnode = node.node_root(snode.context)
        cnode.name = snode.name
        for child in snode.get_children():
            cnode.add_child(child)
        return shell.run(cnode)

    # If there are children that returned a result, then just pass those on.
    # In this case the given node is acting as a container
    if child_results:
        return child_results



def get_executor_shell(cnode):
    return lambda ctx, matched_input, child_results: execute_context(cnode, ctx, child_results)






def main():

    import flange
    FG = flange.Flange(
        data=DSH_FLANGE_PLUGIN,
        root_ns='prj',
        file_patterns=['.cmd.*'],
        base_dir='~/workspace',
        file_search_depth=2)


    root = FG.mget('sire6')


    shell.run(root)



if __name__ == '__main__':
    main()
