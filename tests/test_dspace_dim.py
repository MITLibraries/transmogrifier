import transmogrifier.models as timdex
from transmogrifier.helpers import parse_xml_records
from transmogrifier.sources.dspace_dim import DspaceDim


def test_dspace_dim_transform_with_all_fields_transforms_correctly():
    input_records = parse_xml_records(
        "tests/fixtures/dspace/dspace_dim_record_all_fields.xml"
    )
    output_records = DspaceDim("cool-repo", input_records)
    assert next(output_records) == timdex.TimdexRecord(
        citation="Journal of Geophysical Research: Solid Earth 121 (2016): 5859–5879",
        source="A Cool Repository",
        source_link="https://example.com/1912/2641",
        timdex_record_id="cool-repo:1912-2641",
        title=(
            "Time lapse movie of meiosis I in a living spermatocyte from the crane fly, "
            "Nephrotoma suturalis, viewed with polarized light microscopy"
        ),
        alternate_titles=[
            timdex.AlternateTitle(value="An Alternative Title", kind="alternative"),
        ],
        content_type=["Moving Image"],
        contents=["Chapter 1"],
        contributors=[
            timdex.Contributor(
                value="Jamerson, James",
                kind="Creator",
            ),
            timdex.Contributor(
                value="LaFountain, James R.",
                kind="author",
            ),
            timdex.Contributor(
                value="Oldenbourg, Rudolf",
                kind="author",
            ),
        ],
        dates=[
            timdex.Date(kind="accessioned", value="2009-01-08T16:24:37Z"),
            timdex.Date(kind="available", value="2009-01-08T16:24:37Z"),
            timdex.Date(kind="Publication date", value="2002-11"),
            timdex.Date(kind="coverage", note="1201-01-01 - 1965-12-21"),
            timdex.Date(
                kind="coverage",
                range=timdex.Date_Range(gte="1201-01-01", lte="1965-12-21"),
            ),
        ],
        file_formats=[
            "application/msword",
            "image/tiff",
            "video/quicktime",
        ],
        format="electronic resource",
        funding_information=[
            timdex.Funder(
                funder_name="NSF Grant Numbers: OCE-1029305, OCE-1029411, OCE-1249353",
            )
        ],
        identifiers=[
            timdex.Identifier(value="https://hdl.handle.net/1912/2641", kind="uri")
        ],
        languages=["en_US"],
        links=[
            timdex.Link(
                url="https://hdl.handle.net/1912/2641",
                kind="Digital object URL",
                text="Digital object URL",
            )
        ],
        locations=[timdex.Location(value="Central equatorial Pacific Ocean")],
        notes=[
            timdex.Note(
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
            timdex.Note(value=["2026-01"], kind="embargo"),
        ],
        publication_information=["Woods Hole Oceanographic Institution"],
        related_items=[
            timdex.RelatedItem(
                description=(
                    "A low resolution version of this movie was published as supplemental"
                    " material to: Rieder, C. L. and A. Khodjakov. Mitosis through the "
                    "microscope: advances in seeing inside live dividing cells. Science "
                    "300 (2003): 91-96, doi: 10.1126/science.1082177"
                ),
            ),
            timdex.RelatedItem(
                description="International Association of Aquatic and Marine Science "
                "Libraries and Information Centers (38th : 2012: Anchorage, Alaska)",
                relationship="ispartofseries",
            ),
            timdex.RelatedItem(
                uri="https://doi.org/10.1002/2016JB013228",
            ),
        ],
        rights=[
            timdex.Rights(
                description="Attribution-NonCommercial-NoDerivatives 4.0 International",
            ),
            timdex.Rights(
                uri="http://creativecommons.org/licenses/by-nc-nd/4.0/",
            ),
            timdex.Rights(description="CC-BY-NC 4.0", kind="license"),
        ],
        subjects=[
            timdex.Subject(
                value=["Spermatocyte", "Microtubules", "Kinetochore microtubules"],
                kind="lcsh",
            ),
            timdex.Subject(
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


def test_dspace_dim_transform_with_optional_fields_blank_transforms_correctly():
    input_records = parse_xml_records(
        "tests/fixtures/dspace/dspace_dim_record_optional_fields_blank.xml"
    )
    output_records = DspaceDim("cool-repo", input_records)
    assert next(output_records) == timdex.TimdexRecord(
        source="A Cool Repository",
        source_link="https://example.com/1912/2641",
        timdex_record_id="cool-repo:1912-2641",
        title="Title not provided",
        citation="Title not provided. https://example.com/1912/2641",
        format="electronic resource",
    )


def test_dspace_dim_transform_with_optional_fields_missing_transforms_correctly():
    input_records = parse_xml_records(
        "tests/fixtures/dspace/dspace_dim_record_optional_fields_missing.xml"
    )
    output_records = DspaceDim("cool-repo", input_records)
    assert next(output_records) == timdex.TimdexRecord(
        source="A Cool Repository",
        source_link="https://example.com/1912/2641",
        timdex_record_id="cool-repo:1912-2641",
        title="Title not provided",
        citation="Title not provided. https://example.com/1912/2641",
        format="electronic resource",
    )
