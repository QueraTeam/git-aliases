import os
import subprocess
import unittest
from pathlib import Path
from uuid import uuid4
import shutil


def random_name(length=8):
    return uuid4().hex[:length]


def run_cmd(*args, **kwargs):
    return subprocess.run(*args, **kwargs, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def commit(path: Path, msg):
    run_cmd('git add .', cwd=path)
    run_cmd(f'git commit -m "{msg}" > /dev/null', cwd=path)


def nonsense_commit(path: Path, number=1) -> None:
    for i in range(number):
        some_file = path / random_name()
        some_file.touch()
        commit(path, "nonsense")


def number_of_commits(path: Path):
    return int(run_cmd('git log --format=oneline | wc -l', cwd=path, ).stdout.strip().decode('utf-8'))


def get_files_list(path: Path):
    _, _, files = next(os.walk(path))
    files = list(sorted(filter(lambda x: not x.startswith('reset.'), files)))
    return files


class TestPythonScript(unittest.TestCase):
    BASE_DIR = Path(__file__).resolve().parent.parent
    TESTS_DIR = BASE_DIR / 'tests'
    INITIALS_DIR = TESTS_DIR / 'initials'
    SUBMITS_DIR = TESTS_DIR / 'submits'

    def setUp(self) -> None:
        run_cmd(f'rm -rf {self.SUBMITS_DIR}')
        self.SUBMITS_DIR.mkdir(parents=True, exist_ok=True)
        run_cmd(f'rm -rf {self.INITIALS_DIR}')
        self.INITIALS_DIR.mkdir(parents=True, exist_ok=True)

        self.initial_repo = self.INITIALS_DIR / 'initial_repo'
        self.initial_repo.mkdir(parents=True, exist_ok=True)
        run_cmd('git init', cwd=self.initial_repo)
        nonsense_commit(self.initial_repo, 3)

        self.submit_repo = self.create_submit_repo(src_repo=self.initial_repo)

    def tearDown(self) -> None:
        run_cmd(f'rm -rf {self.SUBMITS_DIR} {self.INITIALS_DIR}')

    def run_reset_script(self):
        shutil.copy(self.BASE_DIR / 'reset.py', self.submit_repo)
        run_cmd(f'python3 reset.py {self.initial_repo}', cwd=self.submit_repo)

    def create_submit_repo(self, *, src_repo) -> Path:
        run_cmd(f'git clone {src_repo}', cwd=self.SUBMITS_DIR)
        repo_name = src_repo.stem
        return self.SUBMITS_DIR / repo_name

    def test_reset_commits(self):
        commits_num_before = number_of_commits(self.submit_repo)
        nonsense_commit_number = 2
        nonsense_commit(self.submit_repo, number=nonsense_commit_number)
        commits_num_after = number_of_commits(self.submit_repo)
        self.assertEqual(commits_num_before + nonsense_commit_number, commits_num_after)
        self.run_reset_script()
        self.assertEqual(commits_num_before, number_of_commits(self.submit_repo))

    def test_files(self):
        initial_files = get_files_list(self.submit_repo)
        for file in initial_files:
            (self.submit_repo / file).unlink()
        commit(self.submit_repo, msg='deleted all files')
        nonsense_commit_number = 1
        nonsense_commit(self.submit_repo, number=nonsense_commit_number)
        new_files = get_files_list(self.submit_repo)
        self.assertNotEqual(initial_files, new_files)
        self.run_reset_script()
        files_after_reset = get_files_list(self.submit_repo)
        self.assertEqual(initial_files, files_after_reset)
