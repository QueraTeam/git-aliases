import os
import subprocess
import unittest
from pathlib import Path
from uuid import uuid4
import shutil


def random_name(length=8):
    return uuid4().hex[:length]


def run_cmd(*args, **kwargs):
    return subprocess.run(*args, **kwargs, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def commit(path: Path, msg):
    run_cmd('git add .', cwd=path)
    run_cmd(f'git commit -m "{msg}" -q', cwd=path)


def nonsense_commit(path: Path, number=1) -> None:
    for i in range(number):
        some_file = path / random_name()
        some_file.touch()
        commit(path, "nonsense")


def nonsense_branch(path: Path, number=1) -> set[str]:
    new_branches = [random_name() for _ in range(number)]
    for branch in new_branches:
        run_cmd(f'git branch {branch}', cwd=path)
    return set(new_branches)


def get_current_branch(path: Path):
    return run_cmd('git rev-parse --abbrev-ref HEAD', cwd=path).stdout.strip()


def number_of_commits(path: Path):
    return int(run_cmd('git rev-list --count HEAD', cwd=path).stdout.strip())


def get_files_list(path: Path):
    _, _, files = next(os.walk(path))
    files = list(sorted(filter(lambda x: not x.startswith('qreset.'), files)))
    return files


def get_branch_names(path: Path, *, ref='refs/heads') -> set[str]:
    return set(map(str, run_cmd(
        f'git for-each-ref --format "%(refname:short)" {ref}',
        cwd=path,
    ).stdout.strip().split()))


def clone_with_branches(src_repo: Path, path: Path):
    run_cmd(f'git clone {src_repo} {path.stem}', cwd=path.parent)
    remote_branches = get_branch_names(path, ref=f'refs/remotes/')
    for branch in remote_branches:
        _, fork_branch_name = branch.split('/', 1)
        run_cmd(f"git checkout -b {fork_branch_name}", cwd=path)


class TestScripts(unittest.TestCase):
    BASE_DIR = Path(__file__).resolve().parent.parent
    SCRIPTS_DIR = BASE_DIR / 'scripts'
    TESTS_DIR = BASE_DIR / 'tests'
    INITIALS_DIR = TESTS_DIR / 'initials'
    SUBMITS_DIR = TESTS_DIR / 'submits'
    VALID_LANG = ('sh',)

    def setUp(self) -> None:
        self.tearDown()
        self.SUBMITS_DIR.mkdir(parents=True, exist_ok=True)
        self.INITIALS_DIR.mkdir(parents=True, exist_ok=True)

    def create_initial_repo(self, commits_number=3):
        initial_repo = self.INITIALS_DIR / 'initial_repo'
        initial_repo.mkdir(parents=True, exist_ok=True)
        run_cmd('git init', cwd=initial_repo)
        nonsense_commit(initial_repo, commits_number)
        return initial_repo

    def create_submit_repo(self, *, src_repo: Path) -> Path:
        remote_submit_repo_path = self.SUBMITS_DIR / f'remote_{src_repo.stem}'
        clone_with_branches(src_repo, remote_submit_repo_path)
        run_cmd(f'git remote rm origin', cwd=remote_submit_repo_path)

        submit_repo_path = self.SUBMITS_DIR / src_repo.stem
        clone_with_branches(src_repo, submit_repo_path)

        return submit_repo_path

    def tearDown(self) -> None:
        shutil.rmtree(self.SUBMITS_DIR, ignore_errors=True)
        shutil.rmtree(self.INITIALS_DIR, ignore_errors=True)

    def run_reset_script(self, initial_repo, dst, lang='sh'):
        if lang not in self.VALID_LANG:
            raise Exception(f'lang should be one of followings: {self.VALID_LANG}')

        script_file_name = f'qreset.{lang}'
        shutil.copy(self.SCRIPTS_DIR / script_file_name, dst)
        if lang == 'sh':
            # CHECK:
            #   This block of code may fail in Windows.
            #   We can not run a bash script in Windows like this.
            subprocess.run(f'chmod +x {script_file_name}', cwd=dst, shell=True)
            subprocess.run(f'./{script_file_name} {initial_repo}', cwd=dst, shell=True)

    def raw_test_reset_commits(self, *, lang):
        initial_repo = self.create_initial_repo()
        submit_repo = self.create_submit_repo(src_repo=initial_repo)

        commits_num_before = number_of_commits(submit_repo)
        nonsense_commit_number = 2
        nonsense_commit(submit_repo, number=nonsense_commit_number)
        commits_num_after = number_of_commits(submit_repo)
        self.assertEqual(commits_num_before + nonsense_commit_number, commits_num_after)
        self.run_reset_script(initial_repo, submit_repo, lang=lang)
        self.assertEqual(commits_num_before, number_of_commits(submit_repo))

    def raw_test_files(self, *, lang):
        initial_repo = self.create_initial_repo()
        submit_repo = self.create_submit_repo(src_repo=initial_repo)

        initial_files = get_files_list(submit_repo)
        for file in initial_files:
            (submit_repo / file).unlink()
        commit(submit_repo, msg='deleted all files')
        nonsense_commit_number = 1
        nonsense_commit(submit_repo, number=nonsense_commit_number)
        new_files = get_files_list(submit_repo)
        self.assertNotEqual(initial_files, new_files)
        self.run_reset_script(initial_repo, submit_repo, lang=lang)
        files_after_reset = get_files_list(submit_repo)
        self.assertEqual(initial_files, files_after_reset)

    def raw_test_branches(self, *, lang):
        initial_repo = self.create_initial_repo()
        nonsense_branch(initial_repo, number=3)
        initial_repo_branches = get_branch_names(initial_repo)

        submit_repo = self.create_submit_repo(src_repo=initial_repo)
        submit_repo_branches = get_branch_names(submit_repo)
        self.assertSetEqual(submit_repo_branches, initial_repo_branches)

        new_submit_branches = nonsense_branch(submit_repo, number=3)
        submit_repo_branches = get_branch_names(submit_repo)
        self.assertSetEqual(submit_repo_branches, initial_repo_branches | new_submit_branches)

        self.run_reset_script(initial_repo, submit_repo, lang=lang)

        submit_repo_branches = get_branch_names(submit_repo)
        self.assertSetEqual(submit_repo_branches, initial_repo_branches)

    def test_bash_reset_commits(self):
        self.raw_test_reset_commits(lang='sh')

    def test_bash_test_files(self):
        self.raw_test_files(lang='sh')

    def test_bash_test_branches(self):
        self.raw_test_branches(lang='sh')
