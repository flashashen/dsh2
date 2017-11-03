
import os, yaml, six
import flange
import shell
import node
import executors





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
        return node.node_shell_command(key, val, ctx=ctx, return_output=False)

    # command can be a list of commands (nesting allowed)
    elif isinstance(val, list):
        root = node.CmdNode(key, context=ctx, usage=usage)
        for i, c in enumerate(val):
            root.add_child(node_dsh_cmd(key+'_'+str(i+1), c))
        return root

    # command can be a dict with keys {do,help,env}
    elif isinstance(val, dict):
        root = node.CmdNode(key, context=ctx)
        if 'vars' in val:
            ctx
        root.add_child(node_dsh_cmd(
            key+'_do',
            val['do'],
            ctx=val['vars'] if 'vars' in val else {}))

        return root

    else:
        raise ValueError("value of command {} must be a string, list, or dict. type is {}".format(key, type(val)))



def node_dsh_context(data, name=None, ctx={}):

    if name:
        rootCmd = node.CmdNode(name)
    else:
        rootCmd = node.node_root()


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
