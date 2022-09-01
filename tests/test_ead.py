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
        title=(
            "Guide to the Charles J. Connick Stained Glass Foundation Collection, "
            "VC.0002"
        ),
        alternate_titles=[
            timdex.AlternateTitle(value="A subtitle", kind="subtitle"),
            timdex.AlternateTitle(value="Title 2, VC.0002"),
            timdex.AlternateTitle(value="Title 3"),
        ],
        citation=(
            "Preferred Citation Charles J. Connick Stained Glass Foundation Collection, "
            "VC-0002, box X.  Massachusetts Institute of Technology, Department of "
            "Distinctive Collections, Cambridge, Massachusetts."
        ),
        content_type=["Universal transverse Mercator projection"],
        contents=[
            (
                "Scope and Contents The Charles J. Connick Stained Glass Foundation "
                "Collection contains documents, photographs, slides, film, periodicals, "
                "articles, clippings, lecture transcripts, tools, sketches, designs and "
                "cartoons (full size stained glass window designs), stained glass, and "
                "ephemera. The primary reference material is the job information.  In "
                "particular, the job files (boxes 7-9) are used most often in research.  "
                "Job files list specific information for each job performed by the "
                "studio. For more information, including access to the digital content "
                "of the collection, please visit the collection website ."
            )
        ],
        contributors=[
            timdex.Contributor(
                value="Connick, Charles J. (Charles Jay)",
                kind="Creator",
                identifier=["nr99025157"],
            )
        ],
        dates=[
            timdex.Date(kind="inclusive", value="1905-2012"),
            timdex.Date(value="1962 1968"),
        ],
        format="electronic resource",
        funding_information=[
            timdex.Funder(
                funder_name=(
                    "Processing sponsored by grant funding from the National Historical "
                    "Publications and Records Commission, grant number 94-0123"
                )
            )
        ],
        identifiers=[
            timdex.Identifier(value="VC.0002"),
        ],
        languages=["English"],
        links=[
            timdex.Link(
                url="http://hdl.handle.net/1721.3/75096",
                text="Saint Martin of Tours, CONGI_0002",
            ),
        ],
        locations=[
            timdex.Location(
                value=(
                    "Existence and Location of Originals Original job cards are located "
                    "at the Boston Public Library Fine Arts Department."
                )
            ),
            timdex.Location(
                value=(
                    "Digital scans available on MIT Libraries' Dome Digital Repository: "
                    "http://dome.mit.edu/handle/1721.3/74802"
                )
            ),
        ],
        notes=[
            timdex.Note(
                value=[
                    "Source unknown. Originally deposited in University Library, "
                    "transferred to Department of Palaeography, 24 April 1958"
                ],
                kind="acqinfo",
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
                kind="appraisal",
            ),
            timdex.Note(
                value=[
                    "Monographs Affiches americaines San Domingo: Imprimerie royale du "
                    "Cap, 1782. Nos. 30, 35."
                ],
                kind="bibliography",
            ),
            timdex.Note(
                value=[
                    "Biographical Note Charles J. Connick (1875-1945) was an American "
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
                kind="bioghist",
            ),
            timdex.Note(
                value=[
                    "The George Franklin Papers were maintained by the staff of the "
                    "Mayor's Office, City of Irvine, California, in the records storage "
                    "facility at City Hall from the time of Franklin's death in 1972 "
                    "until they were transferred, at his family's request, to Special "
                    "Collections and Archives, The UC Irvine Libraries, in 1988."
                ],
                kind="custodhist",
            ),
            timdex.Note(value=["Processing Information note"], kind="processinfo"),
            timdex.Note(
                value=[
                    "Processing Information note Some collection descriptions are based "
                    "on legacy data and may be incomplete or contain inaccuracies. "
                    "Description may change pending verification. Please contact the MIT "
                    "Department of Distinctive Collections if you notice any errors or "
                    "discrepancies."
                ],
                kind="processinfo",
            ),
        ],
        physical_description=("31 box(es) 12 linear feet"),
        publication_information=[
            "Massachusetts Institute of Technology. Libraries. Department of Distinctive "
            "Collections 2012 Massachusetts Institute of Technology Libraries Building "
            "14N-118 77 Massachusetts Avenue Cambridge, MA 02139-4307 "
            "distinctive-collections@mit.edu URL:"
        ],
        related_items=[
            timdex.RelatedItem(
                description=(
                    "Existence and Location of Copies Digitized items in the collection "
                    "and a finding aid can be viewed in the MIT Libraries Digital "
                    "Repository, Dome: http://dome.mit.edu/handle/1721.3/74802"
                ),
                relationship="altformavail",
            ),
            timdex.RelatedItem(
                description=(
                    "Related Materials The Charles J. Connick and Associates Archives "
                    "are located at the Boston Public Library's Fine Arts Department "
                    "(http://www.bpl.org/research/finearts.htm). The Charles J. Connick "
                    "papers, 1901-1949 are located at the Smithsonian Archives of "
                    "American Art "
                    "(http://www.aaa.si.edu/collections/charles-j-connick-papers-7235). "
                    "Information on the Charles J. Connick Stained Glass Foundation may "
                    "be found at their website (http://www.cjconnick.org/)."
                ),
                item_type=None,
                relationship="relatedmaterial",
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
                relationship="otherfindaid",
            ),
            timdex.RelatedItem(
                description=(
                    "Add MS 88967: Michael Butterworth and J G Ballard: Correspondence, "
                    "1965-2011"
                ),
                relationship="relation",
            ),
        ],
        rights=[
            timdex.Rights(
                description="Conditions Governing Access This collection is open.",
                kind="accessrestrict",
            ),
            timdex.Rights(description="Public Record(s)", kind="legalstatus"),
            timdex.Rights(
                description=(
                    "Conditions Governing Use Access to collections in the Department of "
                    "Distinctive Collections is not authorization to publish. Please see "
                    "the MIT Libraries Permissions Policy for permission information. "
                    "Copyright of some items in this collection may be held by "
                    "respective creators, not by the donor of the collection or MIT."
                ),
                kind="userestrict",
            ),
        ],
        subjects=[
            timdex.Subject(value=["Glass painting and staining"], kind="lcsh"),
            timdex.Subject(value=["Connick, Charles J. (Charles Jay)"], kind="naf"),
            timdex.Subject(value=["Correspondence"], kind="gmgpc"),
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
        format="electronic resource",
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
        format="electronic resource",
    )
