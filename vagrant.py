#! /usr/bin/env python
"""
Usage:
  vagrant.py init
  vagrant.py update [-y | --yes]
  vagrant.py copyimage
  vagrant.py destroy
"""

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

volumes_path = repo_dir / 'vagrant/base/volumes.json'


def _commit():
    completed = subprocess.run("vagrant commit", shell=True, env=base_env, capture_output=True)
    volumes = []
    for line in completed.stdout.decode().splitlines():
        start, sep, end = line.partition(f"{config['hostname']}: commiting")
        if not sep:
            continue
        if start.strip():
            continue
        volumes.append(end)
    with volumes_path.open('w') as f:
        f.write(json.dumps(volumes))

def _full_destroy():
    with volumes_path.open() as f:
        volumes = json.loads(f.read())
    for vol in volumes:
        cmd = f"sudo -E qemu-img info {vol} --force | grep 'backing file:' | cut -d ':' -f2`.chomp"
        completed = subprocess.run(cmd, shell=True, capture_output=True)
        backing = completed.stdout.decode()
        cmd = f"sudo rm -f {backing}"
        completed = subprocess.run(cmd, shell=True)


def do_destroy(args):
    if not volumes_path.exists():
        print("No commit was made. You may run `copybox` to update it")
        return
    ans = input("This will destroy the base image. Continue? [n] ")
    if not ans or ans.strip().lower() not in ('y', 'yes'):
        return
    _full_destroy()

def get_image_name(name):
    parts = name.split('/')
    return '-VAGRANTSLASH-'.join(parts)


def get_boxes_path():
    completed = subprocess.run("vagrant showinfo", shell=True, capture_output=True)
    info = json.loads(completed.stdout)
    return Path(info['boxes_path'])

def get_box_dir(boxes_path):
    image_name = get_image_name(config['image'])
    boxname = get_image_name(config['boxname'])
    return Path(boxes_path) / image_name / '0' / boxname


def _copyimage(*, boxes_path):
    image_name = get_image_name(config['image'])
    box_dir = boxes_path / image_name
    dirs = [x for x in box_dir.iterdir() if x.is_dir()]
    last_version = sorted(dirs, key=lambda p: str(p))[-1]
    image = last_version / 'libvirt/box.img'
    boxname = get_image_name(config['boxname'])
    target_dir = boxes_path / boxname / '0/libvirt'
    if target_dir.exists():
        ans = input(f"{target_dir} exists. Replace? [n] ")
        if not ans or ans.strip().lower() not in ('y', 'yes'):
            return
    target_dir.mkdir(parents=True, exist_ok=True)
    cmd = f"cp {repo_dir}/vagrant/base/box_template/* {target_dir}"
    result = subprocess.run(cmd, shell=True)
    cmd = f"cp {image} {target_dir}"
    result = subprocess.run(cmd, shell=True)

def do_copyimage(args):
    boxes_path = get_boxes_path()
    _copyimage(boxes_path=boxes_path)


def do_init(args):
    # TODO: --rm flag
    boxes_path = get_boxes_path()
    boxname = get_image_name(config['boxname'])
    target_dir = boxes_path / boxname / '0/libvirt'
    if not target_dir.exists():
        do_copyimage(args)
    do_update(args)


def do_update(args):
    completed = subprocess.run("vagrant up --provision", shell=True, env=base_env)
    if completed.returncode:
        sys.exit(completed.returncode)
    ans = input("Do you want to commit the image? [y] ")
    if ans and ans.strip().lower() not in ['y', 'yes']:
        return
    completed = subprocess.run("vagrant commit", shell=True, env=base_env)
    if completed.returncode:
        sys.exit(completed.returncode)
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
    if args['update']:
        do_update(args)
    elif args['destroy']:
        do_destroy(args)
    elif args['copyimage']:
        do_copyimage(args)
    elif args['init']:
        do_init(args)


if __name__ == '__main__':
    main()