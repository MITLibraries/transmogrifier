import logging
import os

from bs4 import Tag  # type: ignore[import-untyped]

from transmogrifier.sources.xmltransformer import XMLTransformer

logger = logging.getLogger(__name__)

# DEBUG: shim to use env var to get parsing approach
PARSER = os.getenv("PARSER", "bs4")

SIMULATE_NUM = 50


class MarcV2(XMLTransformer):
    """Marc transformer."""

    # DEBUG: REQUIRED
    @classmethod
    def get_main_titles(cls, source_record: Tag) -> list[str]:
        """
        Arbitrary field method to simulate lots of realistic data parsing via BS4 or lxml.

        For each, a `for x in range(0, 50)` is added to simulate other field methods
        parsing data from the record.  This is probably a high number, maybe a typical
        record only has 20-30 calls for data, but it exposes the difference between BS4
        and lxml.

        The final result is a technically valid record with a title pulled.
        """
        if PARSER == "bs4":
            subfield = None
            for x in range(0, SIMULATE_NUM):
                try:
                    element = source_record.find("datafield", tag="245")
                    for subfield in element.find_all(name=True, string=True):
                        if subfield.get("code", "") == "a":
                            break
                except AttributeError:
                    logger.exception(
                        "Record ID %s is missing a 245 field",
                        cls.get_source_record_id(source_record),
                    )
                    return []

            if subfield is not None:
                return [str(subfield.string)]
            else:
                return []

        elif PARSER == "lxml":

            # DEBUG ##############################
            # DEBUG: XPath: slow
            # NOTE: this demonstrates using lxml.element.xpath, and is 7-8x times slower
            #  than using element.iter()
            # DEBUG ##############################
            # for x in range(0, SIMULATE_NUM):
            #     e = source_record.xpath("//datafield[@tag=245]/subfield[@code='a']")[0]
            # return [e.text]

            # DEBUG ##############################
            # DEBUG: element.iter: fast
            # DEBUG ##############################
            # e = None
            # for x in range(0, SIMULATE_NUM):
            #     for element in source_record.iter("datafield"):
            #         if element.attrib.get("tag") == "245":
            #             for subfield in element.iter("subfield"):
            #                 if subfield.attrib.get("code") == "a":
            #                     e = subfield
            #                     break
            # if e is not None:
            #     return [e.text]
            # else:
            #     return []

            # DEBUG ##############################
            # DEBUG: find: slow (uses XPath)
            # NOTE: this demonstrates using lxml.element.find, which is quite fast
            # NOTE: while it looks like XPath, it's not the full implementation, so can
            #  be somewhat tricky to use; unsure what exactly is supported
            #  https://docs.python.org/2/library/xml.etree.elementtree.html#elementtree-xpath
            # DEBUG ##############################
            e = None
            for x in range(0, SIMULATE_NUM):
                e = source_record.find(".//datafield[@tag='245']/subfield[@code='a']")
            if e is not None:
                return [e.text]
            else:
                return []

    @classmethod
    def get_source_record_id(cls, source_record: Tag) -> str:
        """
        Get the source record ID from a MARC XML record.

        Overrides metaclass get_source_record_id() method.

        Args:
            source_record: A BeautifulSoup Tag representing a single MARC XML record.
        """

        if PARSER == "bs4":
            return str(source_record.find("controlfield", tag="001", string=True).string)

        elif PARSER == "lxml":
            return source_record.xpath("//controlfield[@tag=001]")[0].text

    @classmethod
    def record_is_deleted(cls, source_record: Tag) -> bool:
        """
        Determine whether record has a status of deleted.

        Overrides metaclass record_is_deleted() method.

        Args:
            source_record: A BeautifulSoup Tag representing a single MARC XML record
        """
        if PARSER == "bs4":
            if leader := source_record.find("leader", string=True):  # noqa: SIM102
                if leader.string[5:6] == "d":
                    return True
            return False

        elif PARSER == "lxml":
            if source_record.xpath("//leader")[0].text[5:6] == "d":
                return True
            return False
