import json
import logging
import re

import transmogrifier.models as timdex
from transmogrifier.helpers import validate_date
from transmogrifier.sources.transformer import JSON, JSONTransformer

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
    def get_source_link(
        cls,
        _source_base_url: str,
        source_record_id: str,
        source_record: dict[str, JSON],
    ) -> str:
        """
        Class method to set the source link for the item.

        May be overridden by source subclasses if needed.

        Unlike other Transmogrifier sources that dynamically build a source link,
        MITAardvark files are expected to have a fully formed and appropriate source link
        in the metadata already.  This method relies on that data.

        Args:
            _source_base_url: Source base URL.  Not used for MITAardvark transforms.
            source_record_id: Record identifier for the source record.
            source_record: A BeautifulSoup Tag representing a single XML record.
                - not used by default implementation, but could be useful for subclass
                    overrides
        """
        links = cls.get_links(source_record, source_record_id)
        url_links = [link for link in links if link.kind == "Website"]
        if len(url_links) == 1:
            return url_links[0].url
        message = "Could not locate a kind=Website link to pull the source link from."
        raise ValueError(message)

    @classmethod
    def get_timdex_record_id(
        cls,
        source: str,
        source_record_id: str,
        _source_record: dict[str, JSON],
    ) -> str:
        """
        Class method to set the TIMDEX record id.

        Args:
            source: Source name.
            source_record_id: Record identifier for the source record.
            source_record: A JSON object representing a source record.
                - not used by default implementation, but could be useful for subclass
                overrides
        """
        return f"{source}:{source_record_id.replace('/', '-')}"

    @classmethod
    def get_source_record_id(cls, source_record: dict) -> str:
        """
        Get source record ID from a JSON record.

        Removes "mit:" and "ogm:" prefixes to avoid duplication, (e.g. "gismit:mit:abc123"
        NOT "gismit:mit:abc123")

        Args:
            source_record: A JSON object representing a source record.
        """
        return source_record["id"].removeprefix("mit:").removeprefix("ogm:")

    @classmethod
    def record_is_deleted(cls, source_record: dict) -> bool:
        """
        Determine whether record has a status of deleted.

        Args:
            source_record: A JSON object representing a source record.
        """
        if isinstance(source_record["gbl_suppressed_b"], bool):
            return source_record["gbl_suppressed_b"]

        message = (
            f"Record ID '{cls.get_source_record_id(source_record)}': "
            "'gbl_suppressed_b' value is not a boolean"
        )
        raise ValueError(message)

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
        fields["content_type"] = source_record.get("gbl_resourceType_sm")

        # contributors
        fields["contributors"] = self.get_contributors(source_record) or None

        # dates
        fields["dates"] = self.get_dates(source_record, source_record_id) or None

        # edition not used in MITAardvark

        # file_formats not used in MITAardvark

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
        fields["locations"] = self.get_locations(source_record, source_record_id) or None

        # notes
        fields["notes"] = self.get_notes(source_record) or None

        # provider
        fields["provider"] = source_record.get("schema_provider_s")

        # publishers
        fields["publishers"] = self.get_publishers(source_record) or None

        # related_items not used in MITAardvark

        # rights
        fields["rights"] = self.get_rights(self.source, source_record) or None

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

    @classmethod
    def get_dates(cls, source_record: dict, source_record_id: str) -> list[timdex.Date]:
        """Get values from source record for TIMDEX dates field.

        This method aggregates dates from a variety of Aardvark fields.  Once aggregated,
        the results are filtered to allow only well formed DateRanges or validated date
        strings.
        """
        dates = (
            cls._issued_dates(source_record)
            + cls._coverage_dates(source_record)
            + cls._range_dates(source_record, source_record_id)
        )
        return [
            date
            for date in dates
            # skip value validation for DateRange type dates
            if isinstance(date.range, timdex.DateRange)
            # validate date string if not None
            or (date.value is not None and validate_date(date.value, source_record_id))
        ]

    @classmethod
    def _issued_dates(cls, source_record: dict) -> list[timdex.Date]:
        """Get values for issued dates."""
        issued_dates = []
        if "dct_issued_s" in source_record:
            issued_dates.append(
                timdex.Date(value=source_record["dct_issued_s"], kind="Issued")
            )
        return issued_dates

    @classmethod
    def _coverage_dates(cls, source_record: dict) -> list[timdex.Date]:
        """Get values for coverage dates."""
        coverage_dates = []
        coverage_date_values = []
        coverage_date_values.extend(source_record.get("dct_temporal_sm", []))
        coverage_date_values.extend(
            [
                str(date_value)
                for date_value in source_record.get("gbl_indexYear_im", [])
                if str(date_value) not in coverage_date_values
            ]
        )
        coverage_dates.extend(
            [
                timdex.Date(value=coverage_date_value, kind="Coverage")
                for coverage_date_value in coverage_date_values
            ]
        )
        return coverage_dates

    @classmethod
    def _range_dates(
        cls, source_record: dict, source_record_id: str
    ) -> list[timdex.Date]:
        """Get values for issued dates."""
        range_dates = []
        for date_range_string in source_record.get("gbl_dateRange_drsim", []):
            try:
                date_range_values = cls.parse_solr_date_range_string(
                    date_range_string, source_record_id
                )
            except ValueError as exc:
                logger.warning(exc)
                continue
            range_dates.append(
                timdex.Date(
                    kind="Coverage",
                    range=timdex.DateRange(
                        gte=date_range_values[0], lte=date_range_values[1]
                    ),
                )
            )
        return range_dates

    @classmethod
    def parse_solr_date_range_string(
        cls, date_range_string: str, source_record_id: str
    ) -> tuple:
        """Get a list of values from a Solr-formatted date range string.

        Example:
         - "[1943 TO 1946]"

        Args:
            date_range_string: Formatted date range string to parse.
            source_record_id: The ID of the record containing the string to parse.
        """
        try:
            matches = re.match(r"\[([0-9]{4}) TO ([0-9]{4})\]", date_range_string)
            return matches.groups()  # type: ignore[union-attr]
        except AttributeError:
            message = (
                f"Record ID '{source_record_id}': "
                f"Unable to parse date range string '{date_range_string}'"
            )
            raise ValueError(message) from None

    @staticmethod
    def get_identifiers(source_record: dict) -> list[timdex.Identifier]:
        """Get values from source record for TIMDEX identifiers field."""
        return [
            timdex.Identifier(value=identifier_value, kind="Not specified")
            for identifier_value in source_record.get("dct_identifier_sm", [])
        ]

    @staticmethod
    def get_links(source_record: dict, source_record_id: str) -> list[timdex.Link]:
        """Get values from source record for TIMDEX links field.

        The dct_references_s is a JSON string following a particular format defined here:
        https://opengeometadata.org/ogm-aardvark/#references.  Keys in the parsed JSON
        object define what kind of URL it is.  This is a flat mapping of namespace:url,
        except in the case of 'http://schema.org/downloadUrl' which will be an array of
        complex objects.
        """
        links = []
        links_string = source_record["dct_references_s"]
        try:
            links_object = json.loads(links_string)
            links.extend(
                [
                    timdex.Link(
                        url=link.get("url"), kind="Download", text=link.get("label")
                    )
                    for link in links_object.get("http://schema.org/downloadUrl", [])
                    if isinstance(link.get("url", {}), str)
                ]
            )
            if schema_url := links_object.get("http://schema.org/url"):
                links.append(timdex.Link(url=schema_url, kind="Website", text="Website"))
        except ValueError:
            message = (
                f"Record ID '{source_record_id}': Unable to parse "
                f"links string '{links_string}' as JSON"
            )
            logger.warning(message)
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
        for aardvark_location_field, kind_value in aardvark_location_fields.items():
            if aardvark_location_field not in source_record:
                continue
            if (
                geodata_string := source_record[aardvark_location_field]
            ) and "ENVELOPE" in source_record[aardvark_location_field]:
                locations.append(
                    timdex.Location(
                        geoshape=geodata_string.replace("ENVELOPE", "BBOX "),
                        kind=kind_value,
                    )
                )
            else:
                message = (
                    f"Record ID '{source_record_id}': "
                    f"Unable to parse geodata string '{geodata_string}' "
                    f"in '{aardvark_location_field}'"
                )
                logger.warning(message)
        return locations

    @staticmethod
    def get_notes(source_record: dict) -> list[timdex.Note]:
        """Get values from source record for TIMDEX notes field."""
        return [
            timdex.Note(value=[note_value], kind="Display note")
            for note_value in source_record.get("gbl_displayNote_sm", [])
        ]

    @staticmethod
    def get_publishers(source_record: dict) -> list[timdex.Publisher]:
        """Get values from source record for TIMDEX publishers field."""
        publishers = []
        if "dct_publisher_sm" in source_record:
            publishers.extend(
                [
                    timdex.Publisher(name=publisher)
                    for publisher in source_record["dct_publisher_sm"]
                ]
            )
        return publishers

    @staticmethod
    def get_rights(source: str, source_record: dict) -> list[timdex.Rights]:
        """Get values from source record for TIMDEX rights field."""
        rights = []
        kind_access_to_files = "Access to files"

        rights.append(
            timdex.Rights(
                description=source_record["dct_accessRights_s"],
                kind="Access rights",
            )
        )

        if source == "gisogm":
            rights.append(
                timdex.Rights(description="Not owned by MIT", kind=kind_access_to_files)
            )
        elif source == "gismit":
            if source_record["dct_accessRights_s"] == "Restricted":
                rights.append(
                    timdex.Rights(
                        description="MIT authentication",
                        kind=kind_access_to_files,
                    )
                )
            else:
                rights.append(
                    timdex.Rights(
                        description="Free/open to all", kind=kind_access_to_files
                    )
                )

        rights.extend(
            [
                timdex.Rights(uri=rights_uri_value)
                for rights_uri_value in source_record.get("dct_license_sm", [])
            ]
        )

        rights.extend(
            [
                timdex.Rights(description=". ".join(source_record[aardvark_rights_field]))
                for aardvark_rights_field in ["dct_rights_sm", "dct_rightsHolder_sm"]
                if aardvark_rights_field in source_record
            ]
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
            "dcat_keyword_sm": "DCAT; Keyword",
            "dcat_theme_sm": "DCAT; Theme",
            "dct_spatial_sm": "Dublin Core; Spatial",
            "dct_subject_sm": "Dublin Core; Subject",
            "gbl_resourceClass_sm": "Subject scheme not provided",
        }

        for subject_field, subject_kind in aardvark_subject_fields.items():
            subjects.extend(
                [
                    timdex.Subject(value=[subject], kind=subject_kind)
                    for subject in source_record.get(subject_field, [])
                ]
            )

        return subjects
