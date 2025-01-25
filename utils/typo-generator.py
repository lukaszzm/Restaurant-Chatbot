import yaml
import random
import re

NLU_FILE_PATH = "<path-to-nlu.yml>"
NLU_FILE_OUTPUT_PATH = "<path-to-save-typos>"

adjacent_map = {
    'q': ['w', 'a'], 'w': ['q', 'e', 's'], 'e': ['w', 'r', 'd'], 'r': ['e', 't', 'f'],
    't': ['r', 'y', 'g'], 'y': ['t', 'u', 'h'], 'u': ['y', 'i', 'j'], 'i': ['u', 'o', 'k'],
    'o': ['i', 'p', 'l'], 'p': ['o'], 'a': ['q', 's', 'z'], 's': ['a', 'w', 'd', 'x'],
    'd': ['s', 'e', 'f', 'c'], 'f': ['d', 'r', 'g', 'v'], 'g': ['f', 't', 'h', 'b'],
    'h': ['g', 'y', 'j', 'n'], 'j': ['h', 'u', 'k', 'm'], 'k': ['j', 'i', 'l'], 'l': ['k', 'o'],
    'z': ['a', 's', 'x'], 'x': ['z', 's', 'd', 'c'], 'c': ['x', 'd', 'f', 'v'],
    'v': ['c', 'f', 'g', 'b'], 'b': ['v', 'g', 'h', 'n'], 'n': ['b', 'h', 'j', 'm'],
    'm': ['n', 'j', 'k']
}


def get_adjacent_chars(char):
    return adjacent_map.get(char.lower(), [])


def introduce_typo(text):
    if len(text) < 1:
        return text
    chars = list(text)
    pos = random.randint(0, len(chars) - 1)

    if not chars[pos].isalpha() or not chars[pos].isascii():
        return text

    typo_type = random.choice(['delete', 'insert', 'substitute', 'transpose'])

    try:
        if typo_type == 'delete':
            del chars[pos]
        elif typo_type == 'insert':
            adjacent = get_adjacent_chars(chars[pos])
            if adjacent:
                insert_char = random.choice(adjacent)
                if random.choice([True, False]):
                    chars.insert(pos, insert_char)
                else:
                    chars.insert(pos + 1, insert_char)
        elif typo_type == 'substitute':
            adjacent = get_adjacent_chars(chars[pos])
            if adjacent:
                replace_char = random.choice(adjacent)
                if chars[pos].isupper():
                    replace_char = replace_char.upper()
                chars[pos] = replace_char
        elif typo_type == 'transpose' and pos < len(chars) - 1:
            chars[pos], chars[pos + 1] = chars[pos + 1], chars[pos]
    except IndexError:
        pass

    return ''.join(chars)


def process_example(example):
    parts = re.split(r'(\[.*?]\(.*?\))', example)
    modified = []
    for part in parts:
        if re.match(r'\[.*?]\(.*?\)', part):
            modified.append(part)
        else:
            modified.append(introduce_typo(part))
    return ''.join(modified)


def process_file(input_file, output_file):
    with open(input_file, 'r') as f:
        data = yaml.safe_load(f)

    for intent in data['nlu']:
        original_examples = [
            line.strip()[2:]
            for line in intent['examples'].split('\n')
            if line.strip().startswith('-')
        ]

        new_examples = []
        for example in original_examples:
            new_examples.append(f"- {example}")
            modified = process_example(example)
            new_examples.append(f"- {modified}")

        intent['examples'] = '|\n    ' + '\n    '.join(new_examples)

    yaml.add_representer(str, lambda dumper, data: dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|'))

    with open(output_file, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


if __name__ == "__main__":
    process_file(NLU_FILE_PATH, NLU_FILE_OUTPUT_PATH)
