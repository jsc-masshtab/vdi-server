#! /usr/bin/env python
"""
Usage:
  vagrant.py setup [--rm]
  vagrant.py copyimage
"""
import re

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


def _commit():
    completed = subprocess.run("vagrant commit", shell=True, env=base_env, capture_output=True)
    if completed.returncode:
        sys.exit(completed.returncode)
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
    completed = subprocess.run("vagrant showinfo", shell=True, capture_output=True)
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
    cmd = f"cp {repo_dir}/vagrant/base/box/dir/* {target_dir}"
    result = subprocess.run(cmd, shell=True)
    cmd = f"cp {image} {target_dir}"
    result = subprocess.run(cmd, shell=True)

def do_copyimage(args):
    boxes_path = get_boxes_path()
    _copyimage(boxes_path=boxes_path)


def get_last_version(*, boxes_path):
    env = {
        'VAGRANT_CWD': repo_dir / 'vagrant/base/box',
        **os.environ
    }
    result = subprocess.run("vagrant box update", shell=True, env=env)
    image_name = get_image_name(config['image'])
    box_dir = boxes_path / image_name
    version_regexp = re.compile(r'[\d\.]+')
    versions = [x for x in box_dir.iterdir() if x.is_dir() and version_regexp.match(x.name)]
    last_version = sorted(versions, key=lambda p: str(p))[-1]
    return last_version


def do_setup(args):
    if args['--rm']:
        #TODO check status
        # init & update
        result = subprocess.run("vagrant fulldestroy", shell=True)
        if result.returncode:
            sys.exit(result.returncode)
        result = subprocess.run("sudo systemctl restart libvirtd", shell=True)
        if result.returncode:
            sys.exit(result.returncode)
    boxes_path = get_boxes_path()
    last_version = get_last_version(boxes_path=boxes_path)
    image = last_version / 'libvirt/box.img'
    boxname = get_image_name(config['boxname'])
    target_dir = boxes_path / boxname / last_version.name / 'libvirt'
    if not target_dir.exists():
        do_copyimage(args)
    do_update(args)


def do_update(args):
    completed = subprocess.run("vagrant destroy -f", shell=True, env=base_env)
    if completed.returncode:
        sys.exit(completed.returncode)
    completed = subprocess.run("vagrant up --provision", shell=True, env=base_env)
    if completed.returncode:
        sys.exit(completed.returncode)
    ans = input("Do you want to commit the image? [y] ")
    if ans and ans.strip().lower() not in ['y', 'yes']:
        return
    _commit()
    set_not_provisioned()

def set_not_provisioned():
    completed = subprocess.run("vagrant showinfo", shell=True, capture_output=True)
    machine_info = json.loads(completed.stdout)
    path = Path(machine_info['data_dir']) / 'action_provision'
    try:
        os.remove(path.absolute())
    except FileNotFoundError:
        pass



def main():
    args = docopt(__doc__)
    # if args['update']:
    #     do_update(args)
    if args['copyimage']:
        do_copyimage(args)
    elif args['setup']:
        do_setup(args)


if __name__ == '__main__':
    main()