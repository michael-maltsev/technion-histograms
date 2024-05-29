from pathlib import Path


for course in Path('.').glob('_mismatch_*'):
    assert course.is_dir()

    for sem in course.glob('*'):
        assert sem.is_dir()

        for f in sem.glob('*'):
            assert f.is_file()

            f2 = f.parent.parent.parent / f.parts[-3].removeprefix('_mismatch_') / f.parts[-2] / f.parts[-1]
            print(f'{f} -> {f2}')

            f.replace(f2)

        sem.rmdir()

    course.rmdir()
