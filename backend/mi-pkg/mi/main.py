import asyncio
import subprocess
from pathlib import Path

import os
import sys
import re

import json
from runpy import run_path

from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

from cached_property import cached_property as cached

from docopt import docopt

from contextlib import ExitStack




DOCOPT = """\
mi utility.

Helps manage migrations in raw sql.

Usage:
  mi init [--db=db]
  mi check
  mi new [<name>] [--py | --python]
  mi apply [<names>...]
  mi -h | --help
  mi help

Subcommands:
  mi init          Create .mi.json
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
    def config(self):
        p = Path('.') / '.mi.json'
        if not p.exists():
            raise ExitError('Please run mi init')
        with p.open() as f:
            return json.loads(f.read())

    @cached
    def db_url(self):
        return self.config['database_url']

    @cached
    def dir(self):
        d = self.config['migrations_dir']
        return Path(d)

    @cached
    def files(self):
        ret = self.dir.glob('*.*')
        ret = sorted(ret, key=lambda p: p.name) # unneeded?
        return ret

    @cached
    def engine(self):
        return create_engine(self.db_url, poolclass=QueuePool)

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

    @cached
    def exec(self):
        self.ensure_table()
        return self._exec

    def _exec(self, sql):
        # execute in a transaction
        with self.engine.begin() as c:
            return c.execute(sql)

    def ensure_table(self):
        try:
            self._exec("SELECT 1 FROM migrations")
        except:
            create = """\
CREATE TABLE migrations (
    name            varchar(80),
    timestamp       timestamp with time zone DEFAULT now()
);"""
            self._exec(create)

    def _resolve_name(self, name):
        paths = list(self.dir.glob(f'{name}*'))
        if not paths:
            raise ExitError(f'No file matches {name}')
        elif len(paths) > 1:
            matches = ', '.join(p.name for p in paths)
            raise ExitError(f'Multiple matches for {name}: {matches}')
        [p] = paths
        return p

    def get_unapplied_migrations(self):
        if self.args['<names>']:
            return [
                self._resolve_name(name) for name in self.args['<names>']
            ]
        applied = self.exec("SELECT name from migrations")
        applied = [name for (name,) in applied]
        # names = [p.name for p in self.files]
        return [
            p for p in self.files
            if p.name not in applied
        ]

    def get_db_url(self):
        db = self.args['--db']
        if db:
            return db
        db = os.environ.get('DATABASE_URL')
        if db is None:
            raise ExitError('Either set $DATABASE_URL or provide the --db option')
        return db

    def do_init(self):
        d = Path('.')
        mi_json = d / '.mi.json'
        if mi_json.exists():
            print('Already initialized.')
            return
        migration_dir = d / 'migrations'
        if not migration_dir.exists():
            migration_dir.mkdir()
        else:
            ans = input('Do you want to reuse directory migrations? [y/n]')
            if ans.strip() != 'y':
                p = input('Please type the desired directory path: ')
                migration_dir = Path(p)
                migration_dir.mkdir()

        db_url = self.get_db_url()
        conf = {
            'database_url': db_url,
            'migrations_dir': str(migration_dir),
        }
        with mi_json.open('w') as f:
            # pretty-print to file
            conf = json.dumps(conf, sort_keys=True, indent=4, separators=(',', ': '))
            print(conf)
            f.write(conf)

    def do_check(self):
        unapplied = self.get_unapplied_migrations()
        if not unapplied:
            print('All migrations are applied')
            return
        s = ', '.join(p.name for p in unapplied)
        print(f"Unapplied: {s}")

    def do_new(self):
        if self.args['--py'] or self.args['--python']:
            suffix = 'py'
        else:
            suffix = 'sql'
        names = [p.name for p in self.files]
        num = self.get_last_number(names) or 0
        num += 1
        title = self.args['<name>']
        if title:
            name = f'{num:04d}_{title}.{suffix}'
        else:
            name = f'{num:04d}.{suffix}'
        p = self.dir / name
        p.touch()
        print(f'{p.absolute()} is generated. Please fill it with meaning.')


    def do_apply(self):
        unapplied = self.get_unapplied_migrations()
        for p in unapplied:
            if p.name.endswith('.py'):
                result = subprocess.run([sys.executable, str(p)])
                if result.returncode != 0:
                    raise ScriptError
                self.exec(f"INSERT INTO migrations VALUES ('{p.name}');")
                print(f"Applied: {p.name}")
                continue
            with p.open() as f:
                sql = f.read()
            sql = sql.strip()
            if not sql.endswith(";"):
                sql = f"{sql};"
            sql = f'''{sql}\

INSERT INTO migrations VALUES ('{p.name}');'''
            self.exec(sql)
            print(f"Applied: {p.name}")

    def run(self):
        with ExitStack() as stack:
            if os.environ.get('PDB'):
                stack.enter_context(drop_into_debugger())
            commands = '''
                init check new apply help
            '''
            for cmd in commands.split():
                if self.args[cmd]:
                    method = getattr(self, f'do_{cmd}')
                    return method()
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
        Mi().run()
    except ExitError as ee:
        print(str(ee), file=sys.stderr)
        sys.exit(1)
