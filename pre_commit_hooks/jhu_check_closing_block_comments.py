from __future__ import annotations

import argparse
import re
from typing import Sequence


def _fix_file(filename):
    with open(filename, mode='rb') as fp:
        content = fp.read().decode()

    try:
        depth_map = get_depth_map(content)
    except ValueError as e:
        raise ValueError(f'Error found in {filename} {e}')

    block_map = get_block_map_from_depth_map(content, depth_map)

    original_content = content
    content = update_content(content, block_map)

    if content != original_content:
        with open(filename, mode='wb') as fp:
            fp.write(content.encode())
            return 1

    return 0

def get_depth_map(content):
    depth_map = {}
    depth = 0
    for i, c in enumerate(reversed(content)):
        if c == '}':
            depth_map[depth] = {'end': i}
            depth += 1
        if c == '{':
            depth -= 1
            rev_index_map = depth_map.get(depth)
            if rev_index_map is None:
                raise ValueError('unbalanced braces')
            rev_index_map['start'] = i
    return depth_map


def get_block_map_from_depth_map(content, depth_map):
    # Build a map of braces indexes and use that to determine block type.
    block_map = {}
    for rev_index_map in depth_map.values():
        block_map[
            (
                len(content) - rev_index_map['start'],
                len(content) - rev_index_map['end']
            )
        ] = None

    for key in block_map:
        # read backwards until we find a key word
        i = key[0]
        could_be_method = False
        while i > 0:
            if re.match(r'\s+class\s+', content[i - 7:i]):
                block_map[key] = 'CLASS'
                break
            elif re.match(r'\s+while\s+', content[i - 7:i]):
                block_map[key] = 'WHILE'
                break
            elif re.match(r'\s+switch\s+', content[i - 7:i]):
                block_map[key] = 'SWITCH'
                break
            elif re.match(r'\s+for\s+', content[i - 5:i]):
                block_map[key] = 'FOR'
                break
            elif re.match(r'\s+if\s+', content[i - 4:i]):
                block_map[key] = 'IF'
                break
            elif re.match(r'\s+=\s+', content[i - 3:i]):
                block_map[key] = 'EQ'
                break
            elif content[i - 1:i] == ')':
                could_be_method = True
            elif could_be_method and found_method_visibiltiy_before_new_line(content, i):
                block_map[key] = 'METHOD'
                break

            i -= 1

    # Ignore some block types
    ignored = (
        'IF',
        'EQ',
    )
    block_map = {k: v for k, v in block_map.items() if v not in ignored}

    return block_map


def update_content(content, block_map):
    while block_map:
        keys = sorted(block_map.keys())
        key = keys.pop(0)
        value = block_map[key]
        del block_map[key]

        start_brace_index, end_brace_index = key

        if read_forwards_for_comment(content, end_brace_index):
            continue

        increase = 0
        if value == 'CLASS':
            pre_len = len(content)
            content = handle_class(content, start_brace_index, end_brace_index)
            increase = len(content) - pre_len

        block_map = rebuild_block_map(block_map, end_brace_index, increase)

    return content


def rebuild_block_map(block_map, end_brace_index, increase) -> dict:
    new = {}
    for start, stop in block_map.keys():
        if stop > end_brace_index:
            new_stop = end_brace_index + increase
            new[(start, new_stop)] = block_map.get((start, stop))
        else:
            new[(start, stop)] = block_map.get((start, stop))

    return new


def handle_class(content, start_brace_index, end_brace_index):
    # read back from starting brace until you have a full token
    class_name = read_backwards_for_token(content, start_brace_index, stop_by_tokens=('class',))

    # check if class_name is after second index
    comment = f' // end class {class_name}'
    if not content[end_brace_index:].startswith(comment):
        content = content[:end_brace_index] + comment + content[end_brace_index:]

    return content

def found_method_visibiltiy_before_new_line(content, i) -> bool:
    line_start = i
    while line_start >= 0:
        line_start -= 1
        if content[line_start] == '\n':
            break

    for vis_word in ('public', 'protected', 'private'):
        if vis_word in content[line_start: i]:
            return True

    return False


def read_forwards_for_comment(content, end_brace_index) -> int:
    """
    Return offset from end_brace_index of the location of a comment. Return
    zero if no comment was found.
    """
    i = end_brace_index
    while True:
        if content[i:i+2] == '//':
            return i
        elif content[i] == '\n':
            return 0

        i += 1


def read_backwards_for_token(content, start_pos, stop_by_tokens=()) -> str:
    # Read backwards until you find a stop by token.
    found_start = False
    i = start_pos
    while i > 0 and not found_start:
        i -= 1
        for token in stop_by_tokens:
            if content[i - len(token):i] == token:
                found_start = True
                break

    # Skip space after stop by token.
    i += 1

    # Read forwards for one token.
    chars = []
    while not re.match(r'\s', content[i]):
        chars.append(content[i])
        i += 1

    return ''.join(chars).strip()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='*', help='Filenames to fix')
    args = parser.parse_args(argv)

    return_code = 0
    for filename in args.filenames:
        if _fix_file(filename):
            print(f'Fixing {filename}')
            return_code = 1
    return return_code


if __name__ == '__main__':
    raise SystemExit(main())
