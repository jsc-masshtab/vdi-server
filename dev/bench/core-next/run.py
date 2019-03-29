from graphql import graphql

from schema import schema

with open('/home/pwtail/projects/vdiserver/dev/bench/settings.py') as f:
    text = f.read()

mod = {}
exec(text, mod)

async def main():

    return (await graphql(schema, mod['query']))

import asyncio
asyncio.run(main())