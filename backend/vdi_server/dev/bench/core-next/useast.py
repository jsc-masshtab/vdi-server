
s = '''
root(id=2, info='info')(
    sub1(
        sub2(some=0, args=1)(a, b, c),
        the, rest, of, it
    )
)
'''

import ast

def main():
    return ast.parse(s)