#! env python
"""
Usage:
  init [-i | --interactive] [--bare] [<boxname>]
"""

import docopt

import subprocess
import sys
import os
from textwrap import dedent

def main():
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
        with open('vagrant/temp.Vagrantfile') as f:
            content = f.read()
        if args['-i'] or args['--interactive']:
            line = dedent(f"""\
            $boxname = "{boxname}"
            $script = <<-SCRIPT
            SCRIPT
            """)
        else:
            with open('vagrant/apt.sh') as f:
                apt_sh = f.read()
            line = dedent(f"""$boxname = "{boxname}"\n$script = <<-SCRIPT\n{apt_sh}\nSCRIPT""")
        vagrantfile = '\n'.join((line, content))
        with open('Vagrantfile', 'w') as f:
            f.write(vagrantfile)
        completed = subprocess.run("vagrant up", shell=True)
        if completed.returncode:
            sys.exit(completed.returncode)
        if args['-i'] or args['--interactive']:
            completed = subprocess.run("vagrant ssh", shell=True)
        completed = subprocess.run("vagrant commit", shell=True)
        # Set not provisioned
        from pathlib import Path
        path = Path('.') / '.vagrant' / 'machines' / 'vdihost' / 'libvirt' / 'action_provision'
        os.remove(path.absolute())
    with open('vagrant/real.Vagrantfile') as f:
        content = f.read()
    line = f'$boxname = "{boxname}"'
    vagrantfile = '\n'.join((line, '', content))
    with open('Vagrantfile', 'w') as f:
        f.write(vagrantfile)

main()