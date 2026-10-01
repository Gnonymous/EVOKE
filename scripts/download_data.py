#!/usr/bin/env python3
"""Download the ALFWorld TextWorld resources used by the evaluation."""
import argparse
import hashlib
import json
import urllib.request
import zipfile
from pathlib import Path

URLS = [
    'https://github.com/alfworld/alfworld/releases/download/0.2.2/json_2.1.1_json.zip',
    'https://github.com/alfworld/alfworld/releases/download/0.2.2/json_2.1.1_pddl.zip',
    'https://github.com/alfworld/alfworld/releases/download/0.4.2/json_2.1.3_tw-pddl.zip',
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root', type=Path, required=True, help='Destination ALFWorld resource directory')
    args = parser.parse_args()
    args.data_root.mkdir(parents=True, exist_ok=True)
    cache = Path.home() / '.cache/evoke/alfworld-downloads'
    cache.mkdir(parents=True, exist_ok=True)
    records = []
    for url in URLS:
        archive = cache / url.rsplit('/', 1)[1]
        if not archive.exists():
            temporary = archive.with_suffix('.partial')
            with urllib.request.urlopen(url, timeout=60) as response, temporary.open('wb') as stream:
                while chunk := response.read(1 << 20):
                    stream.write(chunk)
            temporary.replace(archive)
        with zipfile.ZipFile(archive) as source:
            for entry in source.namelist():
                if not (args.data_root / entry).resolve().is_relative_to(args.data_root.resolve()):
                    raise ValueError('Unsafe archive path')
            source.extractall(args.data_root)
        h = hashlib.sha256()
        with archive.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1 << 20), b''):
                h.update(chunk)
        records.append(dict(url=url, sha256=h.hexdigest(), bytes=archive.stat().st_size))
        print(f'Installed {archive.name}', flush=True)
    (args.data_root / 'downloads.json').write_text(json.dumps(records, indent=2) + '\n')


if __name__ == '__main__':
    main()
