"""Store helper functions related to iterable data structures."""

# Is "Sequence" appropriate as a generic iterable?
from typing import Any, Dict, Sequence

# Use when prompting the user to select, through Discord reactions,
# an element from an iterable by index.
DIGIT_EMOJIS = ['0️⃣', '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣']


def iter_to_numbered_list(iter_: Sequence) -> str:
    """Return an iterable as a user-readable numbered list."""
    output = ''

    for index, value in enumerate(iter_):
        output += f'**{index + 1}.** {value}\n'

    return output


def format_dict(dict_: Dict[Any, Any]) -> str:
    """Return a user-readable view of a dictionary."""
    output = ''

    for key, value in dict_.items():
        output += f'\n• {key}: {value}'

    return output


def format_iter(iter_: Sequence, connector: str = 'and', end: str = '.') -> str:
    """Return a user-readable view of an iterable."""
    output = (f' {connector} '
              ).join([', '.join(iter_[:-1]), iter_[-1]] if len(iter_) > 2 else iter_)

    return output + end
