# Copyright 2023 Marcel Bollmann <marcel@bollmann.me>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import itertools as it
from lxml import etree
from typing import Callable, Optional
from xml.sax.saxutils import escape as xml_escape


def clean_whitespace(
    text: Optional[str], func: Optional[Callable[[str], str]] = None
) -> Optional[str]:
    if text is None:
        return text
    while "  " in text:
        text = text.replace("  ", " ")
    if func is not None:
        text = func(text)
    return text


def indent(elem: etree._Element, level: int = 0, internal: bool = False) -> None:
    """Enforce canonical indentation.

    "Canonical indentation" is two spaces, with each tag on a new line,
    except that 'author', 'editor', 'title', and 'booktitle' tags are
    placed on a single line.

    Arguments:
        elem: The XML element to apply canonical indentation to.
        level: Indentation level; used for recursive calls of this function.
        internal: If True, assume we are within a single-line element.

    Note:
        Adapted from [https://stackoverflow.com/a/33956544][].
    """
    # tags that have no internal linebreaks (including children)
    oneline = elem.tag in ("author", "editor", "speaker", "title", "booktitle", "variant")

    elem.text = clean_whitespace(elem.text, lambda x: x.lstrip())

    if len(elem):  # children
        # Set indent of first child for tags with no text
        if not oneline and (not elem.text or not elem.text.strip()):
            elem.text = "\n" + (level + 1) * "  "

        if not elem.tail or not elem.tail.strip():
            if level:
                elem.tail = "\n" + level * "  "
            else:
                elem.tail = "\n"

        # recurse
        for child in elem:
            indent(child, level + 1, internal=(internal or oneline))

        # Clean up the last child
        if oneline:
            child.tail = clean_whitespace(child.tail, lambda x: x.rstrip())
        elif not internal and (not child.tail or not child.tail.strip()):
            child.tail = "\n" + level * "  "
    else:
        elem.text = clean_whitespace(elem.text, lambda x: x.strip())

        if internal:
            elem.tail = clean_whitespace(elem.tail)
        elif not elem.tail or not elem.tail.strip():
            elem.tail = "\n" + level * "  "


def stringify_children(node: etree._Element) -> str:
    """
    Arguments:
        node: An XML element.

    Returns:
        The full content of the input node, including tags.

    Used for nodes that can have mixed text and HTML elements (like `<b>` and `<i>`).
    """
    return "".join(
        chunk
        for chunk in it.chain(
            (xml_escape_or_none(node.text),),
            it.chain(
                *(
                    (
                        etree.tostring(child, with_tail=False, encoding=str),
                        xml_escape_or_none(child.tail),
                    )
                    for child in node
                )
            ),
            (xml_escape_or_none(node.tail),),
        )
        if chunk
    ).strip()


def xml_escape_or_none(t: Optional[str]) -> Optional[str]:
    """Like [xml.sax.saxutils.escape][], but accepts [None][]."""
    return None if t is None else xml_escape(t)


def xsd_boolean(value: str) -> bool:
    """Converts an xsd:boolean value to a bool."""
    if value in ("0", "false"):
        return False
    elif value in ("1", "true"):
        return True
    raise ValueError(f"Not a valid xsd:boolean value: '{value}'")
