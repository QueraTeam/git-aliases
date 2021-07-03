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

    run_cmd(f"git merge --quit")
    run_cmd(f'rm -rf ".git/rebase-apply";')

    run_cmd(f"git checkout --orphan {WATCHER_BRANCH} -q")
    run_cmd(f"git remote rm origin")
    run_cmd(f"git reset --hard -q")

    local_branches = get_branch_names()
    for branch in local_branches:
        run_cmd(f"git branch -D {branch} -q")

    local_tags = run_cmd('git tag -l').split()
    for tag in local_tags:
        run_cmd(f"git tag --delete {tag}")

    run_cmd(f"git remote add origin {origin_url}")
    run_cmd(f"git fetch origin --tags -f -q")

    deleting_branches = []
    submit_remote_branches = get_branch_names(ref='refs/remotes/origin')
    for branch in submit_remote_branches:
        remote_name, branch_name = branch.split('/', 1)
        if branch_name not in ['master', 'main', 'HEAD']:
            deleting_branches.append(branch_name)

    deleting_tags = []
    remote_tags = run_cmd('git tag -l').split()
    for tag in remote_tags:
        run_cmd(f"git tag --delete {tag}")
        if tag.startswith('submit') and tag != 'submit':
            deleting_tags.append(tag)

    run_cmd(f"git push origin --delete {' '.join(deleting_tags)} {' '.join(deleting_branches)} -f -q")

    initial_remote_name = uuid4().hex
    run_cmd(f"git remote add {initial_remote_name} {initial_remote_url}")
    run_cmd(f"git fetch {initial_remote_name} --tags -q")

    initial_remote_branches = get_branch_names(ref=f'refs/remotes/{initial_remote_name}/')
    for branch in initial_remote_branches:
        _, fork_branch_name = branch.split('/', 1)
        run_cmd(f"git checkout -b {fork_branch_name} {branch} -q")

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

    tags = ' '.join(run_cmd('git tag -l').split())
    branches = ' '.join(get_branch_names())
    run_cmd(f"git push origin --atomic -f -q {branches} {tags}")

    print("Your repo have been reset to the initial state.")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1]:
        run(sys.argv[1])
    else:
        run()
