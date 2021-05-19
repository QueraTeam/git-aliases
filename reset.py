import subprocess
import re
from uuid import uuid4
import sys


def run_cmd(cmd: str):
    result = subprocess.run(cmd.split(), stdout=subprocess.PIPE)
    if result.returncode != 0:
        raise Exception()

    return result.stdout.strip().decode('utf-8')


def get_branch_names(*, ref='refs/heads'):
    return run_cmd(f"git for-each-ref --format %(refname:short) {ref}").split()


def run(initial_remote_url=None):
    WATCHER_BRANCH = uuid4().hex

    run_cmd("git config credential.helper store")

    origin_url = run_cmd("git remote get-url origin")

    if not initial_remote_url:
        problem_id = re.fullmatch(r'.*/p-(\d+)\.git', origin_url).group(1)
        initial_remote_url = ''.join(re.split(r'([/:]ao-\d+/)', origin_url)[:-1]) + f'initial/initial-{problem_id}.git'

    run_cmd(f"git checkout --orphan {WATCHER_BRANCH}")
    run_cmd(f"git reset --hard")

    submit_branches = get_branch_names()
    for branch in submit_branches:
        run_cmd(f"git branch -D {branch}")

    initial_remote_name = 'initial_project'
    run_cmd(f"git remote add {initial_remote_name} {initial_remote_url}")

    run_cmd(f"git fetch {initial_remote_name}")
    remote_branches = get_branch_names(ref=f'refs/remotes/{initial_remote_name}/')
    for branch in remote_branches:
        _, fork_branch_name = branch.split('/', 1)
        run_cmd(f"git checkout -b {fork_branch_name} {branch}")

    run_cmd(f"git remote rm {initial_remote_name}")

    branches = get_branch_names()
    if "master" in branches:
        run_cmd(f"git checkout master")
    elif "main" in branches:
        run_cmd(f"git checkout main")

    run_cmd(f"git push --all -f")
    run_cmd(f"git push --tags -f")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1]:
        run(sys.argv[1])
    else:
        run()
