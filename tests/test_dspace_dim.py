from pytest import raises

from transmogrifier.models import (
    AlternateTitle,
    Contributor,
    Date,
    Date_Range,
    Funder,
    Identifier,
    Link,
    Location,
    Note,
    RelatedItem,
    Rights,
    Subject,
    TimdexRecord,
)
from transmogrifier.sources.dspace_dim import DSpaceDim


def test_dspace_dim_iterates_through_all_records(dspace_dim_records):
    output_records = DSpaceDim(
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
        source_link="https://example.com/1912/2641",
        timdex_record_id="cool-repo:1912-2641",
        title=(
            "Time lapse movie of meiosis I in a living spermatocyte from the crane fly, "
            "Nephrotoma suturalis, viewed with polarized light microscopy"
        ),
        alternate_titles=[
            AlternateTitle(value="An Alternative Title", kind="alternative"),
        ],
        content_type=["Moving Image"],
        contents=["Chapter 1"],
        contributors=[
            Contributor(
                value="Jamerson, James",
                kind="Creator",
            ),
            Contributor(
                value="LaFountain, James R.",
                kind="author",
            ),
            Contributor(
                value="Oldenbourg, Rudolf",
                kind="author",
            ),
        ],
        dates=[
            Date(kind="accessioned", value="2009-01-08T16:24:37Z"),
            Date(kind="available", value="2009-01-08T16:24:37Z"),
            Date(kind="Publication", value="2002-11"),
            Date(kind="coverage", value="1201-01-01 - 1965-12-21"),
            Date(
                kind="coverage",
                range=Date_Range(gte="1201-01-01", lte="1965-12-21"),
            ),
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
            )
        ],
        identifiers=[Identifier(value="https://hdl.handle.net/1912/2641", kind="uri")],
        languages=["en_US"],
        links=[
            Link(
                url="https://hdl.handle.net/1912/2641",
                kind="Digital object URL",
                text="Digital object URL",
            )
        ],
        locations=[Location(value="Central equatorial Pacific Ocean")],
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
            ),
            RelatedItem(
                description="International Association of Aquatic and Marine Science "
                "Libraries and Information Centers (38th : 2012: Anchorage, Alaska)",
                relationship="ispartofseries",
            ),
            RelatedItem(
                uri="https://doi.org/10.1002/2016JB013228",
            ),
        ],
        rights=[
            Rights(
                description="Attribution-NonCommercial-NoDerivatives 4.0 International",
            ),
            Rights(
                uri="http://creativecommons.org/licenses/by-nc-nd/4.0/",
            ),
            Rights(description="CC-BY-NC 4.0", kind="license"),
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
        source_link="https://example.com/1912/2641",
        timdex_record_id="cool-repo:1912-2641",
        title=(
            "Time lapse movie of meiosis I in a living spermatocyte from the crane "
            "fly, Nephrotoma suturalis, viewed with polarized light microscopy"
        ),
        citation=(
            "Time lapse movie of meiosis I in a living spermatocyte from the crane fly, "
            "Nephrotoma suturalis, viewed with polarized light microscopy. "
            "https://example.com/1912/2641"
        ),
        dates=[Date(kind="Publication", value="2002-11")],
        format="electronic resource",
        identifiers=[Identifier(value="https://hdl.handle.net/1912/2641", kind="uri")],
        links=[
            Link(
                url="https://hdl.handle.net/1912/2641",
                kind="Digital object URL",
                text="Digital object URL",
            )
        ],
    )


def test_dspace_dim_record_blank_raises_error(
    dspace_dim_record_partial, dspace_dim_record_blank_title
):
    with raises(ValueError):
        output_records = dspace_dim_record_partial(
            input_records=dspace_dim_record_blank_title
        )
        next(output_records)


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
            "Jamerson, James. Time lapse movie of meiosis I in a living "
            "spermatocyte from the crane fly, Nephrotoma suturalis, viewed with "
            "polarized light microscopy. Woods Hole Oceanographic Institution. "
            "https://example.com/1912/2641"
        ),
        source="A Cool Repository",
        source_link="https://example.com/1912/2641",
        timdex_record_id="cool-repo:1912-2641",
        title=(
            "Time lapse movie of meiosis I in a living spermatocyte from the crane fly, "
            "Nephrotoma suturalis, viewed with polarized light microscopy"
        ),
        contributors=[
            Contributor(
                value="Jamerson, James",
                kind="Creator",
            ),
        ],
        dates=[
            Date(kind="Publication", value="2002-11"),
        ],
        format="electronic resource",
        identifiers=[Identifier(value="https://hdl.handle.net/1912/2641", kind="uri")],
        links=[
            Link(
                url="https://hdl.handle.net/1912/2641",
                kind="Digital object URL",
                restrictions=None,
                text="Digital object URL",
            )
        ],
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
