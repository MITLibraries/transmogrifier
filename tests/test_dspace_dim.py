from pytest import raises

from transmogrifier.models import (
    AlternateTitle,
    Contributor,
    Date,
    Funder,
    Identifier,
    Note,
    RelatedItem,
    Rights,
    Subject,
    TimdexRecord,
)
from transmogrifier.sources.dspace_dim import DSpace_dim


def test_dspace_dim_iterates_through_all_records(dspace_dim_records):
    output_records = DSpace_dim(
        "whoas",
        "https://darchive.mblwhoilibrary.org/handle/",
        "Woods Hole Open Access Server",
        dspace_dim_records,
    )
    assert len(list(output_records)) == 5


def test_dspace_dim_record_all_fields(
    dspace_dim_record_partial, dspace_dim_record_all_fields
):
    output_records = dspace_dim_record_partial(
        input_records=dspace_dim_record_all_fields
    )
    assert next(output_records) == TimdexRecord(
        citation="Journal of Geophysical Research: Solid Earth 121 (2016): 5859–5879",
        source="A Cool Repository",
        source_link="https://example.com/oai:darchive.mblwhoilibrary.org:1912/2641",
        timdex_record_id="cool-repo:oai:darchive.mblwhoilibrary.org:1912-2641",
        title=(
            "Time lapse movie of meiosis I in a living spermatocyte from the crane fly, "
            "Nephrotoma suturalis, viewed with polarized light microscopy"
        ),
        alternate_titles=[
            AlternateTitle(value="An Alternative Title", kind="alternative"),
        ],
        contributors=[
            Contributor(
                value="Jamerson, James",
                affiliation=None,
                identifier=None,
                kind="Creator",
                mit_affiliated=None,
            ),
            Contributor(
                value="LaFountain, James R.",
                affiliation=None,
                identifier=None,
                kind="author",
                mit_affiliated=None,
            ),
            Contributor(
                value="Oldenbourg, Rudolf",
                affiliation=None,
                identifier=None,
                kind="author",
                mit_affiliated=None,
            ),
        ],
        dates=[
            Date(
                kind="accessioned", note=None, range=None, value="2009-01-08T16:24:37Z"
            ),
            Date(kind="available", note=None, range=None, value="2009-01-08T16:24:37Z"),
            Date(kind="issued", note=None, range=None, value="2002-11"),
        ],
        file_formats=[
            "application/msword",
            "image/tiff",
            "video/quicktime",
        ],
        format="electronic resource",
        funding_information=[
            Funder(
                funder_name="NSF Grant Numbers: OCE-1029305, OCE-1029411, OCE-1249353",
                funder_identifier=None,
                funder_identifier_type=None,
                award_number=None,
                award_uri=None,
            )
        ],
        identifiers=[Identifier(value="https://hdl.handle.net/1912/2641", kind="uri")],
        languages=["en_US"],
        notes=[
            Note(
                value=[
                    (
                        "Author Posting. © The Author(s), 2008. This is the author's "
                        "version of the work. It is posted here by permission of John "
                        "Wiley  Sons for personal use, not for redistribution. The "
                        "definitive version was published in Journal of Field Robotics "
                        "25 (2008): 861-879, doi:10.1002/rob.20250."
                    )
                ],
                kind=None,
            ),
            Note(value=["2026-01"], kind="embargo"),
        ],
        publication_information=["Woods Hole Oceanographic Institution"],
        related_items=[
            RelatedItem(
                description=(
                    "A low resolution version of this movie was published as supplemental"
                    " material to: Rieder, C. L. and A. Khodjakov. Mitosis through the "
                    "microscope: advances in seeing inside live dividing cells. Science "
                    "300 (2003): 91-96, doi: 10.1126/science.1082177"
                ),
                item_type=None,
                relationship=None,
                uri=None,
            ),
            RelatedItem(
                description="International Association of Aquatic and Marine Science "
                "Libraries and Information Centers (38th : 2012: Anchorage, Alaska)",
                item_type=None,
                relationship="ispartofseries",
                uri=None,
            ),
            RelatedItem(
                description=None,
                item_type=None,
                relationship=None,
                uri="https://doi.org/10.1002/2016JB013228",
            ),
        ],
        rights=[
            Rights(
                description="Attribution-NonCommercial-NoDerivatives 4.0 International",
                kind=None,
                uri=None,
            ),
            Rights(
                description=None,
                kind=None,
                uri="http://creativecommons.org/licenses/by-nc-nd/4.0/",
            ),
            Rights(description="CC-BY-NC 4.0", kind="license", uri=None),
        ],
        subjects=[
            Subject(
                value=["Spermatocyte", "Microtubules", "Kinetochore microtubules"],
                kind="lcsh",
            ),
            Subject(
                value=["Polarized light microscopy", "LC-PolScope"],
                kind="Subject scheme not provided",
            ),
        ],
        summary=[
            (
                "The events of meiosis I in a living spermatocyte obtained from the "
                "testis of a crane-fly larva are recorded in this time-lapse sequence "
                "beginning at diakinesis through telophase to the near completion of "
                "cytokinesis following meiosis I."
            )
        ],
    )


def test_dspace_dim_record_optional_fields_blank_transforms_correctly(
    dspace_dim_record_partial, dspace_dim_record_optional_fields_blank
):
    output_records = dspace_dim_record_partial(
        input_records=dspace_dim_record_optional_fields_blank
    )
    assert next(output_records) == TimdexRecord(
        source="A Cool Repository",
        source_link="https://example.com/oai:darchive.mblwhoilibrary.org:1912/2641",
        timdex_record_id="cool-repo:oai:darchive.mblwhoilibrary.org:1912-2641",
        title=(
            "Time lapse movie of meiosis I in a living spermatocyte from the crane "
            "fly, Nephrotoma suturalis, viewed with polarized light microscopy"
        ),
        alternate_titles=None,
        citation=(
            "(2002-11): Time lapse movie of meiosis I in a living spermatocyte from "
            "the crane fly, Nephrotoma suturalis, viewed with polarized light microscopy."
            " https://example.com/oai:darchive.mblwhoilibrary.org:1912/2641"
        ),
        content_type=None,
        contributors=None,
        dates=[Date(kind="issued", note=None, range=None, value="2002-11")],
        edition=None,
        file_formats=None,
        format="electronic resource",
        funding_information=None,
        identifiers=[Identifier(value="https://hdl.handle.net/1912/2641", kind="uri")],
        languages=None,
        locations=None,
        notes=None,
        publication_information=None,
        related_items=None,
        rights=None,
        subjects=None,
        summary=None,
    )


def test_dspace_dim_record_multiple_titles_raises_error(
    dspace_dim_record_partial, dspace_dim_record_multiple_titles
):
    with raises(ValueError):
        output_records = dspace_dim_record_partial(
            input_records=dspace_dim_record_multiple_titles
        )
        next(output_records)


def test_dspace_dim_record_no_citation_field(
    dspace_dim_record_partial, dspace_dim_record_no_citation_field
):
    output_records = dspace_dim_record_partial(
        input_records=dspace_dim_record_no_citation_field
    )
    assert next(output_records) == TimdexRecord(
        citation=(
            "Jamerson, James (2002-11): Time lapse movie of meiosis I in a living "
            "spermatocyte from the crane fly, Nephrotoma suturalis, viewed with "
            "polarized light microscopy. Woods Hole Oceanographic Institution. "
            "https://example.com/oai:darchive.mblwhoilibrary.org:1912/2641"
        ),
        source="A Cool Repository",
        source_link="https://example.com/oai:darchive.mblwhoilibrary.org:1912/2641",
        timdex_record_id="cool-repo:oai:darchive.mblwhoilibrary.org:1912-2641",
        title=(
            "Time lapse movie of meiosis I in a living spermatocyte from the crane fly, "
            "Nephrotoma suturalis, viewed with polarized light microscopy"
        ),
        contributors=[
            Contributor(
                value="Jamerson, James",
                affiliation=None,
                identifier=None,
                kind="Creator",
                mit_affiliated=None,
            ),
        ],
        dates=[
            Date(
                kind="accessioned", note=None, range=None, value="2009-01-08T16:24:37Z"
            ),
            Date(kind="available", note=None, range=None, value="2009-01-08T16:24:37Z"),
            Date(kind="issued", note=None, range=None, value="2002-11"),
        ],
        format="electronic resource",
        identifiers=[Identifier(value="https://hdl.handle.net/1912/2641", kind="uri")],
        publication_information=["Woods Hole Oceanographic Institution"],
    )


def test_dspace_dim_record_no_title_raises_error(
    dspace_dim_record_partial, dspace_dim_record_no_title
):
    with raises(ValueError):
        output_records = dspace_dim_record_partial(
            input_records=dspace_dim_record_no_title
        )
        next(output_records)


def test_dspace_dim_record_unqualified_identifier(
    dspace_dim_record_partial, dspace_dim_record_unqualified_identifier
):
    output_records = dspace_dim_record_partial(
        input_records=dspace_dim_record_unqualified_identifier
    )
    assert next(output_records) == TimdexRecord(
        citation="Journal of Geophysical Research: Solid Earth 121 (2016): 5859–5879",
        source="A Cool Repository",
        source_link="https://example.com/oai:darchive.mblwhoilibrary.org:1912/2641",
        timdex_record_id="cool-repo:oai:darchive.mblwhoilibrary.org:1912-2641",
        title=(
            "Time lapse movie of meiosis I in a living spermatocyte from the crane fly, "
            "Nephrotoma suturalis, viewed with polarized light microscopy"
        ),
        dates=[
            Date(
                kind="accessioned", note=None, range=None, value="2009-01-08T16:24:37Z"
            ),
            Date(kind="available", note=None, range=None, value="2009-01-08T16:24:37Z"),
            Date(kind="issued", note=None, range=None, value="2002-11"),
        ],
        format="electronic resource",
        identifiers=[Identifier(value="123456", kind=None)],
    )
