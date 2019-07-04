#! /usr/bin/env python
"""
Usage:
  vagrant.py setup [--rm]
  vagrant.py copyimage
  vagrant.py purge
"""
import re
from contextlib import ExitStack, suppress

from functools import wraps
from docopt import docopt
import subprocess
from pathlib import Path
import json
import os, sys


repo_dir = Path(__file__).parent.absolute()
base_env = {
    'VAGRANT_CWD': repo_dir / 'vagrant/base', **os.environ
}
config_path = repo_dir / 'vagrant/config.json'
with config_path.open() as f:
    config = json.loads(f.read())


class SysExit(Exception):
    def __init__(self, returncode):
        self.returncode = returncode


@wraps(subprocess.run)
def run(*args, **kwargs):
    completed = subprocess.run(*args, **kwargs)
    if completed.returncode:
        raise SysExit(completed.returncode)
    return completed


def _commit():
    completed = run("vagrant commit", shell=True, env=base_env, capture_output=True)
    volumes = []
    for line in completed.stdout.decode().splitlines():
        start, sep, end = line.partition(f"{config['hostname']}: commiting")
        volume = end
        if not sep:
            continue
        if start.strip():
            continue
        volumes.append(volume)
        print(f"Updated: {volume}")


def get_image_name(name):
    parts = name.split('/')
    return '-VAGRANTSLASH-'.join(parts)


def get_boxes_path():
    completed = run("vagrant showinfo", shell=True, capture_output=True)
    info = json.loads(completed.stdout)
    return Path(info['boxes_path'])

def _copyimage(*, boxes_path):
    last_version = get_last_version(boxes_path=boxes_path)
    image = last_version / 'libvirt/box.img'
    boxname = get_image_name(config['boxname'])
    target_dir = boxes_path / boxname / last_version.name / 'libvirt'

    if target_dir.exists():
        ans = input(f"{target_dir} exists. Replace? [n] ")
        if not ans or ans.strip().lower() not in ('y', 'yes'):
            return
    target_dir.mkdir(parents=True, exist_ok=True)
    src_dir = last_version / 'libvirt'
    run(f"cp -r {src_dir}/* {target_dir}", shell=True)

def do_copyimage(args):
    boxes_path = get_boxes_path()
    _copyimage(boxes_path=boxes_path)


def get_last_version(*, boxes_path):
    env = {
        'VAGRANT_CWD': repo_dir / 'vagrant/base/box',
        **os.environ
    }
    run("vagrant box update", shell=True, env=env)
    image_name = get_image_name(config['image'])
    box_dir = boxes_path / image_name
    version_regexp = re.compile(r'[\d\.]+')
    versions = [x for x in box_dir.iterdir() if x.is_dir() and version_regexp.match(x.name)]
    last_version = sorted(versions, key=lambda p: str(p))[-1]
    return last_version


#TODO set provisioned on/off

def _full_destroy(*, suppress_error=False):
    env = {
        **base_env, 'NO_OP': 'True'
    }
    with ExitStack() as stack:
        if suppress_error:
            ctx = suppress(SysExit)
            stack.enter_context(ctx)
        run("vagrant up", shell=True, env=env)
        run("vagrant fulldestroy", shell=True, env=env)
        run("vagrant destroy -f", shell=True)

    run("sudo systemctl restart libvirtd", shell=True)


def init_config():
    path = repo_dir / 'vagrant/config.json'
    if not path.exists():
        template_path = repo_dir / 'vagrant/config.json.template'
        path.write_text(template_path.read_text())


def do_setup(args):
    if args['--rm']:
        _full_destroy()
    boxes_path = get_boxes_path()
    last_version = get_last_version(boxes_path=boxes_path)
    boxname = get_image_name(config['boxname'])
    target_dir = boxes_path / boxname / last_version.name / 'libvirt'
    if not target_dir.exists():
        _full_destroy(suppress_error=True)
        do_copyimage(args)
    _update(args)


def do_purge(args):
    _full_destroy()


def _update(args):
    run("vagrant destroy -f", shell=True, env=base_env)
    run("vagrant up --provision", shell=True, env=base_env)
    ans = input("Do you want to commit the image? [y] ")
    if ans and ans.strip().lower() not in ['y', 'yes']:
        return
    _commit()
    set_not_provisioned()
    run("vagrant destroy -f", shell=True, env=base_env)

def set_not_provisioned():
    completed = run("vagrant showinfo", shell=True, capture_output=True)
    machine_info = json.loads(completed.stdout)
    path = Path(machine_info['data_dir']) / 'action_provision'
    try:
        os.remove(path.absolute())
    except FileNotFoundError:
        pass



def main():
    args = docopt(__doc__)
    init_config()
    try:
        if args['copyimage']:
            do_copyimage(args)
        elif args['setup']:
            do_setup(args)
        elif args['purge']:
            do_purge(args)
    except SysExit as ex:
        sys.exit(ex.returncode)


if __name__ == '__main__':
    main()