import jsonschema, yaml
from dsh import main, node, evaluators, matchers, api, executors

from flange import cfg, model as flmd

from click.testing import CliRunner


FG = cfg.Cfg(
    data=main.DSH_FLANGE_PLUGIN,
    root_path='prj',
    file_patterns=['example.yml'],
    base_dir='.',
    file_search_depth=1)


import os
PATH_EXAMPLE = os.path.join(os.path.dirname(__file__), 'example.yml')
with open(PATH_EXAMPLE) as f:
    DSH_EXAMPLE = yaml.safe_load(f)


MODULE_NAME = __name__.replace('.', '/')




def test_dsh_schema():

    # First make sure the example conforms to the schema
    jsonschema.validate(DSH_EXAMPLE, main.DSH_SCHEMA)

    # Then, check that flange discovers the example as in instance of the model
    f = cfg.from_file('tests/example.yml', root_path='root',)
    f.register_model('dshnode', flmd.Model('dshnode', flmd.Model.get_schema_validator(main.DSH_SCHEMA), main.node_factory_context))
    assert f.obj('root', model='dshnode')


def test_config_model_registration():
    # The initial data contains the test plugin registation
    cmdroot = FG.obj('prj')

    path = cmdroot.resolve('platform')
    assert path.match_result.completions == ['up', 'stop', 'ps', 'build']

    path = cmdroot.resolve('platform build')
    assert path.match_result.completions == []


def test_context_vars():

    cmdroot = FG.obj('prj')
    prod = [x for x in cmdroot.get_children() if x.name == 'prod'][0]



def test_nested_do():

    cmdroot = FG.obj('prj')
    path = cmdroot.resolve('cmd_do_nested')
    path.execute()
    print(cmdroot)



def test_on_failure():
    cmdroot = FG.obj('prj')
    cmdroot.resolve('platform build', 'MODE_EXECUTE').execute()



# def test_context_cmd_do_after_simple():
#
#     cmdroot = FG.obj('tests', model='dshnode')
#     path = cmdroot.resolve('platform build')
#     path.execute()
#     print cmdroot
#

# def test_main():

#     data = {
        
#     }
#     f = main.get_flange_cfg(
#         options=None,
#         root_ns=main.DSH_DEFAULT_ROOT,
#         base_dir=['test'],
#         file_patterns=['.dsh*.yml'],
#         file_search_depth=0,
#         initial_data=data)

#     roots = f.objs(main.DSH_DEFAULT_ROOT, model='dshnode')
#     assert roots
 


# def test_cli():
#   runner = CliRunner()
#   result = runner.invoke(main.cli, ['--exist_on_init', True])
#   assert result.exit_code == 0
