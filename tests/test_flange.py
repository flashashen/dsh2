import jsonschema, yaml
from context import *
import flange


print(dir(flange))
FG = flange.Flange(
    data=node.DSH_FLANGE_PLUGIN,
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
    jsonschema.validate(DSH_EXAMPLE, node.DSH_SCHEMA)

    # Then, check that flange discovers the example as in instance of the model
    f = flange.from_file('example.yml', root_ns='root',)
    f.register('dshnode', node.DSH_SCHEMA, )
    dshnode = f.get('root', 'dshnode')
    assert dshnode.get


def test_flange_config_model_registration():
    # The initial data contains the test plugin registation
    cmdroot = FG.get('tests', 'dshnode')

    path = resolver.ResolutionPath(cmdroot)
    resolver.resolve(path, ['root', 'platform'], 0)
    assert sorted(path.match_result.completions) == ['build', 'ps', 'stop', 'up']

    resolver.resolve(path, ['root', 'platform', 'build'], 0)
    assert path.match_result.completions == []


