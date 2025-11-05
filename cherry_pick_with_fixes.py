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
    'הידרודינמיקה של אוניות': 'Ship Hydrodynamics',
    'שיטות אנליטיות בהנדסת מכונות 1': 'Analytical Methods in Mechanical Engineering 1',
    'מבוא להנדסת שריפה': 'Introduction to Combustion Engineering',
    'מעבדה בשיטות ניסוי': 'Experimental Methods Laboratory',
    'פרויקט תכן לייצור': 'Design for Manufacturing Project',
    'שיטות מספריות בהנדסת מכונות 1': 'Computational Methods in Mechanical Eng.',
    'תורת הזרימה 2': 'Fluid Mechanics 2',
    'מנועי שריפה פנימית': 'Internal Combustion Engines',
    'פונקציות מרוכבות א\'': 'Complex Functions a',
    'מבוא לשיטות ניסוי': 'Int. to Experimental Methods and Meas.',
    'תרמודינמיקה  2': 'Thermodynamics 2',
    'שימוש המחשב בתורת הזרימה': 'Computational Fluid Dynamics',
    'זרימה דחיסה': 'Compressible Flow',
    'נושאים נבחרים בזרימה ואלסטיות - בינלאומי': 'Topics in Fluids and Elasticity - International',
    'מעבר חום': 'Heat Transfer',
    'אנרגיה מתחדשת ובת קיימא': 'Renewable and Sustainable Energy',
    'פרקים נבחרים בתולדות ישראל - בינלאומי': 'Topics in History of the Jewish People - International',
    'חינוך גופני - הגנה עצמית': 'Physical Education Courses',
    'דינמיקה': 'Dynamics',
    'תורת הזרימה 1': 'Fluid Mechanics 1',
    'סוגיות נבחרות בחברה הישראלית-מרכז בינ"ל - בינלאומי': 'Issues in Contemporary Israeli Society - International',
    'מכניקת מוצקים 2': 'Solid Mechanics 2',
    'אנליזה נומרית מ\'': 'Numerical Analysis M',
    'משוואות דיפרנציאליות חלקיות מ\'': 'Partial Differential Equations/M',
    'מכניקת מוצקים 1': 'Solid Mechanics 1',
    'משוואות דיפרנציאליות רגילות ח\'': 'Ordinary Differential Equations/H',
    'חשבון דיפרנציאלי ואינטגרלי 2ת\'': 'Differential and Integral Calculus 2T',
    'אלגברה 1/מורחב - בינלאומי': 'Algebra 1/Extended',
    'חשבון דיפרנציאלי ואינטגרלי 1מ\' - בינלאומי': 'Differential and Integral Calculus 1M',
    'מבוא למחשב  שפת סי אנגלית - בינלאומי': 'Introduction to Computer-C (En)',
    'פיסיקה 1 - בינלאומי': 'Physics 1',
    'כימיה כללית - בינלאומי': 'General Chemistry',
    'קומבינטוריקה': 'Combinatorics',
    'כימיה אורגנית מורחב 1': 'Organic Chemistry 1/ Extended',
    'יסודות היזמות': 'Innovation Masterclass',
    'מושגי יסוד במתמטיקה': 'Basic Concepts in Mathematics',
    'מערכות ליניאריות מ\' – בינלאומי': 'Linear Systems M – International',
    'חשבון דיפרנציאלי ואינטגרלי 1מ\' - בינלאומי': 'Differential and Integral Calculus 1M - International',
    'פיסיקה 1 - בינלאומי': 'Physics 1 - International',
    'עברית לביה"ס הבינלאומי 44 - בינלאומי': 'Hebrew for the International School 44 - International',
    'כימיה כללית - בינלאומי': 'General Chemistry - International',
    'עברית לביה"ס הבינלאומי 33 - בינלאומי': 'Hebrew for the International School 33 - International',
    'אותות ומערכות': 'Signals and Systems',
    'גרמנית 1': 'German 1',
    'יסודות התקני מוליכים למחצה': 'Basics of Semiconductor Devices',
    'מבוא לכלכלה': 'Introductory Economics',
    'מעבדה בהנדסת חשמל 1א': 'Electrical Engineering Lab 1a',
    'תורת המעגלים החשמליים': 'Theory of Electronic Circuits',
    'תורת הקוואנטים: מבט פילוסופי': 'Quantum Theory: Philosophical Perspectiv',
    'קטליזה על משטחים': 'Catalysis on Surfaces',
    'תקשורת המדע': 'Science Communications',
    'אלגברה 1מ1': 'Algebra 1M1',
    'חשבון דיפרנציאלי ואינטגרלי 1ת\'': 'Differential and Integral Calculus 1T',
    'טורי פורייה והתמרות אינטגרליות': 'Fourier Series and Integral Transforms',
    'מחקרי שוק': 'Marketing Research',
    'משוואות דיפרנציאליות רגילות מ\'': 'Ordinary Differential Equations M',
    'משוואות דפרנציאליות חלקיות ת\'': 'Partial Differential Equations/T',
    'אחריות מקצועית:דילמות חוק ואתיקה': 'Professional Liability Dilemmas',
    'אלגברה ב': 'Algebra B',
    'אקו-פילוסופיה:חשיבה סביבתית': 'Eco-Philosophy:Environmental Thought',
    'מעבדה להנדסת פולימרים': 'Polymer Engineering Laboratory',
    'תרמודינמיקה סטטיסטית בהנדסה כימית': 'Statistical Termodynamics in Chem. Eng.',
    'ממברנות עקרונות וחומרים': 'Membranes Principles and Materials',
    'סטטיסטיקה תעשייתית': 'Industrial Statistics',
    'אנגלית מורחבת לתארים מתקדמים': 'advanced english for graduate students',
}


GIT_MSGS_TO_SKIP = (
    'Automatic fixes by cherry_pick_with_fixes.py',
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

    if msg.startswith('#'):
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

    if histogram_course_name_missing:
        raise Exception(f'histogramCourseNameMissing: {commit}')
    
    if histogram_category_missing:
        raise Exception(f'histogramCategoryMissing: {commit}')

    if histogram_course_name_mismatch:
        course_name = properties['courseName']
        histogram_course_name = properties['histogramCourseName']
        if COURSE_ALTERNATIVE_NAMES.get(histogram_course_name) != course_name:
            from_escaped = histogram_course_name.replace('\'', '\\\'')
            to_escaped = course_name.replace('\'', '\\\'')
            raise Exception(f'histogramCourseNameMismatch in commit {commit}, rule => \'{from_escaped}\': \'{to_escaped}\',')

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

        if properties['courseName'].endswith('- בינלאומי'):
            is_international = True
        elif re.match(r'"?[A-Z]', properties['courseName']):
            is_international = True
        elif re.match(r'"?[א-ת]', properties['courseName']):
            is_international = False
        else:
            raise Exception(f'Unexpected courseName in {properties}')

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
