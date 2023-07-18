import logging
from typing import Optional

from bs4 import Tag

from transmogrifier.sources.springshare import SpringshareOaiDc

logger = logging.getLogger(__name__)


class Libguides(SpringshareOaiDc):
    """Libguides transformer."""

    def get_optional_fields(self, xml: Tag) -> Optional[dict]:
        """
        Retrieve optional TIMDEX fields from a Libguides OAI DC XML record, leaning
        heavily (if not entirely) on the shared fields as extracted by the
        SpringshareOaiDc transformer.

        Overrides metaclass get_optional_fields() method.

        Args:
            xml: A BeautifulSoup Tag representing a single Libguides OAI DC XML record
        """

        return self.get_shared_optional_fields(xml)
