import jsonschema, yaml
from context import *
from flange import cfg, model as flmd


FG = cfg.Cfg(
    data=main.DSH_FLANGE_PLUGIN,
    root_path='prj',
    file_patterns=['example.yml'],
    base_dir='.',
    file_search_depth=1)


import os
PATH_EXAMPLE = os.path.join(os.path.dirname(__file__), 'example.yml')
with open(PATH_EXAMPLE) as f:
    DSH_EXAMPLE = yaml.load(f)


MODULE_NAME = __name__.replace('.', '/')




def test_dsh_schema():

    # First make sure the example conforms to the schema
    jsonschema.validate(DSH_EXAMPLE, main.DSH_SCHEMA)

    # Then, check that flange discovers the example as in instance of the model
    f = cfg.from_file('tests/example.yml', root_path='root',)
    f.register_model('dshnode', flmd.Model('dshnode', flmd.Model.get_schema_validator(main.DSH_SCHEMA), main.node_dsh_context))
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


# def test_context_cmd_do_after_simple():
#
#     cmdroot = FG.get('tests', model='dshnode')
#     path = cmdroot.resolve('platform build')
#     path.execute()
#     print cmdroot


# def test_main():
#
#     from flange import cfg
#     FG = cfg.Cfg(
#         data=main.DSH_FLANGE_PLUGIN,
#         root_path='prj',
#         file_patterns=['.cmd.*'],
#         base_dir='~/workspace',
#         file_search_depth=3)
#
#     root = FG.obj('sire6')
#     assert root
#     assert root.resolve('platform ps').execute()
#
