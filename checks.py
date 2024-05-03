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
    handled_mismatches = {
        '207624079f4e37a9db268907006d256bbf86dc8c',
        'c2048d026e16b37a0671ef743cce1bfd1ab7d8d2',
        '60a6e7bf0581b8cb71663d7957fabc0bf9863729',
        'be7884122e9fbb028ea7f65171818f6c826addef',
        '2118dd6e7afd5987cf3bdb1f46b9b948d4c04883',
        '6d638fa8d4e024db8c3bf7c77ab5bf4ffe7628f4',
        '2b730452defff7557b3b0619c84fba536ae9e899',
        'f3e42486d838280a45cbfd427830a64d8fa449f5',
        '8bd76399c30ec4babbff885c2e6cdffb4b413456',
        '1fe2fad976f1e366883339a1484a92f4025da55f',
        '54ceefe9cb4c275d92d96903251628d106b53ab5',
        '7ff3646e217f80491667bd5119991f79d40d0c47',
        'c88a3d7e94d67cbd1d81be14bd9fa7f3186d6e61',
        'b49b6885cb3c043bffbf7b34e6fb3a7e732cb5da',
    }

    unhandled_mismatches = []
    for commit in git_run_get_lines(['log', '--format=%H', '--grep=Mismatch: true']):
        if commit not in handled_mismatches:
            unhandled_mismatches.append(commit)

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
