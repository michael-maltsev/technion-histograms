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


def check_mismatches() -> bool:
    last_handled_mismatch = '8950f1d5f9967a8eee6f9332bd6fbcc37b251f90:'

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
        commit_message = git_run(['log', '-1', '--format=%ci\n\n%B', commit])

        date, _, properties = commit_message.split('\n\n', 2)
        properties = properties.strip().split('\n')
        properties = dict(property.split(': ', 1) for property in properties)

        description = ''

        if properties.get('histogramCourseNameMissing', 'false') != 'false':
            description += 'histogramCourseNameMissing, '

        if properties.get('histogramCourseNameMismatch', 'false') != 'false':
            course_name = properties['courseName']
            histogram_course_name = properties['histogramCourseName']
            description += f'histogramCourseNameMismatch ({course_name} != {histogram_course_name}), '

        if properties.get('histogramCategoryMissing', 'false') != 'false':
            description += 'histogramCategoryMissing, '

        if properties.get('histogramCategoryMismatch', 'false') != 'false':
            category = properties['category']
            histogram_category = properties['histogramCategory']
            description += f'histogramCategoryMismatch ({category} != {histogram_category}), '

        if description:
            description = description.removesuffix(', ')
        else:
            description = '(unknown)'

        print(f'[{date}] {commit}: {description}')
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
