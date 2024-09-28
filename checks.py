import subprocess
import sys
from typing import List


def git_run(cmd: List[str]) -> str:
    return subprocess.check_output(['git'] + cmd, text=True, encoding='utf-8')


def git_run_get_lines(cmd: List[str]) -> List[str]:
    result = git_run(cmd).rstrip('\n')
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


def main():
    checks_failed = False

    if not check_bad_images():
        checks_failed = True

    if checks_failed:
        sys.exit(1)


if __name__ == '__main__':
    main()
