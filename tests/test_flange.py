import jsonschema, yaml
from context import *
import flange


print(dir(flange))
FG = flange.Flange(
    data=main.DSH_FLANGE_PLUGIN,
    root_ns='prj',
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
    f = flange.from_file('example.yml', root_ns='root',)
    f.register('dshnode', main.DSH_SCHEMA, )
    dshnode = f.get('root', 'dshnode')
    assert dshnode.get


def test_flange_config_model_registration():
    # The initial data contains the test plugin registation
    cmdroot = FG.get('tests', 'dshnode')

    path = node.ResolutionPath(cmdroot)
    node.resolve(path, ['platform'], 0)
    assert sorted(path.match_result.completions) == ['build', 'ps', 'stop', 'up']

    node.resolve(path, ['platform', 'build'], 0)
    assert path.match_result.completions == []


def test_main():

    import flange
    FG = flange.Flange(
        data=main.DSH_FLANGE_PLUGIN,
        root_ns='prj',
        file_patterns=['.cmd.*'],
        base_dir='~/workspace',
        file_search_depth=3)

    assert node.resolve_and_execute(FG.mget('sire6'), ctx=None, matched_input='platform ps', child_results=None)

