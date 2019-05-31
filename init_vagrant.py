"""
Usage:
  init <boxname>
"""

import docopt
args = docopt.docopt(__doc__)

import subprocess
import sys

def main():
    cmd = f"vagrant init {args['<boxname>']}"
    completed = subprocess.run(cmd, shell=True)
    if completed.returncode:
        sys.exit(completed.returncode)
    breakpoint()
    completed = subprocess.run("vagrant up", shell=True)
    if completed.returncode:
        sys.exit(completed.returncode)


    completed = subprocess.run("vagrant ssh", shell=True)
    completed = subprocess.run("vagrant commit", shell=True)
    with open('_Vagrantfile') as f:
        content = f.read()
    boxname = ''.join(('"', args['<boxname>'], '"'))
    line = f"$boxname = {boxname}"
    vagrantfile = '\n'.join((line, content))
    with open('Vagrantfile', 'w') as f:
        f.write(vagrantfile)

main()