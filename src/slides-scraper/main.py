import re
import os
import sys

from typing import Any
from urllib.parse import urlparse
from urllib.request import urlretrieve
from pathlib import Path
from PIL import Image

"""
Usage:
    Call with python main.py <path-to-input-file> <path-to-output-file>

    Only partially tested
"""

input = sys.argv[1]
output = sys.argv[2]

COMPRESS = True  # Not implemented
COMP_TRESHOLD = 1048576  # 1MB
QUALITY = 90
MAX_RESOLUTION = [1920, 1080]
IGNORE_COMPRESSED_FORMATS = ['.webm']
FOLDER = "attachments/"
FALLBACK_EXT = 'jpg'


def get_unsplash_filetype(url: str) -> str:
    try:
        return re.findall(r'fm=(\w+)', url)[0]
    except IndexError:
        return ''


def get_filename(url: str, folder: str = FOLDER, def_ext: str = FALLBACK_EXT) -> str:
    p = Path(urlparse(url).path)

    # Giphy gifs
    for name, ext in re.findall(r'giphy\.com/media/(.+)/[^.]+(.+)$', url):
        return f'{folder}{name}{ext}'

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
    if os.stat(fn).st_size < max_size or \
       Path(fn).suffix in IGNORE_COMPRESSED_FORMATS:
        return

    img = Image.open(fn)
    if Path(fn).suffix == '.gif':
        print('Unable to compress gifs (yet)')
        return

    if list(img.size) > MAX_RESOLUTION:
        # Resize large images
        f_x, f_y = img.size[0] / MAX_RESOLUTION[0], img.size[1] / MAX_RESOLUTION[1]
        f = f_x if f_x > f_y else f_y
        img = img.resize((int(img.size[0]/f), int(img.size[1]/f)), Image.Resampling.LANCZOS)

    # Save compressed image
    img.save(fn, quality=QUALITY, optimize=True, format='webp')


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
