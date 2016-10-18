from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
import subprocess
import pwd
import cPickle as pickle
import argparse
from datetime import datetime
from tabulate import tabulate

TEST = 0
DOCKER_BASE_URL = 'unix://var/run/docker.sock'
STATUS_FILE = '/tmp/dockers/status.pkl'


class DockerBlockEntry(object):

    def __init__(self, name, blocked_by, user_fullname, since, until):
        self.name = name
        self.blocked_by = blocked_by
        self.user_fullname = None if user_fullname is None else user_fullname.strip(', ')
        self.since = since
        self.until = until

    def to_list(self):
        return [self.name, self.blocked_by,
                None if self.user_fullname is None else self.user_fullname.strip(', '),
                self.since, self.until]


def block(args):
    status = load_status()
    username, full_name = get_username()

    entry = next((s for s in status if s.name == args.container), None)
    if entry is None:
        raise ValueError('Invalid container name: {}'.format(args.container))

    if entry.blocked_by is not None and entry.blocked_by != username:
        raise ValueError('Container {} is already blocked by {}'.format(entry.name, entry.blocked_by))
    entry.blocked_by = username
    entry.user_fullname = full_name
    if entry.since is None:
        entry.since = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if args.until is not None and len(args.until) > 0:
        entry.until = args.until
    save_status(status)
    print('Done. Container {} blocked for {}'.format(entry.name, username))
    print()
    ls(args)


def unblock(args):
    status = load_status()
    username, full_name = get_username()

    entry = next((s for s in status if s.name == args.container), None)
    if entry is None:
        raise ValueError('Invalid container name: {}'.format(args.container))

    if entry.blocked_by != username:
        raise ValueError('Cannot unblock. Container {} was not blocked by you ({})'.format(entry.name, username))
    entry.blocked_by = None
    entry.user_fullname = None
    entry.since = None
    entry.until = None
    save_status(status)
    print('Done. Container {} is unblocked'.format(entry.name))
    print()
    ls(args)


def ls(_):
    print(tabulate([s.to_list() for s in load_status()],
                   headers=['Name', 'Blocked by', 'Full name', 'Since', 'Until']))


def get_container_names():
    if TEST:
        return ['gpu0', 'gpu1', 'gpus']
    else:
        from docker import Client
        docker_client = Client(base_url=DOCKER_BASE_URL)
        return sorted([x['Names'][0][1:] for x in docker_client.containers() if len(x.get('Names')) > 0])


def load_status():
    containers = get_container_names()

    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, 'r') as f:
            status = pickle.load(f)
    else:
        status = []
        d = os.path.split(STATUS_FILE)[0]
        if not os.path.exists(d):
            os.makedirs(d, mode=0777)

        umask_original = os.umask(0)
        try:
            handle = os.fdopen(os.open(STATUS_FILE, os.O_WRONLY | os.O_CREAT, int("0666", 8)), 'w')
        finally:
            os.umask(umask_original)
        pickle.dump(status, handle)
        handle.close()

    for c in containers:
        if next((s for s in status if s.name == c), None) is None:
            status.append(DockerBlockEntry(c, None, None, None, None))

    return [s for s in status if s.name in containers]


def save_status(status):
    with open(STATUS_FILE, 'w') as f:
        pickle.dump(status, f)


def get_username():
    username = pwd.getpwuid(os.getuid()).pw_name

    # platform-dependent
    if sys.platform.startswith('linux'):
        return username, run_process(['getent', 'passwd', username]).split(':')[4]
    if sys.platform.startswith('darwin'):
        return username, run_process(['id', '-F'])

    return username, None


def run_process(args):
    p = subprocess.Popen(args, stdout=subprocess.PIPE)
    p.wait()
    if p.returncode == 0:
        return p.stdout.readline().strip(', ')
    return None


def main():
    parser = argparse.ArgumentParser(description='Poor-man\'s GPU container blocking system')
    subparsers = parser.add_subparsers(help='Run "command -h" for help on each command')

    parser_block = subparsers.add_parser('block',
                                         help='Block a container. Can only block an unblocked container')
    parser_block.add_argument('container', type=str, help='Name of the GPU container to be blocked')
    parser_block.add_argument('--until', metavar='Time', type=str, help='Until when to block the container')
    parser_block.set_defaults(func=block)

    parser_unblock = subparsers.add_parser('unblock',
                                           help='Unblock a container. Can only unblock containers that you blocked')
    parser_unblock.add_argument('container', type=str, help='Name of the GPU container to be unblocked')
    parser_unblock.set_defaults(func=unblock)

    parser_ls = subparsers.add_parser('ls', help='List the status of all containers on this machine')
    parser_ls.set_defaults(func=ls)

    parser_go = subparsers.add_parser('go', help='Go to a particular container')
    parser_go.add_argument('container', type=str, help='Name of the GPU container to go to')

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()


