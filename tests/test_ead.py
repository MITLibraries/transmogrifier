import pytest

import transmogrifier.models as timdex
from transmogrifier.helpers import parse_xml_records
from transmogrifier.sources.ead import Ead


def test_ead_record_all_fields_transform_correctly():
    ead_xml_records = parse_xml_records("tests/fixtures/ead/ead_record_all_fields.xml")
    output_records = Ead("aspace", ead_xml_records)
    assert next(output_records) == timdex.TimdexRecord(
        source="MIT ArchivesSpace",
        source_link="https://archivesspace.mit.edu/repositories/2/resources/1",
        timdex_record_id="aspace:repositories-2-resources-1",
        title=("Charles J. Connick Stained Glass Foundation Collection, " "VC.0002"),
        alternate_titles=[
            timdex.AlternateTitle(value="Title 2, VC.0002"),
            timdex.AlternateTitle(value="Title 3"),
        ],
        citation=(
            "Charles J. Connick Stained Glass Foundation Collection, "
            "VC-0002, box X.  Massachusetts Institute of Technology, Department of "
            "Distinctive Collections, Cambridge, Massachusetts."
        ),
        content_type=["Correspondence", "Archival materials"],
        contents=[
            (
                "This collection is organized into ten series: "
                "Series 1. Charles J. Connick and Connick Studio documents "
                "Series 2. Charles J. Connick Studio and Associates job information "
                "Series 3. Charles J. Connick Stained Glass Foundation documents"
            )
        ],
        contributors=[
            timdex.Contributor(
                value="Connick, Charles J. (Charles Jay)",
                kind="Creator",
                identifier=["https://lccn.loc.gov/nr99025157"],
            ),
            timdex.Contributor(
                value="Author, Unknown",
                identifier=["nr9902"],
                kind="Creator",
            ),
            timdex.Contributor(
                value="Name 2",
                affiliation=None,
                identifier=["http://viaf.org/viaf/nr99025157"],
                kind="Creator",
                mit_affiliated=None,
            ),
            timdex.Contributor(
                value="Name 3",
                affiliation=None,
                identifier=["https://snaccooperative.org/view/nr99025157"],
                kind="Creator",
                mit_affiliated=None,
            ),
        ],
        dates=[
            timdex.Date(kind="inclusive", value="1905-2012"),
            timdex.Date(value="1962 1968"),
        ],
        funding_information=[
            timdex.Funder(
                funder_name=(
                    "Processing sponsored by grant funding from the National Historical "
                    "Publications and Records Commission, grant number 94-0123"
                )
            )
        ],
        holdings=[
            timdex.Holding(
                note=(
                    "Existence and Location of Originals Original job cards are located "
                    "at the Boston Public Library Fine Arts Department."
                ),
            ),
            timdex.Holding(
                note=(
                    "Digital scans available on MIT Libraries' Dome Digital Repository: "
                    "http://dome.mit.edu/handle/1721.3/74802"
                ),
            ),
        ],
        identifiers=[
            timdex.Identifier(value="VC.0002"),
        ],
        languages=["English."],
        locations=[timdex.Location(value="Boston Massachusetts")],
        notes=[
            timdex.Note(
                value=[
                    "Source unknown. Originally deposited in University Library, "
                    "transferred to Department of Palaeography, 24 April 1958"
                ],
                kind="Acquisition Information",
            ),
            timdex.Note(
                value=[
                    "The records of the Mid-Ocean Dynamics Experiment came to the "
                    "Institute Archives in two accessions in 1980 and 1982. During "
                    "processing the collection was reduced from fifteen cubic feet to "
                    "four by discarding duplicate materials, financial records, and "
                    "publications not authored by MODE participants. Forty charts and "
                    "six inches of raw data presented the primary appraisal issues. "
                    "The raw data consisted of bulletins and reports referring to float "
                    "positions, moorings, isotherms, geostrophic velocity calculations, "
                    "ships' summaries, and work proposed and work carried out during the "
                    "MODE-I experiment."
                ],
                kind="Appraisal",
            ),
            timdex.Note(
                value=[
                    "Affiches americaines San Domingo: Imprimerie royale du "
                    "Cap, 1782. Nos. 30, 35."
                ],
                kind="Bibliography",
            ),
            timdex.Note(
                value=[
                    "Charles J. Connick (1875-1945) was an American "
                    "stained glass artist whose work may be found in cities all across "
                    "the United States. Connick's works in the Arts and Crafts movement "
                    "and beyond uniquely combined ancient and modern techniques and also "
                    "sparked a revival of medieval European stained glass craftsmanship. "
                    "Connick studied symbols and the interaction between light, color "
                    "and glass, as well as the crucial connection between the stained "
                    "glass window and its surrounding architecture. Connick founded his "
                    "own studio in 1912 in Boston. The Charles J. Connick Studio "
                    "performed work for churches, synagogues, schools, hospitals, public "
                    "buildings and private homes in cities across the United States and "
                    "in several other countries.  When Connick died in 1945, the "
                    "worker-owned studio continued as Charles J. Connick Associates "
                    "under the supervision of Orin E. Skinner in Boston's Back Bay "
                    "until closing in 1987. The Charles J. Connick Stained Glass "
                    "Foundation was created to preserve the Connick tradition of stained "
                    "glass.  At the same time, items from the studio were donated to the "
                    "Boston Public Library's Fine Arts Department to form Charles J. "
                    "Connick Studio Collection. In 2008, the Foundation donated its own "
                    "collection of stained glass windows, designs, cartoons, slides, "
                    "documents, periodicals, and other items to the MIT Libraries.  The "
                    "collection was processed over three years from March 2009 to May "
                    "2012."
                ],
                kind="Biography or History",
            ),
            timdex.Note(
                value=[
                    "The George Franklin Papers were maintained by the staff of the "
                    "Mayor's Office, City of Irvine, California, in the records storage "
                    "facility at City Hall from the time of Franklin's death in 1972 "
                    "until they were transferred, at his family's request, to Special "
                    "Collections and Archives, The UC Irvine Libraries, in 1988."
                ],
                kind="Custodial History",
            ),
            timdex.Note(
                value=[
                    "Some collection descriptions are based "
                    "on legacy data and may be "
                    "incomplete or contain inaccuracies. Description may change pending "
                    "verification. Please contact the MIT Department of Distinctive "
                    "Collections if you notice any errors or discrepancies."
                ],
                kind="Processing Information",
            ),
            timdex.Note(
                value=[
                    "The Charles J. Connick Stained Glass Foundation "
                    "Collection contains documents, photographs, slides, film, "
                    "periodicals, articles, clippings, lecture transcripts, tools, "
                    "sketches, designs and cartoons (full size stained glass window "
                    "designs), stained glass, and ephemera. The primary reference "
                    "material is the job information.  In particular, the job files "
                    "(boxes 7-9) are used most often in research.  Job files list "
                    "specific information for each job performed by the studio. For more "
                    "information, including access to the digital content of the "
                    "collection, please visit the collection website ."
                ],
                kind="Scope and Contents Note",
            ),
        ],
        physical_description="31 box(es)",
        publication_information=[
            "Massachusetts Institute of Technology. Libraries. Department of Distinctive "
            "Collections 2012 Massachusetts Institute of Technology Libraries Building "
            "14N-118 77 Massachusetts Avenue Cambridge, MA 02139-4307 "
            "distinctive-collections@mit.edu URL:"
        ],
        related_items=[
            timdex.RelatedItem(
                description=(
                    "Digitized items in the collection and a finding aid can be viewed "
                    "in the MIT Libraries Digital Repository, Dome: "
                    "http://dome.mit.edu/handle/1721.3/74802"
                ),
                relationship="Alternative Form Available",
            ),
            timdex.RelatedItem(
                description=(
                    "The Charles J. Connick and Associates Archives are located at the "
                    "Boston Public Library's Fine Arts Department "
                    "(http://www.bpl.org/research/finearts.htm). The Charles J. Connick "
                    "papers, 1901-1949 are located at the Smithsonian Archives of "
                    "American Art "
                    "(http://www.aaa.si.edu/collections/charles-j-connick-papers-7235). "
                    "Information on the Charles J. Connick Stained Glass Foundation may "
                    "be found at their website (http://www.cjconnick.org/)."
                ),
                item_type=None,
                relationship="Related Material",
                uri=None,
            ),
            timdex.RelatedItem(
                description=(
                    "The Society has published an expanded guide to this collection: "
                    "Guide to the Records of the American Crystal Sugar Company. . "
                    "Compiled by David Carmichael ; assisted by Lydia A. Lucas and "
                    "Marion E. Matters . St. Paul. Division of Archives and Manuscripts. "
                    "Minnesota Historical Society. 1985."
                ),
                relationship="Other Finding Aid",
            ),
            timdex.RelatedItem(
                description=(
                    "Add MS 88967: Michael Butterworth and J G Ballard: Correspondence, "
                    "1965-2011"
                ),
                relationship="Relation",
            ),
            timdex.RelatedItem(
                description=(
                    "Photographs have been transferred to Pictorial Collections of The "
                    "Bancroft Library."
                ),
                relationship="Separated Material",
            ),
        ],
        rights=[
            timdex.Rights(
                description="This collection is open.",
                kind="Conditions Governing Access",
            ),
            timdex.Rights(description="Public Record(s)", kind="Legal Status"),
            timdex.Rights(
                description=(
                    "Access to collections in the Department of "
                    "Distinctive Collections is not authorization to publish. Please see "
                    "the MIT Libraries Permissions Policy for permission information. "
                    "Copyright of some items in this collection may be held by "
                    "respective creators, not by the donor of the collection or MIT."
                ),
                kind="Conditions Governing Use",
            ),
        ],
        subjects=[
            timdex.Subject(
                value=["Glass painting and staining"],
                kind="Library of Congress Subject Headings",
            ),
            timdex.Subject(value=["Painting"], kind="Art & Architecture Thesaurus"),
            timdex.Subject(
                value=["Subject 2"],
                kind="Thesaurus for Use in College and University Archives",
            ),
            timdex.Subject(
                value=["Connick, Charles J. (Charles Jay)"],
                kind="Library of Congress Name Authority File",
            ),
            timdex.Subject(
                value=["Name 2"], kind="Virtual International Authority File"
            ),
            timdex.Subject(
                value=["Name 3"], kind="Social Networks and Archival Context"
            ),
            timdex.Subject(
                value=["Last, First"], kind="Library of Congress Name Authority File"
            ),
            timdex.Subject(
                value=["Correspondence"],
                kind=(
                    "Thesaurus for Graphic Materials II: Genre and Physical "
                    "Characteristic Terms"
                ),
            ),
            timdex.Subject(
                value=["Boston Massachusetts"],
            ),
        ],
        summary=[
            "Four manuscript survey maps and one plat map depicting areas of Orange "
            "County and attributed to the noted surveyor and judge Richard Egan. One map "
            "is dated 1878 and 1879 by Egan. The other maps are undated and unsigned but "
            "it is likely that he drew them during these years. These maps primarily "
            "depict subdivisions of non-rancho tracts of land occupying what is now "
            "Orange County, with the addition of some topographical details."
        ],
    )


def test_ead_record_with_missing_archdesc_raises_error():
    with pytest.raises(ValueError):
        ead_xml_records = parse_xml_records(
            "tests/fixtures/ead/ead_record_missing_archdesc.xml"
        )
        next(Ead("aspace", ead_xml_records))


def test_ead_record_with_missing_optional_fields_transforms_correctly():
    ead_xml_records = parse_xml_records(
        "tests/fixtures/ead/ead_record_missing_optional_fields.xml"
    )
    output_records = Ead("aspace", ead_xml_records)
    assert next(output_records) == timdex.TimdexRecord(
        source="MIT ArchivesSpace",
        source_link="https://archivesspace.mit.edu/repositories/2/resources/2",
        timdex_record_id="aspace:repositories-2-resources-2",
        title="Title not provided",
        citation=(
            "Title not provided. https://archivesspace.mit.edu/repositories/2/resources/2"
        ),
        content_type=["Not specified"],
    )


def test_ead_record_with_blank_optional_fields_transforms_correctly():
    ead_xml_records = parse_xml_records(
        "tests/fixtures/ead/ead_record_blank_optional_fields.xml"
    )
    output_records = Ead("aspace", ead_xml_records)
    assert next(output_records) == timdex.TimdexRecord(
        source="MIT ArchivesSpace",
        source_link="https://archivesspace.mit.edu/repositories/2/resources/3",
        timdex_record_id="aspace:repositories-2-resources-3",
        title="Title not provided",
        citation=(
            "Title not provided. https://archivesspace.mit.edu/repositories/2/resources/3"
        ),
        content_type=["Not specified"],
    )
