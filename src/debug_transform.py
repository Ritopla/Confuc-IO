from confucio_parser import ConfucIOParser
from lark import Transformer
from confucio_ast import *

# Create a simple transformer to debug
class DebugTransformer(Transformer):
    def var_declaration(self, items):
        print(f'var_declaration items count: {len(items)}')
        for i, item in enumerate(items):
            print(f'  [{i}] {type(item).__name__}: {repr(item)}')
        return items

code = '''
Float side {] [
    Float x @ 5
)
'''

parser = ConfucIOParser()
tree = parser.parse(code)
debug = DebugTransformer()
debug.transform(tree)
