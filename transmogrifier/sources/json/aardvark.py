import json
import logging

import transmogrifier.models as timdex
from transmogrifier.helpers import parse_geodata_string, parse_solr_date_range_string
from transmogrifier.sources.transformer import JSONTransformer

logger = logging.getLogger(__name__)


class MITAardvark(JSONTransformer):
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
        Retrieve optional TIMDEX fields from an Aardvark JSON record.

        Overrides metaclass get_optional_fields() method.

        Args:
            source_record: A JSON object representing a source record.
        """
        fields: dict = {}

        source_record_id = self.get_source_record_id(source_record)

        # alternate_titles
        fields["alternate_titles"] = self.get_alternate_titles(source_record) or None

        # content_type
        fields["content_type"] = ["Geospatial data"]

        # contributors
        fields["contributors"] = self.get_contributors(source_record) or None

        # dates
        fields["dates"] = self.get_dates(source_record, source_record_id) or None

        # edition not used in MITAardvark

        # format
        fields["format"] = source_record.get("dct_format_s")

        # funding_information not used in MITAardvark

        # identifiers
        fields["identifiers"] = self.get_identifiers(source_record) or None

        # languages
        fields["languages"] = source_record.get("dct_language_sm")

        # links
        fields["links"] = self.get_links(source_record, source_record_id) or None

        # locations
        fields["locations"] = (
            self.get_locations(source_record, source_record_id) or None
        )

        # notes
        fields["notes"] = self.get_notes(source_record) or None

        # publication_information
        fields["publication_information"] = (
            self.get_publication_information(source_record) or None
        )

        # related_items not used in MITAardvark

        # rights
        fields["rights"] = self.get_rights(source_record) or None

        # subjects
        fields["subjects"] = self.get_subjects(source_record) or None

        # summary field
        fields["summary"] = source_record.get("dct_description_sm")

        return fields

    @staticmethod
    def get_alternate_titles(source_record: dict) -> list[timdex.AlternateTitle]:
        """Get values from source record for TIMDEX alternate_titles field."""
        return [
            timdex.AlternateTitle(value=title_value)
            for title_value in source_record.get("dct_alternative_sm", [])
        ]

    @staticmethod
    def get_contributors(source_record: dict) -> list[timdex.Contributor]:
        """Get values from source record for TIMDEX contributors field."""
        return [
            timdex.Contributor(value=contributor_value, kind="Creator")
            for contributor_value in source_record.get("dct_creator_sm", [])
        ]

    @staticmethod
    def get_dates(source_record: dict, source_record_id: str) -> list[timdex.Date]:
        """Get values from source record for TIMDEX dates field."""
        dates = []

        if "dct_issued_s" in source_record:
            dates.append(
                timdex.Date(value=source_record["dct_issued_s"], kind="Issued")
            )

        # logic to remove duplicate entries from the 2 fields that record coverage dates
        coverage_date_values = []
        coverage_date_values.extend(source_record.get("dct_temporal_sm", []))
        for date_value in [
            str(date_value)
            for date_value in source_record.get("gbl_indexYear_im", [])
            if str(date_value) not in coverage_date_values
        ]:
            coverage_date_values.append(date_value)
        for coverage_date_value in coverage_date_values:
            dates.append(timdex.Date(value=coverage_date_value, kind="Coverage"))

        for date_range_string in [
            date_range_strings
            for date_range_strings in source_record.get("gbl_dateRange_drsim", [])
        ]:
            date_range_values = parse_solr_date_range_string(
                date_range_string, source_record_id
            )
            dates.append(
                timdex.Date(
                    range=timdex.Date_Range(
                        gte=date_range_values[0], lte=date_range_values[1]
                    )
                )
            )

        return dates

    @staticmethod
    def get_identifiers(source_record: dict) -> list[timdex.Identifier]:
        """Get values from source record for TIMDEX identifiers field."""
        return [
            timdex.Identifier(value=identifier_value)
            for identifier_value in source_record.get("dct_identifier_sm", [])
        ]

    @staticmethod
    def get_links(source_record: dict, source_record_id: str) -> list[timdex.Link]:
        """Get values from source record for TIMDEX links field."""
        links = []
        try:
            links_string = source_record.get("dct_references_s", "")
            links_object = json.loads(links_string)
            links.extend(
                [
                    timdex.Link(
                        url=link.get("url"), kind="Download", text=link.get("label")
                    )
                    for link in links_object.get("https://schema.org/downloadUrl")
                ]
            )
        except ValueError:
            logger.warning(
                f"Record ID '{source_record_id}': Unable to parse "
                f"links string '{links_string}' as JSON"
            )
        return links

    @staticmethod
    def get_locations(
        source_record: dict, source_record_id: str
    ) -> list[timdex.Location]:
        """Get values from source record for TIMDEX locations field."""
        locations = []

        aardvark_location_fields = {
            "dcat_bbox": "Bounding Box",
            "locn_geometry": "Geometry",
        }
        for aardvark_location_field, kind_value in {
            key: value
            for key, value in aardvark_location_fields.items()
            if key in source_record
        }.items():
            if geodata_points := parse_geodata_string(
                source_record[aardvark_location_field], source_record_id
            ):
                locations.append(
                    timdex.Location(
                        geodata=geodata_points,
                        kind=kind_value,
                    )
                )
        return locations

    @staticmethod
    def get_notes(source_record: dict) -> list[timdex.Note]:
        """Get values from source record for TIMDEX notes field."""
        return [
            timdex.Note(value=[note_value], kind="Display note")
            for note_value in source_record.get("gbl_displayNote_sm", [])
        ]

    @staticmethod
    def get_publication_information(source_record: dict) -> list[str]:
        """Get values from source record for TIMDEX publication_information field."""
        publication_information = []

        if "dct_publisher_sm" in source_record:
            publication_information.extend(source_record["dct_publisher_sm"])

        if "schema_provider_s" in source_record:
            publication_information.append(source_record["schema_provider_s"])

        return publication_information

    @staticmethod
    def get_rights(source_record: dict) -> list[timdex.Rights]:
        """Get values from source record for TIMDEX rights field."""
        rights = []

        if "dct_accessRights_s" in source_record:
            rights.append(
                timdex.Rights(
                    description=source_record["dct_accessRights_s"], kind="Access"
                )
            )

        rights.extend(
            [
                timdex.Rights(uri=rights_uri_value)
                for rights_uri_value in source_record.get("dct_license_sm", [])
            ]
        )

        for aardvark_rights_field in ["dct_rights_sm", "dct_rightsHolder_sm"]:
            if aardvark_rights_field in source_record:
                rights.append(
                    timdex.Rights(
                        description=". ".join(source_record[aardvark_rights_field])
                    )
                )

        return rights

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
