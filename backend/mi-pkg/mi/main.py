# Adds higher directory to python modules path.
import sys
sys.path.append(".")
sys.path.append("..")
sys.path.append("...")


from db.db import db

import asyncio
import subprocess
from pathlib import Path

import os
import sys
import re

import json
from runpy import run_path

from cached_property import cached_property as cached

from docopt import docopt

from contextlib import ExitStack

from asyncpg.exceptions import DuplicateTableError


DOCOPT = """\
mi utility.

Helps manage migrations in raw sql.

Usage:
  mi check
  mi new [<name>] [--py | --python]
  mi apply [<names>...]
  mi -h | --help
  mi help

Subcommands:
  mi check         Check for unapplied migrations
  mi new           Create empty migration
  mi apply         Apply migration(s)
"""


class ScriptError(Exception):
    pass


class Mi:

    @cached
    def args(self):
        return docopt(doc=DOCOPT)

    @cached
    def dir(self):
        MIGRATIONS_DIR = os.environ.get('MIGRATIONS_DIR')
        if MIGRATIONS_DIR:
            p = Path(MIGRATIONS_DIR)
        else:
            p = Path(os.getcwd()) / 'migrations'
        return p.absolute()

    @cached
    def files(self):
        ret = self.dir.glob('*.*')
        ret = sorted(ret, key=lambda p: p.name) # unneeded?
        return ret


    @classmethod
    def get_last_number(cls, names):
        names = reversed(names)
        regexp = re.compile(r'^(\d+)(_\w+)?.(sql|py)')
        for name in names:
            m = regexp.match(name)
            if not m:
                continue
            number, title, ext = m.groups()
            return int(number)

    async def exec(self, sql):
        await self.ensure_table()
        return await self._exec(sql)

    async def _exec(self, sql):
        # execute in a transaction
        async with db.transaction() as c:
            return await c.execute(sql)

    async def ensure_table(self):
        try:
            await self._exec("SELECT 1 FROM migrations")
        except:
            create = """\
CREATE TABLE migrations (
    name            varchar(80),
    timestamp       timestamp with time zone DEFAULT now()
);"""
            await self._exec(create)

    def _resolve_name(self, name):
        paths = list(self.dir.glob('{}*'.format(name)))
        if not paths:
            raise ExitError('No file matches {}'.format(name))
        elif len(paths) > 1:
            matches = ', '.join(p.name for p in paths)
            raise ExitError('Multiple matches for {}: {}'.format(name, matches))
        [p] = paths
        return p

    async def get_unapplied_migrations(self):
        if self.args['<names>']:
            return [
                self._resolve_name(name) for name in self.args['<names>']
            ]
        applied = await self.exec("SELECT name from migrations")
        applied = [name for (name,) in applied]
        # names = [p.name for p in self.files]
        return [
            p for p in self.files
            if p.name not in applied
        ]


    async def do_check(self):
        unapplied = await self.get_unapplied_migrations()
        if not unapplied:
            print('All migrations are applied')
            return
        s = ', '.join(p.name for p in unapplied)
        print('Unapplied: {}'.format(s))

    async def do_new(self):
        if self.args['--py'] or self.args['--python']:
            suffix = 'py'
        else:
            suffix = 'sql'
        names = [p.name for p in self.files]
        num = self.get_last_number(names) or 0
        num += 1
        title = self.args['<name>']
        if title:
            name = '%04d_%s.%s' % (num, title, suffix)
        else:
            name = '%04d.%s' % (num, suffix)   # f'{num:04d}.{suffix}'
        p = self.dir / name
        p.touch()
        print('{} is generated. Please fill it with meaning.'.format(p.absolute()) )


    async def do_apply(self):
        unapplied = await self.get_unapplied_migrations()
        for p in unapplied:
            if p.name.endswith('.py'):
                result = subprocess.run([sys.executable, str(p)])
                if result.returncode != 0:
                    # raise ScriptError
                    print('SCRIPT ERROR IN {}'.format(p.name))
                    continue
                await self.exec("INSERT INTO migrations VALUES ('{}');".format(p.name))
                print("Applied: {}".format(p.name))
                continue
            with p.open() as f:
                sql = f.read()
            sql = sql.strip()
            if not sql.endswith(";"):
                sql = "{};".format(sql)
            sql = '''{}\
            INSERT INTO migrations VALUES ('{}');'''.format(sql, p.name)
            try:
                await self.exec(sql)
            except DuplicateTableError:
                print('DuplicateTable VIOLATION. Maybe migrations are already applied. Stop applying')
                break
            print("Applied: {}".format(p.name))

    async def run(self):
        with ExitStack() as stack:
            if os.environ.get('PDB'):
                stack.enter_context(drop_into_debugger())
            commands = '''
                check new apply help
            '''
            for cmd in commands.split():
                if self.args[cmd]:
                    method = getattr(self, 'do_{}'.format(cmd))
                    return await method()
            if self.args['-h'] or self.args['--help']:
                return self.do_help()
            assert False


    def do_help(self):
        print(DOCOPT)


class ExitError(Exception):
    pass


class drop_into_debugger:
    def __enter__(self):
        pass
    def __exit__(self, e, m, tb):
        if not e:
            return
        try:
            import ipdb as pdb
        except ImportError:
            import pdb
        print(m.__repr__(), file=sys.stderr)
        pdb.post_mortem(tb)


def entry_point():
    try:
        loop = asyncio.get_event_loop()
        # asyncio.run(Mi().run()) # 3.7
        loop.run_until_complete(Mi().run())
        loop.close()
    except ExitError as ee:
        print(str(ee), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    entry_point()