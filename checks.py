import subprocess
import sys
from typing import List


def git_run_get_lines(cmd: List[str]) -> List[str]:
    result = subprocess.check_output(['git'] + cmd, text=True, encoding='utf-8').rstrip('\n')
    if not result:
        return []

    return result.split('\n')


def check_bad_images() -> bool:
    bad_images = []
    for line in git_run_get_lines(['ls-tree', '-r', 'HEAD']):
        if '76b85c3ecefcb57e8856889dbb44b31c52b50fc3' in line:
            bad_images.append(line)

    if not bad_images:
        return True

    print('Bad images:')
    for line in bad_images:
        print(line)

    print('For each result, revert:')
    print('git revert `git log --format="%H" -1 -- <image>.png`')
    print('Or restore:')
    print('git restore --source=`git log --format="%H" -1 -- <image>.png`~ -- <image>.png')
    print()

    return False


def check_mismatches() -> bool:
    last_handled_mismatch = 'b49b6885cb3c043bffbf7b34e6fb3a7e732cb5da'

    unhandled_mismatches = git_run_get_lines([
        'log',
        f'{last_handled_mismatch}..',
        '--format=%H',
        '--perl-regexp',
        '--grep=(Missing|Mismatch): true'
    ])
    if not unhandled_mismatches:
        return True

    print('Unhandled mismatches:')
    for commit in unhandled_mismatches:
        print(commit)
    print()

    return False


def check_unsupported_course_numbers() -> bool:
    # These course numbers are handled separately:
    # 97030005
    # 97030006
    # 97030007
    # 97030008
    # 97030009
    # 97030010
    # 97030011
    # 97030012

    pattern = r'course: (?!([1-9][0-9]{1,2}0[0-9]{3}|9703000[5-9]|9703001[0-2])\b)'

    bad_commits = []
    for commit in git_run_get_lines(['log', '--format=%H', '--perl-regexp', '--grep=' + pattern]):
        bad_commits.append(commit)

    if not bad_commits:
        return True

    print('Commits with unsupported course numbers:')
    for commit in bad_commits:
        print(commit)
    print()

    return False


def main():
    checks_failed = False

    if not check_bad_images():
        checks_failed = True

    if not check_mismatches():
        checks_failed = True

    if not check_unsupported_course_numbers():
        checks_failed = True

    if checks_failed:
        sys.exit(1)


if __name__ == '__main__':
    main()
