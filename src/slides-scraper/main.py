import re
import os
import sys

from typing import Any
from urllib.parse import urlparse
from urllib.request import urlretrieve
from pathlib import Path

"""
Usage:
    Call with python main.py <path-to-input-file> <path-to-output-file>

    Only partially tested
"""

input = sys.argv[1]
output = sys.argv[2]

COMPRESS = False  # Not implemented
COMP_TRESHOLD = 1048576  # 1MB
IGNORE_COMPRESSED_FORMATS = ['.gif']
FOLDER = "attachments/"
FALLBACK_EXT = 'jpg'


def get_unsplash_filetype(url: str) -> str:
    try:
        return re.findall(r'fm=(\w+)', url)[0]
    except IndexError:
        return ''


def get_filename(url: str, folder: str = FOLDER, def_ext: str = FALLBACK_EXT) -> str:
    p = Path(urlparse(url).path)
    if p.suffix:
        return f'{folder}{p.name}'

    # Check if unsplash url contains filetype hint
    unsplash_ext = get_unsplash_filetype(url)
    if unsplash_ext:
        return f'{folder}{p.name}.{unsplash_ext}'

    # Fallback to def_ext
    return f'{folder}{p.name}.{def_ext}'


def scan_images(content: str) -> list[Any]:
    images = re.findall(r'data-background-image=\"(https:\/\/[^\"]+)\"', content)
    images += re.findall(r'\<img.+data-src=\"(https:\/\/[^\"]+)\"', content)

    return [[url, get_filename(url)] for url in images]


def compress_image(fn: str, max_size: int = COMP_TRESHOLD) -> None:
    if Path(fn).suffix in IGNORE_COMPRESSED_FORMATS:
        print(f'Skipping compression of {Path(fn).suffix} ({fn})')
        return

    if os.stat(fn).st_size > max_size:
        print("Compressing ", fn)
        raise NotImplementedError
    else:
        print(f'Skipping compression of {Path(fn).suffix} ({fn})')
        raise NotImplementedError


def download_tuples(tuples: list[Any], compress: bool = False) -> None:
    for url, fn in tuples:
        Path(fn).parent.mkdir(exist_ok=True, parents=True)
        if not Path(fn).is_file():
            urlretrieve(url, fn)


def update_content(content: str, tuples: list[Any]) -> str:
    for url, fn in tuples:
        content = content.replace(url, fn)
    return content


if __name__ == '__main__':
    if not input.lower().endswith('.html') or not output.lower().endswith('.html'):
        raise RuntimeError("Invalid filetypes")

    # Read the input html contents and store it
    content = open(input, 'r').read()

    # Get pairs of image urls and filenames from the src urls
    pairs = scan_images(content)

    # Get absolute path from output
    abs_pairs = [[url, Path(output).parent.absolute().joinpath(Path(fn))] for url, fn in pairs]

    # Download images from the url/filename pairs in a folder named "attachments"
    download_tuples(abs_pairs)

    # Compress images
    if COMPRESS:
        [compress_image(fn) for _, fn in abs_pairs]

    # Update links
    content = update_content(content, pairs)

    # Save to output
    open(output, "w").write(content)
