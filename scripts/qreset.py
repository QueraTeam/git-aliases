import re
import subprocess
import sys
from uuid import uuid4


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

    run_cmd(f"git checkout --orphan {WATCHER_BRANCH} -q")
    run_cmd(f"git reset --hard -q")

    submit_branches = get_branch_names()
    for branch in submit_branches:
        run_cmd(f"git branch -D {branch} -q")

    initial_remote_name = uuid4().hex
    run_cmd(f"git remote add {initial_remote_name} {initial_remote_url}")

    run_cmd(f"git fetch {initial_remote_name} -q")
    remote_branches = get_branch_names(ref=f'refs/remotes/{initial_remote_name}/')
    for branch in remote_branches:
        _, fork_branch_name = branch.split('/', 1)
        run_cmd(f"git checkout -b {fork_branch_name} {branch} -q")

    local_tags = run_cmd(f"git tag -l").split()
    for tag in local_tags:
        run_cmd(f"git tag --delete {tag} -q")
    run_cmd(f"git fetch --tags -f -q")
    tags = run_cmd(f"git tag -l").split()
    for tag in filter(lambda t: not t.startswith('submit'), tags):
        run_cmd(f"git tag --delete {tag}")
        run_cmd(f"git push -f --delete origin {tag} -q")
    run_cmd(f"git fetch --tags {initial_remote_name} -q")

    remotes = run_cmd(f"git remote").split()
    for remote in filter(lambda r: r != 'origin', remotes):
        run_cmd(f"git remote rm {remote}")

    branches = get_branch_names()
    if "master" in branches:
        run_cmd(f"git checkout master -q")
    elif "main" in branches:
        run_cmd(f"git checkout main -q")

    run_cmd(f"git push --all -f -q")
    run_cmd(f"git push --tags -f -q")

    print("Your repo have been reset to the initial state.")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1]:
        run(sys.argv[1])
    else:
        run()
