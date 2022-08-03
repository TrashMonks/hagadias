"""Classes to represent population data from PopulationTables.xml."""
from typing import List

from lxml import etree as et
from lxml.etree import ElementBase


class QudPopList:
    def __init__(self, pop_elem: ElementBase):
        """Abstract class to represent a population item that has sub-nodes. In practice,
        this corresponds both to <population> and <group> nodes in PopulationTables.xml.

        Args:
            pop_elem: etree object which represents the population item.
        """
        self._items: List[QudPopItem] = []
        for item in pop_elem:
            if item.tag == "group":
                self._items.append(QudPopulationGroup(item))
            elif item.tag == "object":
                self._items.append(QudPopulationObject(item))
            elif item.tag == "table":
                self._items.append(QudPopulationTable(item))

    @property
    def children(self):
        return self._items


class QudPopItem:
    def __init__(self, pop_elem: ElementBase):
        """Abstract class to represent any item contained in a population. In practice,
        this corresponds to <group>, <table>, and <object> nodes in PopulationTables.xml,
        and loosely mirrors the game's own abstract class (PopulationItem) for representing these
        types of data.

        Args:
            pop_elem: etree object which represents the population item.
        """
        self.weight: int = int(pop_elem.attrib.get("Weight", 1))
        self.number: str = pop_elem.attrib.get("Number", "1")
        self.chance: str = pop_elem.attrib.get("Chance", "100")

    @property
    def displayname(self) -> str:
        raise NotImplementedError()  # to be implemented by inheriting subclasses

    @property
    def type(self) -> str:
        raise NotImplementedError()  # to be implemented by inheriting subclasses


class QudPopulation(QudPopList):
    def __init__(self, pop_elem: ElementBase):
        """Represents a single <population> node from PopulationTables.xml.

        Args:
            pop_elem: etree object which represents the <population> node from PopulationTables.xml
        """
        super().__init__(pop_elem)
        self.name: str = pop_elem.attrib.get("Name")
        self._xml: str = f'  {et.tostring(pop_elem, encoding="unicode", method="xml")}'
        self._depth: int | None = None
        # TODO: Standardize tabs / spaces, they print differently

    @property
    def xml(self) -> str:
        """The raw XML representation of this population from PopulationTables.xml."""
        return self._xml

    @property
    def style(self) -> str:
        """Style of the population or its main defining group ('pickone' or 'pickeach')"""
        if len(self.children) == 1 and self.children[0].type == "group":
            # noinspection PyUnresolvedReferences
            return self.children[0].style
        # the following return value based on advice from Armithaig, probably usually true?
        # https://discordapp.com/channels/214532333900922882/482714670860468234/902779863465865216
        return "pickeach"

    @property
    def depth(self) -> int:
        """The maximum nesting depth of this population. 1 represents a simple population table with
        no nested groups. 2 or higher represents additional levels of nested groups."""
        if self._depth is None:
            # Populations can have a single group beneath them that holds all items, or they can
            # hold items directly with no encapsulating group, so our logic accounts for that here -
            # both cases are considered only a single level of depth.
            if len(self.children) == 1 and self.children[0].type == "group":
                # noinspection PyTypeChecker
                self._depth = self._eval_depth(self.children[0])
            else:
                self._depth = self._eval_depth(self)
        return self._depth

    def _eval_depth(self, pop_group: QudPopList, cur_depth: int = 1) -> int:
        """Returns the maximum depth of the pop_group as an integer.

        Args:
            pop_group: A QudPopList item
            cur_depth: Current calculated population depth
        """
        max_depth = cur_depth
        for child in pop_group.children:
            if child.type == "group":
                # noinspection PyTypeChecker
                child_depth = self._eval_depth(child, cur_depth + 1)
                if child_depth > max_depth:
                    max_depth = child_depth
        return max_depth

    def get_effective_children(self) -> List[QudPopItem]:
        """Returns the main children of this population. If there is a single enclosing group that
        represents the entire population, returns that group's children instead of the direct
        children of the population node."""
        if len(self.children) == 1 and self.children[0].type == "group":
            # noinspection PyUnresolvedReferences
            return self.children[0].children
        return self.children


class QudPopulationObject(QudPopItem):
    def __init__(self, pop_elem: ElementBase):
        """Represents an <object> node from PopulationTables.xml.

        Args:
            pop_elem: etree object which represents the <object> node from PopulationTables.xml
        """
        super().__init__(pop_elem)
        self.blueprint: str = pop_elem.attrib.get("Blueprint", "")  # NOTE: can be an empty string

    @property
    def displayname(self) -> str:
        return self.blueprint

    @property
    def type(self) -> str:
        return "object"


class QudPopulationTable(QudPopItem):
    def __init__(self, pop_elem: ElementBase):
        """Represents a <table> node from PopulationTables.xml.

        Args:
            pop_elem: etree object which represents the <table> node from PopulationTables.xml
        """
        super().__init__(pop_elem)
        self.name: str = pop_elem.attrib.get("Name", "")  # NOTE: can be "Nothing"

    @property
    def displayname(self) -> str:
        return self.name

    @property
    def type(self) -> str:
        return "table"


class QudPopulationGroup(QudPopList, QudPopItem):
    def __init__(self, pop_elem: ElementBase):
        """Represents a <group> node from PopulationTables.xml.

        Args:
            pop_elem: etree object which represents the <group> node from PopulationTables.xml
        """
        QudPopItem.__init__(self, pop_elem)
        QudPopList.__init__(self, pop_elem)
        self.name: str = pop_elem.attrib.get("Name", "unnamed")  # NOTE: used for mods/merge only
        self.style: str = pop_elem.attrib.get("Style", "")  # NOTE: always 'pickeach' or 'pickone'

    @property
    def displayname(self) -> str:
        return self.name

    @property
    def type(self) -> str:
        return "group"
