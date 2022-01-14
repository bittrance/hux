#!/usr/bin/env python3

import argparse
import os
import subprocess
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument(
    '--repository', default=os.environ.get('HUX_REPOSITORY', None))


def validate(args):
    if not args.repository:
        raise RuntimeError(
            'Please set --repository to the repo you want to watch')


def run(args, workdir):
    git = subprocess.Popen(
        ['git', '-C', workdir, 'clone', '--depth=1', args.repository, '.'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    res = git.wait()
    print(git.stdout.read().decode('utf-8'))
    print(git.stderr.read().decode('utf-8'))
    if res != 0:
        raise RuntimeError(git.stderr.read().decode('utf-8'))

    tf = subprocess.Popen(
        ['terraform', '-chdir=%s' % workdir, 'init'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    res = tf.wait()
    print(tf.stdout.read().decode('utf-8'))
    if res != 0:
        raise RuntimeError(tf.stderr.read().decode('utf-8'))

    plan = tempfile.NamedTemporaryFile()
    tf = subprocess.Popen(
        ['terraform', '-chdir=%s' %
            workdir, 'plan', '-out', plan.name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    res = tf.wait()
    print(tf.stdout.read().decode('utf-8'))
    if res != 0:
        raise RuntimeError(tf.stderr.read().decode('utf-8'))

    tf = subprocess.Popen(
        ['terraform', '-chdir=%s' % workdir, 'apply', plan.name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    res = tf.wait()
    print(tf.stdout.read().decode('utf-8'))
    if res != 0:
        raise RuntimeError(tf.stderr.read().decode('utf-8'))


if __name__ == '__main__':
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as workdir:
        run(args, workdir)
