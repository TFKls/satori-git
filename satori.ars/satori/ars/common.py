# vim:ts=4:sts=4:sw=4:expandtab
"""Common functionality for ARS providers.
"""

from blist import sortedset

from satori.objects import Argument, DispatchOn
from satori.ars.model import ArsElement, ArsList, ArsMap, ArsSet, ArsTypeAlias
from satori.ars.model import ArsField, ArsStructure, ArsProcedure, ArsService
from satori.ars.api import Writer


class TopologicalWriter(Writer):
    """Abstract. A base for Writers which process the elements in topological order.
    """

    def __init__(self):
        pass

    def _write(self, item, target):
        """Abstract. Write a single Element to the target file.

        Implementations can assume that all referenced Elements have already been written.
        """
        raise NotImplementedError()

    @DispatchOn(item=ArsElement)
    def _dependencies(self, item):
        return []

    @DispatchOn(item=(ArsList, ArsSet))
    def _dependencies(self, item):
        yield item.element_type

    @DispatchOn(item=ArsMap)
    def _dependencies(self, item):
        yield item.key_type
        yield item.value_type

    @DispatchOn(item=ArsTypeAlias)
    def _dependencies(self, item):
        yield item.target_type

    @DispatchOn(item=ArsField)
    def _dependencies(self, item):
        yield item.type

    @DispatchOn(item=ArsStructure)
    def _dependencies(self, item):
        for field in item.fields:
            yield field

    @DispatchOn(item=ArsProcedure)
    def _dependencies(self, item):
        yield item.return_type
        for parameter in item.parameters:
            yield parameter
        for exception_type in item.exception_types:
            yield exception_type

    @DispatchOn(item=ArsService)
    def _dependencies(self, item):
        for procedure in item.procedures:
            yield procedure

    def write_to(self, services, target):
        done = set()
        def _recwrite(item):
            if item in done:
                return
            done.add(item)
            for dependency in self._dependencies(item):
                _recwrite(dependency)
            self._write(item, target)
        for service in services:
            _recwrite(service)

class TopologicalSortedWriter(TopologicalWriter):
    """Abstract. A base for Writers which process the elements in topological order.
    """

    def __init__(self):
        pass

    def _sortkey(self, item):
        """Abstract. Write a single Element to the target file.

        Implementations can assume that all referenced Elements have already been written.
        """
        raise NotImplementedError()

    def write_to(self, contracts, target):
        ready = sortedset()
        deps = dict()
        fol = dict()

        def _recfind(item):
            if item in deps:
            	return
            d = list(self._dependencies(item))
            deps[item] = len(d)
            fol[item] = []
            if deps[item] == 0:
            	ready.add((self._sortkey(item), item,))
            for dependency in d:
            	_recfind(dependency)
            	fol[dependency].append(item)

        for contract in contracts:
        	_recfind(contract)

        while len(ready) > 0:
        	item = ready.pop(0)[1]
        	self._write(item, target)
        	for f in fol[item]:
        		deps[f] = deps[f] - 1
                if deps[f] == 0:
                	ready.add((self._sortkey(f), f,))

