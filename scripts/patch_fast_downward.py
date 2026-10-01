"""Keep Fast Downward's shared library alive until the environment closes."""
import hashlib
import importlib.util
from pathlib import Path


def main():
    spec = importlib.util.find_spec('fast_downward')
    if spec is None or spec.origin is None:
        raise RuntimeError('fast_downward is not installed')
    target = Path(spec.origin).parent / 'interface.py'
    text = target.read_text()
    if 'downward_lib._evoke_tempdir = tempdir' in text:
        print('Fast Downward patch already applied')
        return
    if hashlib.sha256(text.encode()).hexdigest() != 'c5c23ec7d6d8acd845fb6788c8edd01f7d527ee1f0148ba333e7bacc517c151b':
        raise RuntimeError('Unexpected Fast Downward interface version')
    begin = text.index('    with tempfile.TemporaryDirectory() as tmpdir:', text.index('def load_lib():'))
    end = text.index('\n    return downward_lib', begin)
    lines = text[begin:end].splitlines()
    body = '\n'.join(line[4:] if line.startswith('    ') else line for line in lines[1:])
    body = body.replace('    downward_lib = cdll.LoadLibrary(downward_lib_path)',
                        '    downward_lib = cdll.LoadLibrary(downward_lib_path)\n    downward_lib._evoke_tempdir = tempdir')
    text = text[:begin] + '    tempdir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)\n    tmpdir = tempdir.name\n' + body + '\n' + text[end:]
    text = text.replace('    dlclose_func(downward_lib._handle)',
                        '    dlclose_func(downward_lib._handle)\n    if hasattr(downward_lib, "_evoke_tempdir"):\n        downward_lib._evoke_tempdir.cleanup()')
    target.write_text(text)
    print('Fast Downward patch applied', hashlib.sha256(text.encode()).hexdigest())


if __name__ == '__main__':
    main()
