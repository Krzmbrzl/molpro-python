from typing import Optional
from typing import List
from typing import Iterator
from typing import Any
from typing import Dict
from typing import Union
from typing import Set
from typing import Tuple
from typing import Type

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


def get_count(types: Any) -> int:
    try:
        return len(types)
    except TypeError:
        return 1


def process_columns(line: str, types: List[List[Union[Type, Tuple[Type]]]] = [], delimiter: Optional[str] = None, format_exception: Type =
                    OutputFormatError, remove_empty: bool = False) -> List[Any]:
    """Parses the given line by splitting it into different columns and optionally transforming each column to a given type"""
    columns = line.split() if delimiter is None else line.split(delimiter)

    if remove_empty:
        columns = [x for x in columns if x != ""]

    if len(types) > 0:
        col_counts = []
        for option in types:
            counter = 0
            for currentType in option:
                if not currentType is None:
                    counter += get_count(currentType)

            col_counts.append(counter)

        if not len(col_counts) == len(set(col_counts)):
            raise RuntimeError(
                "Can only have optional types, if the column count is still unique")

        try:
            type_idx = col_counts.index(len(columns))
        except ValueError:
            raise format_exception("Amount of types (%s) doesn't match with amount of columns (%d)" % (
                str(col_counts), len(columns)))

        convertedColumns = []

        i = 0
        colOffset = 0
        while i < len(types[type_idx]):
            currentType = types[type_idx][i]

            if currentType is None:
                convertedColumns.append(None)
                i += 1
                colOffset -= 1
                continue

            if currentType is float:
                # Make sure we convert from Fortran-style scientific notation to regular one
                columns[i + colOffset] = columns[i + colOffset].replace("D", "E")

            if isinstance(currentType, type):
                convertedColumns.append(currentType(columns[i + colOffset]))
            else:
                # Composite types, e.g. (str, int)
                tmp = []
                for j in range(len(currentType)):
                    tmp.append(currentType[j](columns[i + colOffset + j]))

                    if i + j == len(columns):
                        raise format_exception(
                            "Size of composite type exceeded column count")

                colOffset += len(currentType) - 1

                convertedColumns.append(tuple(tmp))

            i += 1

        columns = convertedColumns

    return columns


def parse_iteration_table(lines: List[str], lineIt: Iterator[int], format_exception: type = OutputFormatError, col_sep: Optional[str] = None,
                          col_types: List[List[Union[Type, Tuple[Type]]]] = [], substitutions: Dict[str, str] = {},
                          del_cols: Set[Union[int, str]] = set()) -> IterationTable:
    headerLine = lines[next(lineIt)]

    for currentSub in substitutions:
        headerLine = headerLine.replace(currentSub, substitutions[currentSub])

    headers = process_columns(
        headerLine, delimiter=col_sep, remove_empty=True, format_exception=format_exception)

    # Only count non-None types
    col_counts = [sum(1 for y in x if y) for x in col_types]

    if len(headers) == 0:
        raise format_exception(
            "Can't parse iteration table for empty header line")
    if len(col_types) != 0 and not len(headers) in col_counts:
        raise format_exception("The amount of found column headers (%d) does not match the expected one (%s)" % (
            len(headers), str(col_counts)))

    iterations = []

    for i in lineIt:
        if lines[i].strip() == "":
            break

        iterations.append(process_columns(
            lines[i], delimiter=col_sep, remove_empty=True, format_exception=format_exception, types=col_types))

    # Remove specified columns. First convert column header names into column indices though
    try:
        del_cols = {
            x if type(x) is int else headers.index(x) for x in del_cols}
    except ValueError as e:
        raise format_exception(
            "Encountered invalid column index or column header ID (specified for deletion): %s" % e)

    headers = [v for i, v in enumerate(headers) if not i in del_cols]

    for i in range(len(iterations)):
        iterations[i] = [v for i, v in enumerate(
            iterations[i]) if not i in del_cols]

    table = IterationTable(columnHeaders=headers, iterations=iterations)

    return table
