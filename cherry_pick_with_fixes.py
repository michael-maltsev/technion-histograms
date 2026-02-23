import functools
import re
import subprocess
import tempfile
from pathlib import Path
from typing import List

from course_lookup import get_available_semesters, lookup_by_number

COURSE_ALTERNATIVE_NAMES = {
}


@functools.cache
def available_semesters():
    return frozenset(get_available_semesters())


def git_run(cmd: List[str]):
    subprocess.check_call(['git'] + cmd, text=True)


def git_run_get_output(cmd: List[str]) -> str:
    return subprocess.check_output(['git'] + cmd, text=True, encoding='utf-8').rstrip('\n')


def git_run_get_lines(cmd: List[str]) -> List[str]:
    result = git_run_get_output(cmd)
    if not result:
        return []

    return result.split('\n')


def cherry_pick_commit_with_fixes(commit: str, tmpdirname: str):
    msg = git_run_get_output([
        'show',
        '-s',
        '--format=%B',
        commit,
    ])

    if msg.lower().startswith('infra:'):
        print(f'Cherry-picking as is: [{commit}] {msg}')
        git_run(['add', '.'])
        git_run(['commit', '--quiet', '-m', 'temp'])
        git_run(['cherry-pick', '--no-commit', commit])
        git_run(['reset', '--quiet', 'HEAD~'])
        return

    title, properties = msg.split('\n\n', 2)
    properties = properties.strip().split('\n')
    properties = dict(property.split(': ', 1) for property in properties)

    override_course = None
    override_semester = None
    override_category = None

    if commit in (
        '3ffdb2f9316a85df96e41b44997922595172447d',
        '51005d4c21963773d50d923c98645b5e55fb7228',
    ):
        override_course = '01040035'
        override_semester = '202101'
    elif commit in (
        '8ff1bc8a5cf42d3eff0a4cfdad6cbe3f70266d0d',
        '90c87340051e36daaf371249fd74dfed9e659dc9',
    ):
        override_course = '01040166'
    elif commit in (
        'ef3c29fd280b18f8731b441df278043d7befa602',
        '857f8e5d6d8be618546ae49c0c545c7d00973fe8',
    ):
        override_course = '01040065'
        override_semester = '202401'
    elif commit in (
        'c2bcebae51abb72d595d60332b1780fef1b9210e',
        'c35258b618980147775dcf267aaf6f53dfe1e396',
    ):
        override_course = '01140074'
        override_semester = '202201'
    elif commit in (
        '0173041a85dc18bbccc1b64eba88680b83626314',
        'a15aa24ea03e36a585ba4dba57e23169b87b2950',
    ):
        override_course = '00140863'
        override_semester = '202403'

    if override_course:
        properties['course'] = override_course
        properties['courseName'] = properties['histogramCourseName']
        properties['histogramCourseNameMismatch'] = 'false'

    if override_category:
        properties['category'] = override_category
        properties['histogramCategoryMismatch'] = 'false'

    histogram_course_name_missing = properties.get('histogramCourseNameMissing', 'false') != 'false'
    histogram_course_name_mismatch = properties.get('histogramCourseNameMismatch', 'false') != 'false'
    histogram_category_missing = properties.get('histogramCategoryMissing', 'false') != 'false'
    histogram_category_mismatch = properties.get('histogramCategoryMismatch', 'false') != 'false'

    # Temporary: https://github.com/TheBooker66/Technion-Plus-Plus/issues/27
    if histogram_course_name_missing and histogram_course_name_mismatch:
        course_name = properties['courseName']
        histogram_course_name = properties['histogramCourseName']
        if histogram_course_name and histogram_course_name == course_name:
            histogram_course_name_missing = False
            histogram_course_name_mismatch = False

    if histogram_course_name_missing:
        raise Exception(f'histogramCourseNameMissing: {commit}')

    if histogram_category_missing:
        raise Exception(f'histogramCategoryMissing: {commit}')

    if histogram_category_mismatch:
        category = properties['category']
        histogram_category = properties['histogramCategory']
        if not (
            (category == re.sub(r'^(?:Exam|Moed|Moed_|Test_Mohed_)([ABC])$', r'Exam_\1', histogram_category)) or
            (category == 'Exam_C' and histogram_category == 'Exam_Special_1') or
            (category == 'Finals' and histogram_category == 'ציון סופי במערכת האקדמית במחשב המרכזי')
        ):
            raise Exception(f'histogramCategoryMismatch: {commit} ({category} != {histogram_category})')

    match = re.search(r'\b(?:Add|Update) (.*)', title)
    if not match:
        raise Exception(f'Could not find path in commit {commit}')

    path = match.group(1)

    course_number = properties['course']

    course_number_fixed = course_number.zfill(8)
    course_number_fixed_legacy = None

    # Remove middle zero.
    pattern = r'(0{0,2}[1-9][0-9]|0{0,1}[1-9][0-9]{2})0[0-9]{3}|970300\d\d'
    if re.fullmatch(pattern, course_number) and course_number[-4] == '0':
        course_number_fixed_legacy = course_number[:-4] + course_number[-3:]

        # Handle special cases:
        # 97030xy -> 9730xy
        course_number_fixed_legacy = re.sub(r'^97030(\d\d)$', r'9730\1', course_number_fixed_legacy)

        # Pad with 6 zeros.
        course_number_fixed_legacy = course_number_fixed_legacy.zfill(6)
    elif not re.fullmatch(r'[0-9]{6,8}', course_number):
        raise Exception(f'Unexpected course number in commit {commit}: {course_number}')

    match = re.fullmatch(r'(?:_mismatch_)?_?[0-9]{5,8}/([0-9]{6})/(\w+)\.(png|json)', path)
    if not match:
        raise Exception(f'Unexpected path in commit {commit}: {path}')

    semester_from_path = match.group(1)
    category_from_path = match.group(2)
    file_extension_from_path = match.group(3)

    if histogram_course_name_mismatch:
        course_name = properties['courseName']
        histogram_course_name = properties['histogramCourseName']
        matched = COURSE_ALTERNATIVE_NAMES.get(histogram_course_name) == course_name

        if not matched:
            course_name = properties['courseName']
            histogram_course_name = properties['histogramCourseName']
            effective_semester = override_semester or semester_from_path
            year = int(effective_semester[:4])
            session = 199 + int(effective_semester[4:])
            if (year, session) not in available_semesters():
                # Fall back to the latest available year with the same session.
                fallback = [y for y, s in available_semesters() if s == session]
                if fallback:
                    year = max(fallback)
                else:
                    year = None
            if year is not None:
                looked_up_name_he = lookup_by_number(year, session, course_number, "he")
                looked_up_name_en = lookup_by_number(year, session, course_number, "en")
                matched = looked_up_name_he == histogram_course_name and looked_up_name_en == course_name

        if not matched:
            from_escaped = histogram_course_name.replace('\'', '\\\'')
            to_escaped = course_name.replace('\'', '\\\'')
            raise Exception(f'histogramCourseNameMismatch in commit {commit}, rule => \'{from_escaped}\': \'{to_escaped}\',')

    path_fixed_suffix = (
        '/' +
        (override_semester or semester_from_path) + '/' +
        (override_category or category_from_path) + '.' +
        file_extension_from_path)
    path_fixed = course_number_fixed + path_fixed_suffix

    path_fixed_legacy = None
    if course_number_fixed_legacy:
        path_fixed_legacy = course_number_fixed_legacy + path_fixed_suffix

    path_without_mismatch = path.removeprefix('_mismatch_')
    if path_without_mismatch == path_fixed:
        pass
    elif path_fixed_legacy and path_without_mismatch == path_fixed_legacy:
        pass
    elif override_course or override_semester or override_category:
        print(f'Overriding path in commit {commit}: {path_without_mismatch} -> {path_fixed}')
    elif path_fixed_legacy and path_without_mismatch == re.sub(r'^9730\d\d/', r'097030/', path_fixed_legacy):
        pass
    elif path_without_mismatch == '_' + course_number + path_fixed_suffix:
        pass
    else:
        raise Exception(f'Unexpected path in commit {commit}: {path_without_mismatch} != {path_fixed}')

    if category_from_path != 'Staff':
        is_international = properties['histogramCourseName'].endswith('- בינלאומי')
    else:
        # The Staff.json file has limited information. Hopefully it's good
        # enough most of the time.
        if 'histogramCourseName' in properties:
            raise Exception(f'Unexpected histogramCourseName in {properties}')

        is_international = False
        if properties['courseName'].endswith('- בינלאומי') or properties['courseName'].endswith('- International'):
            is_international = True
        # elif re.match(r'"?[A-Z]', properties['courseName']):
        #     is_international = True
        # elif re.match(r'"?[א-ת]', properties['courseName']):
        #     is_international = False
        # else:
        #     raise Exception(f'Unexpected courseName in {properties}')
        #
        # Previously, we had the heuristic above, since we got submissions with
        # a generic English courseName, which couldn't be detected as
        # international without histogramCourseName. Last such submission was in
        # October 2024, more than a year ago:
        #
        # commit 9b22a759b2eac6482c2fa4e8244d23a98e8153e2
        # Date:   Sun Oct 13 02:30:04 2024 +0300
        #     courseName: General Chemistry
        #     histogramCourseName: כימיה כללית - בינלאומי
        #
        # This heuristic also caused false positives for non-international
        # courses with English names. It was eventually removed. Hopefully there
        # won't be any more submissions like that.


    if is_international:
        path_fixed = re.sub(r'\.\w+$', r'_international\g<0>', path_fixed)

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


def cherry_pick_with_fixes(after_commit, last_commit):
    commits = git_run_get_lines([
        'rev-list',
        '--ancestry-path',
        f'{after_commit}..{last_commit}',
    ])

    errors = 0

    with tempfile.TemporaryDirectory() as tmpdirname:
        for commit in reversed(commits):
            print('Applying a fixed version of commit ' + commit)
            try:
                cherry_pick_commit_with_fixes(commit, tmpdirname)
            except Exception as e:
                print(f'Error: {e}')
                errors += 1

    if errors:
        raise Exception(f'Failed to apply {errors} commits')


def main():
    last_commit = git_run_get_output(['rev-parse', 'HEAD'])

    after_commit = git_run_get_output([
        'log',
        '-1',
        '--format=%H',
        '--grep',
        r'Automatic fixes by cherry_pick_with_fixes\.py',
    ])

    if after_commit == last_commit:
        print('No fixes to apply')
        return

    print(f'Resetting to {after_commit}')
    git_run(['restore', '--source', after_commit, '.'])

    print(f'Cherry-picking commits between {after_commit} and {last_commit}')

    cherry_pick_with_fixes(after_commit, last_commit)


if __name__ == '__main__':
    main()
