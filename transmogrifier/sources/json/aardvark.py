import json
import logging
import re
from collections.abc import Iterator

import transmogrifier.models as timdex
from transmogrifier.helpers import validate_date, validate_date_range
from transmogrifier.sources.jsontransformer import JSONTransformer
from transmogrifier.sources.transformer import JSON

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

    def get_source_link(
        self,
        source_record: dict[str, JSON],
    ) -> str:
        """
        Class method to set the source link for the item.

        May be overridden by source subclasses if needed.

        Unlike other Transmogrifier sources that dynamically build a source link,
        MITAardvark files are expected to have a fully formed and appropriate source link
        in the metadata already.  This method relies on that data.

        Args:
            source_record: A JSON object representing a source record.
        """
        if (links := self.get_links(source_record)) and (
            url_links := [link for link in links if link.kind == "Website"]
        ):
            return url_links[0].url

        message = "Could not locate a kind=Website link to pull the source link from."
        raise ValueError(message)

    def get_timdex_record_id(self, source_record: dict[str, JSON]) -> str:
        """
        Class method to set the TIMDEX record id.

        Args:
            source_record: A JSON object representing a source record.
        """
        return (
            f"{self.source}:{self.get_source_record_id(source_record).replace('/', '-')}"
        )

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
        if isinstance(source_record.get("gbl_suppressed_b"), bool):
            return source_record["gbl_suppressed_b"]

        message = (
            f"Record ID '{cls.get_source_record_id(source_record)}': "
            "'gbl_suppressed_b' value is not a boolean or missing"
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

        # alternate_titles
        fields["alternate_titles"] = self.get_alternate_titles(source_record)

        # content_type
        fields["content_type"] = self.get_content_type(source_record)

        # contributors
        fields["contributors"] = self.get_contributors(source_record)

        # dates
        fields["dates"] = self.get_dates(source_record)

        # edition not used in MITAardvark

        # file_formats not used in MITAardvark

        # format
        fields["format"] = self.get_format(source_record)

        # funding_information not used in MITAardvark

        # identifiers
        fields["identifiers"] = self.get_identifiers(source_record)

        # languages
        fields["languages"] = self.get_languages(source_record)

        # links
        fields["links"] = self.get_links(source_record) or None

        # locations
        fields["locations"] = self.get_locations(source_record)

        # notes
        fields["notes"] = self.get_notes(source_record)

        # provider
        fields["provider"] = self.get_provider(source_record)

        # publishers
        fields["publishers"] = self.get_publishers(source_record)

        # related_items not used in MITAardvark

        # rights
        fields["rights"] = self.get_rights(source_record, self.source)

        # subjects
        fields["subjects"] = self.get_subjects(source_record)

        # summary field
        fields["summary"] = self.get_summary(source_record)

        return fields

    @classmethod
    def get_alternate_titles(
        cls, source_record: dict
    ) -> list[timdex.AlternateTitle] | None:
        return [
            timdex.AlternateTitle(value=title_value)
            for title_value in source_record.get("dct_alternative_sm", [])
        ] or None

    @classmethod
    def get_content_type(cls, source_record: dict) -> list[str] | None:
        return source_record.get("gbl_resourceType_sm") or None

    @classmethod
    def get_contributors(cls, source_record: dict) -> list[timdex.Contributor] | None:
        return [
            timdex.Contributor(value=contributor_value, kind="Creator")
            for contributor_value in source_record.get("dct_creator_sm", [])
        ] or None

    @classmethod
    def get_dates(cls, source_record: dict) -> list[timdex.Date] | None:
        dates: list[timdex.Date] = []
        dates.extend(cls._get_issued_dates(source_record))
        dates.extend(cls._get_coverage_dates(source_record))
        dates.extend(cls._get_range_dates(source_record))
        return dates or None

    @classmethod
    def _get_issued_dates(cls, source_record: dict) -> Iterator[timdex.Date]:
        if issued_date := source_record.get("dct_issued_s"):  # noqa: SIM102
            if validate_date(issued_date, cls.get_source_record_id(source_record)):
                yield (timdex.Date(value=issued_date, kind="Issued"))

    @classmethod
    def _get_coverage_dates(cls, source_record: dict) -> Iterator[timdex.Date]:
        coverage_date_values = []
        coverage_date_values.extend(source_record.get("dct_temporal_sm", []))
        coverage_date_values.extend(
            [
                str(date_value)
                for date_value in source_record.get("gbl_indexYear_im", [])
                if str(date_value) not in coverage_date_values
            ]
        )

        for coverage_date_value in coverage_date_values:
            if validate_date(
                coverage_date_value, cls.get_source_record_id(source_record)
            ):
                yield timdex.Date(value=coverage_date_value, kind="Coverage")

    @classmethod
    def _get_range_dates(cls, source_record: dict) -> Iterator[timdex.Date]:
        for date_range_string in source_record.get("gbl_dateRange_drsim", []):
            try:
                date_range_values = cls.parse_solr_date_range_string(
                    date_range_string, cls.get_source_record_id(source_record)
                )
            except ValueError as error:
                logger.warning(error)
                continue
            if validate_date_range(
                date_range_values[0],
                date_range_values[1],
                cls.get_source_record_id(source_record),
            ):
                yield timdex.Date(
                    kind="Coverage",
                    range=timdex.DateRange(
                        gte=date_range_values[0], lte=date_range_values[1]
                    ),
                )

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

    @classmethod
    def get_format(cls, source_record: dict) -> str | None:
        return source_record.get("dct_format_s") or None

    @classmethod
    def get_identifiers(cls, source_record: dict) -> list[timdex.Identifier] | None:
        return [
            timdex.Identifier(value=identifier_value, kind="Not specified")
            for identifier_value in source_record.get("dct_identifier_sm", [])
        ] or None

    @classmethod
    def get_languages(cls, source_record: dict) -> list[str] | None:
        return source_record.get("dct_language_sm") or None

    @classmethod
    def get_links(cls, source_record: dict) -> list[timdex.Link] | None:
        """
        The dct_references_s is a JSON string following a particular format defined here:
        https://opengeometadata.org/ogm-aardvark/#references.  Keys in the parsed JSON
        object define what kind of URL it is.  This is a flat mapping of namespace:url,
        except in the case of 'http://schema.org/downloadUrl' which will be an array of
        complex objects.
        """
        links = []
        if links_string := source_record.get("dct_references_s"):
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
                    links.append(
                        timdex.Link(url=schema_url, kind="Website", text="Website")
                    )
            except ValueError:
                message = (
                    f"Record ID '{cls.get_source_record_id(source_record)}': Unable to"
                    f" parse links string '{links_string}' as JSON"
                )
                logger.warning(message)
        return links or None

    @classmethod
    def get_locations(cls, source_record: dict) -> list[timdex.Location] | None:
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
                    f"Record ID '{cls.get_source_record_id(source_record)}': "
                    f"Unable to parse geodata string '{geodata_string}' "
                    f"in '{aardvark_location_field}'"
                )
                logger.warning(message)
        return locations or None

    @classmethod
    def get_notes(cls, source_record: dict) -> list[timdex.Note] | None:
        return [
            timdex.Note(value=[note_value], kind="Display note")
            for note_value in source_record.get("gbl_displayNote_sm", [])
        ] or None

    @classmethod
    def get_publishers(cls, source_record: dict) -> list[timdex.Publisher] | None:
        publishers = []
        if "dct_publisher_sm" in source_record:
            publishers.extend(
                [
                    timdex.Publisher(name=publisher)
                    for publisher in source_record["dct_publisher_sm"]
                ]
            )
        return publishers or None

    @classmethod
    def get_provider(cls, source_record: dict) -> str | None:
        return source_record.get("schema_provider_s") or None

    def get_rights(self, source_record: dict) -> list[timdex.Rights] | None:
        rights: list[timdex.Rights] = []
        kind_access_to_files = "Access to files"
        rights.extend(self._get_access_rights(source_record))
        rights.extend(self._get_license_rights(source_record))
        rights.extend(self._get_rights_and_rights_holders(source_record))
        if self.source == "gisogm":
            rights.extend(self._get_gisogm_rights(kind_access_to_files))
        elif self.source == "gismit":
            rights.extend(self._get_gismit_rights(source_record, kind_access_to_files))
        return rights or None

    @classmethod
    def _get_access_rights(cls, source_record: dict) -> Iterator[timdex.Rights]:
        if access_rights := source_record.get("dct_accessRights_s"):
            yield timdex.Rights(
                description=access_rights,
                kind="Access rights",
            )

    @classmethod
    def _get_license_rights(cls, source_record: dict) -> Iterator[timdex.Rights]:
        for rights_uri_value in source_record.get("dct_license_sm", []):
            yield (timdex.Rights(uri=rights_uri_value))

    @classmethod
    def _get_rights_and_rights_holders(
        cls, source_record: dict
    ) -> Iterator[timdex.Rights]:
        for aardvark_rights_field in ["dct_rights_sm", "dct_rightsHolder_sm"]:
            if aardvark_rights_field in source_record:
                yield (
                    timdex.Rights(
                        description=". ".join(source_record[aardvark_rights_field])
                    )
                )

    @classmethod
    def _get_gisogm_rights(cls, kind: str) -> Iterator[timdex.Rights]:
        yield timdex.Rights(
            description="unknown: check with owning institution",
            kind=kind,
        )

    @classmethod
    def _get_gismit_rights(
        cls, source_record: dict, kind: str
    ) -> Iterator[timdex.Rights]:
        if source_record["dct_accessRights_s"] == "Restricted":
            yield timdex.Rights(
                description="MIT authentication required",
                kind=kind,
            )
        else:
            yield timdex.Rights(
                description="no authentication required",
                kind=kind,
            )

    @classmethod
    def get_subjects(cls, source_record: dict) -> list[timdex.Subject] | None:
        """
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

        return subjects or None

    @classmethod
    def get_summary(cls, source_record: dict) -> list[str] | None:
        return source_record.get("dct_description_sm") or None
