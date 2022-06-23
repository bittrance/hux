#!/usr/bin/env python3

import argparse
import os
import subprocess
import tempfile

from contextlib import contextmanager


parser = argparse.ArgumentParser()
parser.add_argument('--repository',
                    default=os.environ.get('HUX_REPOSITORY', None))
parser.add_argument('--state-storage-account',
                    default=os.environ.get('HUX_STATE_STORAGE_ACCOUNT', None))
parser.add_argument('--state-storage-container',
                    default=os.environ.get('HUX_STATE_STORAGE_CONTAINER', None))


def validate(args):
    if not args.repository:
        raise RuntimeError(
            'Please set --repository to the repo you want to watch')


def execute(*args):
    print(args)
    cmd = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    res = cmd.wait()
    if res != 0:
        print(cmd.stdout.read().decode('utf-8'))
        print(cmd.stderr.read().decode('utf-8'))
        raise RuntimeError(cmd.stderr.read().decode('utf-8'))


@contextmanager
def git_repo(repository):
    with tempfile.TemporaryDirectory() as repodir:
        execute('git', '-C', repodir, 'clone', '--depth=1', repository, '.')
        yield repodir


@contextmanager
def state(repodir, args):
    try:
        execute('az', 'storage', 'blob', 'download',
                '--account-name', args.state_storage_account,
                '--container-name', args.state_storage_container,
                '--name', 'terraform.tfstate',
                '--file', os.path.join(repodir, 'terraform.tfstate'))
    except RuntimeError as err:
        print('Hoping error %s is that blob does not exist' % err)
    yield
    execute('az', 'storage', 'blob', 'upload',
            '--overwrite',
            '--account-name', args.state_storage_account,
            '--container-name', args.state_storage_container,
            '--name', 'terraform.tfstate',
            '--file', os.path.join(repodir, 'terraform.tfstate'))


def run(repodir):
    execute('terraform', '-chdir=%s' % repodir, 'init')
    plan = tempfile.NamedTemporaryFile()
    execute('terraform', '-chdir=%s' % repodir, 'plan', '-out', plan.name)
    execute('terraform', '-chdir=%s' % repodir, 'apply', plan.name)


if __name__ == '__main__':
    args = parser.parse_args()
    with git_repo(args.repository) as repodir:
        with state(repodir, args):
            run(repodir)
