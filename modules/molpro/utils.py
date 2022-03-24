from typing import Optional
from typing import List
from typing import Iterator
from typing import Any
from typing import Dict
from typing import Union
from typing import Set

from molpro import OutputFormatError
from molpro import IterationTable


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


def process_columns(line: str, types: List[type] = [], delimiter: Optional[str] = None, expected_column_count: int = -1, format_exception: type =
                    OutputFormatError, remove_empty: bool = False) -> List[Any]:
    """Parses the given line by splitting it into different columns and optionally transforming each column to a given type"""
    columns = line.split() if delimiter is None else line.split(delimiter)

    if remove_empty:
        columns = [x for x in columns if x != ""]

    if expected_column_count >= 0 and len(columns) != expected_column_count:
        raise format_exception("Expected %d columns but got %d" % (
            expected_column_count, len(columns)))

    if len(types) > 0:
        if len(columns) != len(types):
            raise format_exception("Amount of types (%d) doesn't match with amount of columns (%d)" % (
                len(types), len(columns)))

        for i in range(len(columns)):
            if types[i] is float:
                # Make sure we convert from Fortran-style scientific notation to regular one
                columns[i] = columns[i].replace("D", "E")

            columns[i] = types[i](columns[i])

    return columns


def parse_iteration_table(lines: List[str], lineIt: Iterator[int], format_exception: type = OutputFormatError, col_sep: Optional[str] = None,
                          col_types: List[type] = [], substitutions: Dict[str, str] = {}, del_cols: Set[Union[int, str]] = set()) -> IterationTable:
    headerLine = lines[next(lineIt)]

    for currentSub in substitutions:
        headerLine = headerLine.replace(currentSub, substitutions[currentSub])

    headers = process_columns(
        headerLine, delimiter=col_sep, remove_empty=True, format_exception=format_exception)

    if len(headers) == 0:
        raise format_exception(
            "Can't parse iteration table for empty header line")
    if len(col_types) != 0 and len(headers) != len(col_types):
        raise format_exception("The amount of found column headers (%d) does not match the expected one (%d)" % (
            len(headers), len(col_types)))

    iterations = []

    for i in lineIt:
        if lines[i].strip() == "":
            break

        iterations.append(process_columns(lines[i], delimiter=col_sep, remove_empty=True, expected_column_count=len(headers),
                                          format_exception=format_exception, types=col_types))

    # Remove specified columns. First convert column header names into column indices though
    del_cols = {
        x if type(x) is int else headers.index(x) for x in del_cols}
    if any(not type(n) is int or n < 0 for n in del_cols):
        raise format_exception(
            "Encountered invalid column index or column header ID (specified for deletion)")

    headers = [v for i, v in enumerate(headers) if not i in del_cols]
    for i in range(len(iterations)):
        iterations[i] = [v for i, v in enumerate(iterations[i]) if not i in del_cols]


    table = IterationTable(columnHeaders=headers, iterations=iterations)

    return table
