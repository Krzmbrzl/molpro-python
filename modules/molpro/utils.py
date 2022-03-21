from typing import Optional
from typing import List
from typing import Iterator
from typing import Any

from molpro import OutputFormatError


def consume(content: str, prefix: str = "", gobble_until: Optional[str] = None, gobble_from: Optional[str] = None, gobble_after: Optional[str] = None, strip=False,
            optional_ops: List[str] = [], format_exception: type = OutputFormatError, case_sensitive: bool = True) -> str:
    """Consumes the given content by matching and removing the given patterns from it. Returns the remaining part of content. If the given patterns
    don't match the given String, an error of type format_exception is risen"""
    if not case_sensitive:
        def transform(x): return x.lower()
    else:
        def transform(x): return x

    if transform(content).startswith(transform(prefix)):
        # Strip away the prefix
        content = content[len(prefix):]
    elif not "prefix" in optional_ops:
        raise format_exception(
            "Assumed content to start with \"" + prefix + "\"")

    if not gobble_until is None:
        index = transform(content).find(transform(gobble_until))

        if index >= 0:
            content = content[index + len(gobble_until):]
        elif not "gobble_until" in optional_ops:
            raise format_exception("Attempted to gobble until \"" +
                                   gobble_until + "\", but could not find this substring")

    if not gobble_from is None:
        index = transform(content).find(transform(gobble_from))

        if index >= 0:
            content = content[: index]
        elif not "gobble_from" in optional_ops:
            raise format_exception("Attempted to gobble from \"" +
                                   gobble_from + "\", but could not find this substring")

    if not gobble_after is None:
        index = transform(content).find(transform(gobble_after))

        if index >= 0:
            content = content[: index + len(gobble_after)]
        elif not "gobble_after" in optional_ops:
            raise format_exception("Attempted to gobble after \"" +
                                   gobble_after + "\", but could not find this substring")

    return content if not strip else content.strip()


def skip_to(content_list: List[str], indexIt: Iterator[int], contains: Optional[str] = None, startswith: Optional[str] = None, endswith: Optional[str]
            = None, default: Optional[int] = None, case_sensitive: bool = True) -> int:
    """Proceeds the given iterator until the last index emitted by it, references an entry in content_list that matches the provided criterion.
    Returns the found index. Note that the iterator will return the index AFTER the found one, when stepped after this function has been called"""
    if not case_sensitive:
        def transform(x): return x.lower()
    else:
        def transform(x): return x

    for i in indexIt:
        found_content = True

        if found_content and not contains is None:
            found_content = found_content and transform(
                contains) in transform(content_list[i])
        if found_content and not startswith is None:
            found_content = found_content and transform(content_list[i]).startswith(
                transform(startswith))
        if found_content and not endswith is None:
            found_content = found_content and transform(content_list[i]).endswith(
                transform(endswith))

        if found_content:
            return i

    if default is None:
        raise StopIteration()
    else:
        return default


def iterate_to(it: Iterator[Any], to: Any):
    while next(it) != to:
        pass
