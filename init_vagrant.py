#! env python
"""
Usage:
  init [-i | --interactive] [-y] [--bare] [<boxname>]
"""

import docopt
import json

import subprocess
import sys
import os
from textwrap import dedent
from pathlib import Path

def main():
    repo_dir = Path(__file__).parent
    args = docopt.docopt(__doc__)
    if not args['<boxname>']:
        boxname = 'generic/ubuntu1904'
    else:
        boxname = args['<boxname>']
    if os.path.exists('Vagrantfile'):
        ans = input('Delete existing Vagrantfile? [y/n]')
        if ans.strip().lower() != 'y':
            sys.exit(0)
        os.remove('Vagrantfile')
    if not args['--bare']:
        # Create a box, update it and commit
        with (repo_dir / 'vagrant' / 'temp.Vagrantfile').open() as f:
            content = f.read()

        if args['-i'] or args['--interactive']:
            apt_sh = ''
        else:
            with (repo_dir / 'vagrant' / 'apt.sh').open() as f:
                apt_sh = f.read()
        line = dedent(f"""$boxname = "{boxname}"\n$script = <<-SCRIPT\n{apt_sh}\nSCRIPT""")
        vagrantfile = '\n'.join((line, content))
        with open('Vagrantfile', 'w') as f:
            f.write(vagrantfile)
        completed = subprocess.run("vagrant up --provision", shell=True)
        if completed.returncode:
            sys.exit(completed.returncode)
        if args['-i'] or args['--interactive']:
            completed = subprocess.run("vagrant ssh", shell=True)
        completed = subprocess.run("vagrant commit", shell=True)
        # Set not provisioned
        completed = subprocess.run("vagrant showinfo", shell=True, capture_output=True)
        machine_info = json.loads(completed.stdout)
        path = Path(machine_info['data_dir']) / 'action_provision'
        os.remove(path.absolute())
    with (repo_dir / 'vagrant' / 'real.Vagrantfile').open() as f:
        content = f.read()
    line = f'$boxname = "{boxname}"'
    vagrantfile = '\n'.join((line, '', content))
    with open('Vagrantfile', 'w') as f:
        f.write(vagrantfile)

main()