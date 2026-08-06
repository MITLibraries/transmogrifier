from collections import defaultdict

from bs4 import Tag  # type: ignore[import-untyped]

import transmogrifier.models as timdex
from transmogrifier.sources.xml.dspace_dim import DspaceDim


class DigitalCollections(DspaceDim):
    """Digital Collections transformer class."""

    @classmethod
    def get_funding_information(cls, _source_record: Tag) -> list[timdex.Funder] | None:
        return None

    @classmethod
    def get_notes(cls, source_record: Tag) -> list[timdex.Note] | None:
        cultural_context_notes = [
            timdex.Note(value=[str(cultural_context.string)], kind="culturalContext")
            for cultural_context in source_record.find_all(
                "dim:field", mdschema="vra", element="culturalContext", string=True
            )
        ]
        technique_notes = [
            timdex.Note(value=[str(technique.string)], kind="technique")
            for technique in source_record.find_all(
                "dim:field", mdschema="vra", element="technique", string=True
            )
        ]
        medium_notes = [
            timdex.Note(value=[str(medium.string)], kind="medium")
            for medium in source_record.find_all(
                "dim:field", element="format", qualifier="medium", string=True
            )
        ]
        notes = cultural_context_notes + technique_notes + medium_notes
        return notes or None

    @classmethod
    def get_provider(cls, source_record: Tag) -> str | None:
        if provider := source_record.find(
            "dim:field",
            element="publisher",
            qualifier="institution",
            string=True,
        ):
            return str(provider.string)
        return None

    @classmethod
    def get_publishers(cls, source_record: Tag) -> list[timdex.Publisher] | None:
        return [
            timdex.Publisher(name=str(publisher.string))
            for publisher in source_record.find_all(
                "dim:field", element="publisher", string=True
            )
            if not publisher.get("qualifier")
        ] or None

    @classmethod
    def get_subjects(cls, source_record: Tag) -> list[timdex.Subject] | None:
        subjects_dict: defaultdict[str, list[str]] = defaultdict(list)

        # Dublin Core subjects
        for subject in source_record.find_all(
            "dim:field", element="subject", string=True
        ):
            subjects_dict[
                subject.get("qualifier") or "Subject scheme not provided"
            ].append(str(subject.string))

        # VRA worktypes
        for worktype in source_record.find_all(
            "dim:field", mdschema="vra", element="worktype", string=True
        ):
            subjects_dict["worktype"].append(str(worktype.string))

        return [
            timdex.Subject(value=subject_value, kind=subject_scheme)
            for subject_scheme, subject_value in subjects_dict.items()
        ] or None

    @classmethod
    def get_summary(cls, source_record: Tag) -> list[str] | None:
        """Return a list of summary values.

        According to the stakeholder-approved metadata mapping, only the dc.description
        fields with no qualifier or with the qualifier "abstract" are included.
        """
        return [
            str(description.string)
            for description in source_record.find_all(
                "dim:field", element="description", string=True
            )
            if description.get("qualifier") in (None, "abstract")
        ] or None
