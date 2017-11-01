
import flange

# print dir(flange)
FG = flange.Flange(
    root_ns='prj',
    file_patterns=['.cmd.yml'],
    base_dir='~/workspace',
    file_search_depth=2)

def test_nothing():
    assert True 
