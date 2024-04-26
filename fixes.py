import re
import subprocess
import tempfile
from pathlib import Path
from typing import List


def git_run_get_output(cmd: List[str]) -> str:
    return subprocess.check_output(['git'] + cmd, text=True, encoding='utf-8').rstrip('\n')


def git_run_get_lines(cmd: List[str]) -> List[str]:
    result = git_run_get_output(cmd)
    if not result:
        return []

    return result.split('\n')


def fix_unsupported_course_number_commit(commit: str, tmpdirname: str):
    msg = git_run_get_output([
        'show',
        '-s',
        '--format=%B',
        commit,
    ])

    match = re.search(r'\b(?:Add|Update) (.*)', msg)
    if not match:
        raise Exception(f'Could not find path in commit {commit}')

    path = match.group(1)

    match = re.search(r'\bcourse: ([0-9]{8})\b', msg)
    if not match:
        raise Exception(f'Could not find course number in commit {commit}')

    course_number = match.group(1)

    match = re.fullmatch(r'970300([0-9]{2})', course_number)
    if not match:
        raise Exception(f'Unexpected course number in commit {commit}: {course_number}')

    course_number_fixed = '9730' + match.group(1)

    match = re.fullmatch(r'09703[0-9]/([0-9]{6}/\w+\.(?:png|json))', path)
    if not match:
        raise Exception(f'Unexpected path in commit {commit}: {path}')

    path_after_course_number = match.group(1)
    path_fixed = course_number_fixed + '/' + path_after_course_number

    # https://stackoverflow.com/a/65955938
    git_run_get_output([
        '--work-tree',
        tmpdirname,
        'restore',
        '--source=' + commit,
        '--',
        path,
    ])
    Path(path_fixed).parent.mkdir(parents=True, exist_ok=True)
    (Path(tmpdirname) / path).replace(path_fixed)


def fix_unsupported_course_numbers():
    last_fix_date_1 = '2024-02-13'

    last_fix_details = git_run_get_output([
        'log',
        '-1',
        '--format=%cD%n%B',
        '--after=2024-04-26',
        '--',
        '097030/*',
    ])
    if last_fix_details:
        date, msg = last_fix_details.split('\n', 1)
        if msg != 'Automatic fixes by fixes.py':
            raise Exception(f'Unexpected last fix message: {msg}')

        last_fix_date_1 = date

    last_fix_date_2 = '2024-02-13'

    last_fix_details = git_run_get_output([
        'log',
        '-1',
        '--format=%cD%n%B',
        '--after=2024-04-26',
        '--',
        '973[0-9][0-9][0-9]/*',
    ])
    if last_fix_details:
        date, msg = last_fix_details.split('\n', 1)
        if msg != 'Automatic fixes by fixes.py':
            raise Exception(f'Unexpected last fix message: {msg}')

        last_fix_date_2 = date

    assert last_fix_date_1 >= last_fix_date_2, (last_fix_date_1, last_fix_date_2)
    last_fix_date = max(last_fix_date_1, last_fix_date_2)

    pattern = r'course: 9703[0-9]{4}\b'
    commits_to_fix = git_run_get_lines([
        'log',
        '--after=' + last_fix_date,
        '--format=%H',
        '--perl-regexp',
        '--grep=' + pattern,
    ])
    if not commits_to_fix:
        print('No commits to fix')
        return

    for commit in commits_to_fix:
        print('Reverting commit ' + commit)
        git_run_get_output([
            'revert',
            '--no-commit',
            commit,
        ])

    with tempfile.TemporaryDirectory() as tmpdirname:
        for commit in reversed(commits_to_fix):
            print('Applying a fixed version of commit ' + commit)
            fix_unsupported_course_number_commit(commit, tmpdirname)


def main():
    fix_unsupported_course_numbers()


if __name__ == '__main__':
    main()
