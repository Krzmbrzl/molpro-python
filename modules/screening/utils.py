from typing import Dict
from typing import Union
from typing import List
from typing import Any
from typing import Optional

from screening import Extensions


def combine(lhs: Union[List[Dict[str, Any]], List[Any]], rhs: Union[List[Dict[str, Any]], List[Any]]) -> List[Any]:
    """Combines the list of entries given as lhs with the ones given as rhs in such a way, that there
    will be a new entity for every entry in lhs that is extended by the n-th entry in rhs.
    E.g. lhs = [[A], [B]], rhs = [[C,D], [E]] -> [[A,C,D], [B,C,D], [A,E], [B,E]]"""
    results = []
    if len(lhs) == 0:
        return rhs
    if len(rhs) == 0:
        return lhs

    for source in lhs:
        for extend in rhs:
            copy = source.copy()

            # Add the entries from extend into copy
            if isinstance(copy, dict):
                assert isinstance(extend, dict)
                for key in extend:
                    if key in copy:
                        raise RuntimeError(
                            "Encountered duplicate key \"%s\"" % key)
                    copy[key] = extend[key]
            else:
                # We assume that copy and extend are either lists or sets
                for entry in extend:
                    if entry in copy:
                        raise RuntimeError(
                            "Encountered duplicate key \"%s\"" % entry)
                    if isinstance(copy, set):
                        copy.add(entry)
                    else:
                        copy.append(entry)

            results.append(copy)

    return results


def format(content: str, substitutions: Dict[str, Any]) -> str:
    """Formats the given content by performing the requested substitutions"""
    for currentKey in substitutions:
        content = content.replace(
            "%" + currentKey + "%", str(substitutions[currentKey]))

    return content


def __process_param(keyName: str, value: Any, substitutions: Dict[str, Any]):
    if keyName in substitutions:
        raise RuntimeError("Wanted to add extr parameter \"%s=%s\" but this key is already associated with a value: \"%s\"" % (keyName,
                                                                                                                               str(value), substitutions[keyName]))

    substitutions[keyName] = value


def add_extra_substitutions(substitutions: Dict[str, Any], extensions: Optional[Extensions] = None, extra: Optional[Dict[str, Any]] = None):
    if not extensions is None:
        runtime = extensions.estimate_runtime(substitutions)
        memory = extensions.estimate_memory(substitutions)
        disk_space = extensions.estimate_disk_space(substitutions)

        if not runtime is None:
            __process_param("runtime", runtime, substitutions)
        if not memory is None:
            __process_param("memory", memory, substitutions)
        if not disk_space is None:
            __process_param("disk_space", disk_space, substitutions)

    if not extra is None:
        for key in extra:
            __process_param(key, extra[key], substitutions)
