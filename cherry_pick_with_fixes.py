import re
import subprocess
import tempfile
from pathlib import Path
from typing import List

COURSE_ALTERNATIVE_NAMES = {
    'פוליטיקה של זהויות בישראל - בינלאומי': 'A New Israel Order:a Multicultural Perspective on Israeli Society - International',
    'אלגברה 1מ2': 'Akgebra 1M2',
    'אלגברה 1מ\' - בינלאומי': 'Algebra 1/Extended - International',
    'אלגברה 1מ\'': 'Algebra 1/Extended',
    'אלגברה א\'': 'Algebra Am',
    'שיטות אלגבריות במדעי המחשב': 'Algebraic Methods in Computer Science',
    'אלגוריתמים 1': 'Algorithms 1',
    'אלגוריתמים בביולוגיה חישובית': 'Algorithms in Computational Biology',
    'סטודיו אומן בקמפוס 2': 'Artist in Residence Studio 2',
    'אוטומטים ושפות פורמליות': 'Automata and Formal Languages',
    'יסודות למידה והוראה': 'Basics of Learning and Teaching',
    'ביולוגיה 1': 'Biology 1',
    'חשבון אינפיניטסימלי 1מ\'': 'Calculus 1M',
    'חשבון אינפיניטסימלי 2מ\'': 'Calculus 2M',
    'קומבינטוריקה למדעי המחשב': 'Combinatorics for Cs',
    'מבנה מחשבים': 'Computer Architecture',
    'שרטוט הנדסי ממוחשב - בינלאומי': 'Computer Based Engineering Drawing - International',
    'ארגון ותכנות המחשב': 'Computer Organization and Programming',
    'מבני נתונים 1': 'Data Structures 1',
    'חשבון דיפרנציאלי ואינטגרלי 1מ\' - בינלאומי': 'Differential and Integral Calculus 1M - International',
    'חשבון דיפרנציאלי ואינטגרלי 1מ1': 'Differential and Integral Calculus 1M1',
    'חשבון דיפרנציאלי ואינטגרלי 2מ\' - בינלאומי': 'Differential and Integral Calculus 2M - International',
    'מערכות ספרתיות ומבנה המחשב': 'Digital Systems and Computer Structure',
    'מערכות ספרתיות': 'Digital Systems',
    'דינמיקה - בינלאומי': 'Dynamics - International',
    'הנע חשמלי': 'Electric Actuators',
    'כלכלה הנדסית - בינלאומי': 'Engineering Economics - International',
    'תורת הזרימה 1מ\' - בינלאומי': 'Fluid Mechanics 1M - International',
    'מעבדה בכימיה כללית - בינלאומי': 'General Chemistry Laboratory - International',
    'כימיה כללית - בינלאומי': 'General Chemistry',
    'מעבר חום - בינלאומי': 'Heat Transfer - International',
    'עברית 3': 'Hebrew 3',
    'היסטוריה של המזרח התיכון - בינלאומי': 'History of the Middle-East - International',
    'חשבון אינפיניטסימלי 1': 'Infinitesimal Calculus 1',
    'חשבון אינפי 2': 'Infinitesimal Calculus 2',
    'תורת האינפורמציה': 'Information Theory',
    'מבוא למחשב שפת פייתון בל - בינלאומי': 'Int. to Computing with Python Bl - International',
    'מבוא לחישוב מדעי והנדסי - בינלאומי': 'Int. to Scientific and Eng. Computing - International',
    'מב.לתורת הקבוצות ואוטומטים למדמ"ח': 'Int. to Set Theory and Automata for Cs',
    'מבוא להסתברות וסטטיסטיקה': 'Int.to Probability and Statistics',
    'מבוא לבינה מלאכותית': 'Introduction to Artificial Intelligence',
    'מבוא לתורת הצפינה': 'Introduction to Coding Theory',
    'מבוא למדעי המחשב ח\'': 'Introduction to Computer Science H',
    'מבוא למדעי המחשב מ\'': 'Introduction to Computer Science',
    'מבוא לבקרה': 'Introduction to Control',
    'מבוא לשרטוט הנדסי - בינלאומי': 'Introduction to Engineering Drawing - International',
    'מבוא להנדסת חומרים מ\'1 - בינלאומי': 'Introduction to Materials Engineering M1 - International',
    'מבוא למכטרוניקה': 'Introduction to Mechatronics',
    'מבוא לחוגים ושדות': 'Introduction to Rings and Fields',
    'מבוא לתכנות מערכות': 'Introduction to Systems Programming',
    'מבוא לחבורות': 'Introduction to the Theory of Groups',
    'משפט העבודה בישראל': 'Israeli Labor Law',
    'פרויקט  ב': 'Lab. Project B',
    'אלגברה ליניארית ב\'': 'Linear Algebra 2',
    'מערכות ליניאריות מ\'': 'Linear Systems M',
    'תכן לוגי': 'Logic Design',
    'לוגיקה למדעי המחשב': 'Logic for Cs',
    'אהבה וחוק בעידן הטכנולוגי': 'Love and Law in the Age of Tech.',
    'תהליכי יצור': 'Manufacturing Processes',
    'לוגיקה מתמטית': 'Mathematical Logic',
    'תכן מכני 1': 'Mechanical Engineering Design 1',
    'אלגברה מודרנית ח\'': 'Modern Algebra H',
    'קריפטולוגיה מודרנית': 'Modern Cryptology',
    'הגנה ברשתות': 'Network Security',
    'אלגוריתמים נומריים': 'Numerical Algorithms',
    'מערכות הפעלה': 'Operating Systems',
    'משוואות דיפרנציאליות רגילות ח\' - בינלאומי': 'Ordinary Differential Equations/H - International',
    'מבט על הנדסה כימית וביוכימית': 'Overview of Chem Biochem Eng',
    'משוואות דיפרנציאליות חלקיות מ\' - בינלאומי': 'Partial Differential Equations/M - International',
    'פילוסופיה של זמן ומרחב': 'Philosophy of Time and Space',
    'חינוך גופני - אתלטיקה קלה': 'Physical Education - Athletics',
    'חינוך גופני - משחקי כדור': 'Physical Education Courses',
    'חינוך גופני - משחקי מחבט': 'Physical Education Courses',
    'חינוך גופני-מיועד לסטודנטים חדשים': 'Physical Education-for New Students',
    'פיסיקה 1 - בינלאומי': 'Physics 1',
    'פיסיקה 1': 'Physics 1',
    'פיסיקה 1מ': 'Physics 1M',
    'פיסיקה 2 - בינלאומי': 'Physics 2 - International',
    'פיסיקה 2': 'Physics 2',
    'פיסיקה 2ממ': 'Physics 2Mm',
    'פיסיקה 3': 'Physics 3',
    'מעבדה לפיסיקה 1 - בינלאומי': 'Physics Lab. 1 - International',
    'יסודות הכימיה': 'Principles of Chemistry',
    'עקרונות מערכות הנעת כלי שייט': 'Principles of Marine Engineering',
    'הסתברות מ': 'Probability (Advanced)',
    'הנדסה לאחור': 'Reverse Engineering',
    'בטיחות במעבדות חשמל': 'Safety in Ee Labs.',
    'הוראת מדעים זיקה להוראת טכנולוגיה': 'Science Teaching in Relation to Tech.',
    'סמינר במדעי המחשב 2': 'Seminar in Computer Science 2',
    'סמינר באלגוריתמים מבוזרים': 'Seminar in Distributed Algorithms',
    'תורת הקבוצות': 'Set Theory',
    'מכניקת מוצקים 1 - בינלאומי': 'Solid Mechanics 1 - International',
    'מכניקת מוצקים 2 - בינלאומי': 'Solid Mechanics 2 - International',
    'אנגלית טכנית-מתקדמים ב\'': 'Technical English-Advanced B',
    'הרנסנס באיטליה:מסע אמנותי ותרבותי': 'The Renaissance in Italy: An Artistic and Cultural Journey',
    'תורת הקומפילציה': 'Theory of Compilation',
    'תורת החישוביות': 'Theory of Computation',
    'תרמודינמיקה 1 - בינלאומי': 'Thermodynamics 1 - International',
    'נושאים בביולוגיה': 'Topics in Biology',
    '"משחקי גבורה" - מלחמה בקולנוע': 'War and Film',
    'מערכות ליניאריות מ\' - בינלאומי': 'Linear Systems M - International',
    'פרויקט דגל - רכב מרוץ פורמולה': 'Flagship Project - Formula Racecar',
    'מכניקת מוצקים 2מ - בינלאומי': 'Solid Mechanics 2M - International',
    'טרור,ג\'יהד ותגובה מדינית - בינלאומי': 'Terrorism,Jihad and State Response - International',
    'מבוא למחשב שפת פייתון - בל - בינלאומי': 'Int. to Computing with Python -Bl - International',
    'פיסיקה 1 - בינלאומי': 'Physics 1 - International',
    'כימיה כללית - בינלאומי': 'General Chemistry - International',
    'מתמטיקה מכינה בינלאומי': 'Math Pa-Int',
    'פיזיקה בינלאומי': 'Physics-Pa-Int',
    'עברית בינלאומי': 'Hebrew-Pa-Int',
    'אוירודינמיקה בלתי דחיסה': 'Incompressible Aerodynamics',
    'אלגברה אמ\'': 'Algebra Am',
    'אלגברה במ\'': 'Algebra Bm',
    'היסטורית כאב בעיני פילוסופים': 'History of Pain by Philosophers',
    'חינוך גופני - התעמלות כללית בנות': 'Physical Education Courses',
    'למידה והור.מדעים והנ.בחינוך גבוה': 'Learning and Teaching Stem in Higher Ed.',
    'מבוא להסתברות ח\'': 'Introduction to Probability H',
    'מבוא לייצוג ועיבוד מידע': 'Introduction to Data Processing and Representation',
    'מבוא לסטטיסטיקה': 'Introduction to Statistics',
    'מסדי נתונים': 'Databases',
    'מעבדה לפיזיקה - גלים - 3מפ\'': 'Physics Lab. 3Mp',
    'מערכות דינמיות': 'Dynamic Systems',
    'פיסיקה קוונטית 1': 'Quantum Physics 1',
    'פסיכולוגיה של המוזיקה': 'Psychology of Music',
    'פרויקט בבינה מלאכותית': 'Artificial Intelligence and Heuristics Laboratory',
    'שיטות חישוביות באופטימיזציה': 'Computational Methods in Optimization',
}

GIT_MSGS_TO_CHERRY_PICK = (
    'Add cherry_pick_with_fixes.py',
    'Add GitHub Actions workflow for checks and fixes',
    'Add more english course names',
    'Add organize_mismatched.py',
    'checks.py: Add handled mismatches',
    'checks.py: Add more details to output',
    'checks.py: Check for missing data',
    'checks.py: Simplify check for mismatches',
    'Cherry pick since last fix',
    'deploy.php: Skip mismatches',
    'Fix commit_author in the check-and-fix workflow',
    'Fix handling properties with a colon',
    'Fixes to fixes.py (2)',
    'Fixes to fixes.py',
    'organize_mismatched.py: add rmdir',
    'Remove old comment from deploy.php',
    'Run cherry_pick_with_fixes.py in CI',
    'Update check-and-fix.yml with fixes from master',
    'Update checks.py git functions',
    'Update cherry_pick_with_fixes.py',
    'Update GitHub Actions dependencies',
    'Update GitHub Actions',
    'Update last_handled_mismatch',
)


GIT_MSGS_TO_SKIP = (
    'Automatic fixes by cherry_pick_with_fixes.py',
    'Automatic fixes by fixes.py',
    'Fix mismatched submission',
    'Manual fixes',
    'Manually fix mismatched entries',
    'Remove mismatch commits (files already submitted)',
    'Remove mismatched histogram (already submitted)',
)


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

    if msg in GIT_MSGS_TO_CHERRY_PICK or msg.startswith('#'):
        print(f'Cherry-picking as is: [{commit}] {msg}')
        git_run(['add', '.'])
        git_run(['commit', '--quiet', '-m', 'temp'])
        git_run(['cherry-pick', '--no-commit', commit])
        git_run(['reset', '--quiet', 'HEAD~'])
        return

    if msg in GIT_MSGS_TO_SKIP:
        print(f'Skipping: [{commit}] {msg}')
        return

    title, properties = msg.split('\n\n', 2)
    properties = properties.strip().split('\n')
    properties = dict(property.split(': ', 1) for property in properties)

    override_course = None
    override_semester = None
    override_category = None

    if commit in (
        '60a6e7bf0581b8cb71663d7957fabc0bf9863729',
        'be7884122e9fbb028ea7f65171818f6c826addef',
    ):
        override_course = '236350'
        override_semester = '202202'
    elif commit in (
        '52616fdf3603cd494df41975694e7d7af446a177',
        '8c8303a720b52efa18adcfc10c1848f91a9f5888',
    ):
        override_course = '044102'
        override_semester = '202101'
    elif commit in (
        '5c3bf1dfeee74ad5bc4e8e84354d6e7471f7c152',
        '52d6dcd0843a6a5a10cdd5721bad488d905fa0a0',
    ):
        override_course = '014143'
        override_semester = '202301'
    elif commit in (
        '17d2bfea4b1efc215bf694ac632cdca0dd1524db',
        '055cb9ec08bd58927481aab8309d6417feea2d6b',
    ):
        override_category = 'Exam_B'
        override_semester = '201401'
    elif commit in (
        '3b20e2e0a20f79cf3a8b33f08504e52399cb916c',
        'bc30638abd6a1dd79fb7ba8357becec1b2801ba0',
    ):
        override_course = '234218'
        override_semester = '202301'
    elif commit in (
        '1e207ab8761b97ecd6d1faa49c8b30ef6a190624',
        'c4220082689de967bc56587dd8d59b3b05ca0035',
    ):
        override_course = '234292'
        override_semester = '202301'
    elif commit in (
        '3cee07f9b8cd47ebb196a63196508105a105a05a',
        '3d5389aa088c89855066bedfa13f87f0e1b01b4f',
    ):
        override_course = '114037'
        override_semester = '202301'
    elif commit in (
        'd5163e5ceaa68a2858fa69028cc13a01df0642a2',
        '7d004a95d2c6419452123cdeae7217c569220050',
    ):
        override_course = '134082'
        override_semester = '202301'
    elif commit in (
        '4ee4b6316675f781042b3bb02a965a4a21d73ff8',
        '94dfe383b439a3b0adcd1c56e94571450cf17d38',
    ):
        override_course = '207450'
    elif commit in (
        '1610e81865e4b9c4b1f043df58e5005df3be7a7d',
        'e7f22338b9120f09ad5ee7a1f705ee1ad251aa33',
    ):
        override_course = '046278'
        override_semester = '202302'

    if override_course:
        # 9730xy -> 97030xy
        override_course = re.sub(r'^9730(\d\d)$', r'97030\1', override_course)
        override_course = override_course[:-3] + '0' + override_course[-3:]
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

    if histogram_course_name_missing:
        raise Exception(f'histogramCourseNameMissing: {commit}')
    
    if histogram_category_missing:
        raise Exception(f'histogramCategoryMissing: {commit}')

    if histogram_course_name_mismatch:
        course_name = properties['courseName']
        histogram_course_name = properties['histogramCourseName']
        if COURSE_ALTERNATIVE_NAMES.get(histogram_course_name) != course_name:
            raise Exception(f'histogramCourseNameMismatch: {commit} ({course_name} != {histogram_course_name})')

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

    # Remove middle zero.
    pattern = r'(0{0,2}[1-9][0-9]|0{0,1}[1-9][0-9]{2})0[0-9]{3}|970300\d\d'
    if not re.fullmatch(pattern, course_number) or course_number[-4] != '0':
        raise Exception(f'Unexpected course number in commit {commit}: {course_number}')

    course_number_fixed = course_number[:-4] + course_number[-3:]

    # Handle special cases:
    # 97030xy -> 9730xy
    course_number_fixed = re.sub(r'^97030(\d\d)$', r'9730\1', course_number_fixed)

    # Pad with 6 zeros.
    course_number_fixed = course_number_fixed.zfill(6)

    match = re.fullmatch(r'(?:_mismatch_)?[0-9]{6}/([0-9]{6})/(\w+)\.(png|json)', path)
    if not match:
        raise Exception(f'Unexpected path in commit {commit}: {path}')

    semester_from_path = match.group(1)
    category_from_path = match.group(2)
    file_extension_from_path = match.group(3)
    path_fixed = (
        course_number_fixed + '/' +
        (override_semester or semester_from_path) + '/' +
        (override_category or category_from_path) + '.' +
        file_extension_from_path)

    path_without_mismatch = path.removeprefix('_mismatch_')
    if path_fixed != path_without_mismatch:
        if override_course or override_semester or override_category:
            print(f'Overriding path in commit {commit}: {path_without_mismatch} -> {path_fixed}')
        elif path_without_mismatch == re.sub(r'^9730\d\d/', r'097030/', path_fixed):
            pass
        else:
            raise Exception(f'Unexpected path in commit {commit}: {path_without_mismatch} != {path_fixed}')

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

    with tempfile.TemporaryDirectory() as tmpdirname:
        for commit in reversed(commits):
            print('Applying a fixed version of commit ' + commit)
            cherry_pick_commit_with_fixes(commit, tmpdirname)


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
