from __future__ import annotations

import argparse
import re
from typing import Sequence


def _fix_file(filename):
    with open(filename, mode='rb') as fp:
        content = fp.read().decode()

    try:
        indexes = get_brace_indexes(content, filename)
    except ValueError as e:
        raise ValueError(f'Error found in {filename} {e}')

    block_map = ignore_specific_blocks(get_block_map_from_indexes(content, indexes))

    original_content = content
    content = update_content(content, block_map)

    if content != original_content:
        with open(filename, mode='wb') as fp:
            fp.write(content.encode())
            return 1

    return 0


def get_brace_indexes(content, filename) -> list:
    indexes = []
    end_by_depth = {}
    depth = 0
    for i, c in enumerate(reversed(content)):
        if c == '}':
            end_by_depth[depth] = len(content) - i - 1
            depth += 1
        elif c == '{':
            depth -= 1
            end = end_by_depth.get(depth)
            if end is None:
                raise ValueError(f'unbalanced parens near {content[i-100:i+100]} in {filename}')
            del end_by_depth[depth]
            indexes.append(
                (
                    len(content) - i - 1,
                    end,
                )
            )
    return sorted(indexes)


def get_block_map_from_indexes(content, indexes: list[tuple]):
    # Build a map of braces indexes and use that to determine block type.
    block_map = {k: '' for k in indexes}
    for key in block_map:
        # read backwards until we find a key word
        i = key[0]  # Opening brace position
        seen_right_paren = False
        while i > 0:
            if re.match(r'\s+class\s+', content[i - 7:i]):
                block_map[key] = 'CLASS'
                break
            elif re.match(r'\s+while\s+', content[i - 7:i]):
                block_map[key] = 'WHILE'
                break
            elif re.match(r'\s+catch\s+', content[i - 7:i]):
                block_map[key] = 'CATCH'
                break
            elif re.match(r'\s+finally\s+', content[i - 9:i]):
                block_map[key] = 'FINALLY'
                break
            elif re.match(r'\s+switch\s+', content[i - 8:i]):
                block_map[key] = 'SWITCH'
                break
            elif re.match(r'\s+for\s+', content[i - 5:i]):
                block_map[key] = 'FOR'
                break
            elif re.match(r'\s+try\s+', content[i - 5:i]):
                block_map[key] = 'TRY'
                break
            elif re.match(r'\s+if\s+', content[i - 4:i]):
                block_map[key] = 'IF'
                break
            elif re.match(r'new ', content[i - 4:i]):
                block_map[key] = 'ARRAY'
                break
            elif not seen_right_paren and re.match(r'\s+=\s+', content[i - 3:i]):
                block_map[key] = 'EQ'
                break
            elif content[i - 1:i] == ')':
                seen_right_paren = True
            elif seen_right_paren and found_method_visibiltiy_before_new_line(content, i):
                block_map[key] = 'METHOD'
                break

            i -= 1

    return block_map


def ignore_specific_blocks(block_map):
    # Ignore some block types
    ignored = (
        'IF',
        'EQ',
        'TRY',
        'CATCH',
        'FINALLY',
        'ARRAY',
    )
    return {k: v for k, v in block_map.items() if v not in ignored}


def update_content(content, block_map):
    while block_map:
        keys = sorted(block_map.keys())
        key = keys.pop(0)
        value = block_map[key]
        del block_map[key]

        start_brace_index, end_brace_index = key

        if read_forwards_for_comment(content, end_brace_index):
            continue

        pre_len = len(content)
        if value == 'CLASS':
            content = handle_class(content, start_brace_index, end_brace_index)
        elif value == 'METHOD':
            content = handle_method(content, start_brace_index, end_brace_index)
        elif value == 'FOR':
            content = handle_for(content, end_brace_index)
        elif value == 'WHILE':
            content = handle_while(content, end_brace_index)
        elif value == 'SWITCH':
            content = handle_switch(content, end_brace_index)

        block_map = rebuild_block_map(block_map, end_brace_index, len(content) - pre_len)

    return content


def rebuild_block_map(block_map, end_brace_index, increase) -> dict:
    new = {}
    for (start, stop), block in block_map.items():
        if start >= end_brace_index:
            start += increase
        if stop >= end_brace_index:
            stop += increase

        new[(start, stop)] = block

    return new


def handle_class(content, start_brace_index, end_brace_index):
    # read back from starting brace until you have a full token
    class_name = read_backwards_for_token(content, start_brace_index, stop_by_tokens=('class',))

    # check if class_name is after second index
    comment = f' // end class {class_name}'
    if not content[end_brace_index:].startswith(comment):
        content = content[:end_brace_index + 1] + comment + content[end_brace_index + 1:]

    return content


def handle_method(content, start_brace_index, end_brace_index):
    # read back from starting brace until you have a full token
    method_name = read_backwards_for_name_before_parens(
        content,
        start_brace_index,
    )

    # check if name is after second index
    comment = f' // end {method_name}()'
    if not content[end_brace_index:].startswith(comment):
        content = content[:end_brace_index + 1] + comment + content[end_brace_index + 1:]

    return content


def handle_for(content, end_brace_index):
    # check if name is after second index
    comment = f' // end for'
    if not content[end_brace_index:].startswith(comment):
        content = content[:end_brace_index + 1] + comment + content[end_brace_index + 1:]

    return content


def handle_while(content, end_brace_index):
    # check if name is after second index
    comment = f' // end while'
    if not content[end_brace_index:].startswith(comment):
        content = content[:end_brace_index + 1] + comment + content[end_brace_index + 1:]

    return content


def handle_switch(content, end_brace_index):
    # check if name is after second index
    comment = f' // end switch'
    if content[end_brace_index+1:].strip().startswith(";"):
        # Account for semi-colon.
        content = content[:end_brace_index + 2] + comment + content[end_brace_index + 2:]
    else:
        content = content[:end_brace_index + 1] + comment + content[end_brace_index + 1:]

    return content


def found_method_visibiltiy_before_new_line(content, i) -> bool:
    line_start = i
    while line_start > 0:
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


def read_backwards_for_name_before_parens(content, start_pos) -> str:
    # Read backwards until you find a stop by token.
    depth = None
    i = start_pos
    while i > 0 and (depth is None or depth):
        i -= 1
        if content[i] == ')':
            if depth is None:
                depth = 0
            depth += 1
        elif content[i] == '(':
            if depth is None:
                continue
            depth -= 1

    chars = []
    capturing = False
    while True:
        if re.match(r'\s', content[i]) and capturing:
            break
        elif re.match(r'\w', content[i]) and not capturing:
            capturing = True

        if capturing:
            chars.append(content[i])

        i -= 1

    return ''.join(reversed(chars)).strip()


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
