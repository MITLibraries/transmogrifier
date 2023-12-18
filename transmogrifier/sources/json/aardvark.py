import logging

import transmogrifier.models as timdex
from transmogrifier.sources.transformer import JsonTransformer

logger = logging.getLogger(__name__)


class MITAardvark(JsonTransformer):
    """MITAardvark transformer.

    MIT Aardvark records have more required fields than standard Aardvark records
    as detailed here in the geo-harvester's MITAardvark class:

    https://github.com/MITLibraries/geo-harvester/blob/main/harvester/records/record.py
    """

    @classmethod
    def get_main_titles(cls, source_record: dict) -> list[str]:
        """
        Retrieve main title(s) from a MITAardvark JSON record.

        Overrides metaclass get_main_titles() method.

        Args:
            source_record: A JSON object representing a source record.
        """
        return [source_record["dct_title_s"]]

    @classmethod
    def get_source_record_id(cls, source_record: dict) -> str:
        """
        Get source record ID from a JSON record.

        Args:
            source_record: A JSON object representing a source record.
        """
        return source_record["id"]

    @classmethod
    def record_is_deleted(cls, source_record: dict) -> bool:
        """
        Determine whether record has a status of deleted.

        ## WIP - defining to enable instantiation of MITAardvark instance.

        Args:
            source_record: A JSON object representing a source record.
        """
        return False

    def get_optional_fields(self, source_record: dict) -> dict | None:
        """
        Retrieve optional TIMDEX fields from a Aardvar JSON record.

        Overrides metaclass get_optional_fields() method.

        Args:
            xml: A BeautifulSoup Tag representing a single Datacite record in
                oai_datacite XML.
        """
        fields: dict = {}

        # alternate_titles

        # content_type
        fields["content_type"] = ["Geospatial data"]

        # contributors

        # dates

        # edition

        # format

        # funding_information

        # identifiers

        # languages
        fields["languages"] = source_record.get("dct_language_sm")

        # links

        # locations

        # notes

        # publication_information

        # related_items

        # rights

        # subjects
        fields["subjects"] = self.get_subjects(source_record) or None

        # summary field
        return fields

    @staticmethod
    def get_subjects(source_record: dict) -> list[timdex.Subject]:
        """Get values from source record for TIMDEX subjects field.

        Unlike other TIMDEX sources, the subject scheme is not known
        for each term. The kind here represents the uncontrolled field
        in which the term was found.

        DCAT Keyword: https://www.w3.org/TR/vocab-dcat-2/#Property:resource_keyword
        DCAT Theme: https://www.w3.org/TR/vocab-dcat-2/#Property:resource_theme
        Dublin Core Subject: http://purl.org/dc/terms/subject

        Args:
            source_record: A JSON object representing a source record.
        """
        subjects = []
        aardvark_subject_fields = {
            "dcat_keyword_sm": "DCAT Keyword",
            "dcat_theme_sm": "DCAT Theme",
            "dct_subject_sm": "Dublin Core Subject",
            "gbl_resourceClass_sm": "Subject scheme not provided",
            "gbl_resourceType_sm": "Subject scheme not provided",
        }
        for aardvark_subject_field, kind_value in {
            key: value
            for key, value in aardvark_subject_fields.items()
            if key in source_record
        }.items():
            for subject in source_record[aardvark_subject_field]:
                subjects.append(timdex.Subject(value=[subject], kind=kind_value))
        return subjects
