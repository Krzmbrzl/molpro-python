from typing import Optional
from typing import List

from molpro import OutputFormatError


def consume(content: str, prefix: str = "", gobble_until: Optional[str] = None, gobble_from: Optional[str] = None, gobble_after: Optional[str] = None, strip=False,
        format_exception: type = OutputFormatError) -> str:
    if not content.startswith(prefix):
        raise format_exception(
            "Assumed content to start with \"" + prefix + "\"")

    # Strip away the prefix
    content = content[len(prefix):]

    if not gobble_until is None:
        index = content.find(gobble_until)

        if index < 0:
            raise format_exception("Attempted to gobble until \"" +
                                   gobble_until + "\", but could not find this substring")

        content = content[index + len(gobble_until):]

    if not gobble_from is None:
        index = content.find(gobble_from)

        if index < 0:
            raise format_exception("Attempted to gobble from \"" +
                                   gobble_from + "\", but could not find this substring")

        content = content[: index]

    if not gobble_after is None:
        index = content.find(gobble_after)

        if index < 0:
            raise format_exception("Attempted to gobble after \"" +
                                   gobble_after + "\", but could not find this substring")

        content = content[: index + len(gobble_after)]

    return content if not strip else content.strip()


def skip_to(content_list: List[str], index: int, contains: Optional[str] = None, startswith: Optional[str] = None, endswith: Optional[str] = None) -> int:
    for i in range(index, len(content_list)):
        found_content = True

        if found_content and not contains is None:
            found_content = found_content and contains in content_list[i]
        if found_content and not startswith is None:
            found_content = found_content and content_list[i].startswith(
                startswith)
        if found_content and not endswith is None:
            found_content = found_content and content_list[i].endswith(
                endswith)

        if found_content:
            return i

    return len(content_list)


