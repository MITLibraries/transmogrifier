from typing import List, Optional

from bs4 import Tag

from transmogrifier.sources.dspace_dim import DspaceDim


class WHOAS(DspaceDim):
    """WHOAS transformer class."""

    @classmethod
    def get_content_types(cls, dc_type_xml_element_list: Tag) -> List[Optional[str]]:
        """
        Get a list of content_type values from a list of dc.type elements from a WHOAS
        DSpace DIM record.

        Overrides the base DSpaceDim.get_content_types() method.

        Args:
            dc_type_xml_element_list: A list of BeautifulSoup Tags which each represent
            a single DIM dc.type element.
        """
        unaccepted_content_types = [
            "Article",
            "Authority List",
            "Book",
            "Book chapter",
            "Course",
            "Preprint",
            "Presentation",
            "Technical Report",
            "Thesis",
            "Working Paper",
        ]
        content_types = []
        for dc_type_xml_element in [t for t in dc_type_xml_element_list if t.string]:
            content_types.append(dc_type_xml_element.string)
        if all(item in unaccepted_content_types for item in content_types):
            return ["Unaccepted content_types"]
        else:
            return content_types
