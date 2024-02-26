# 4. Field for Institution Information

Follows: https://mitlibraries.github.io/guides/misc/adr.html

Date: 2024-02-22

## Status

Approved.

## Context

The UI for GeoData needs to display the host institution of non-MIT records (e.g., "Stanford", "University of Wisconsin-Madison") to signal to end users where an outlink is going. The question was raised of _where_ this information can be found in the existing TIMDEX data model or, if not present, what field will be used to store this information.

### Current mappings

| Source | Mappings | TIMDEX Field | Examples       |
| ------ | -------- | ------------ | -------------- |
| Alma   | [MARC$985$i](https://www.oclc.org/bibformats/en/9xx.html) | Holdings.Location | Hayden Library |
| MIT GIS | [schema_provider_s](https://opengeometadata.org/ogm-aardvark/#provider)| PublicationInformation | GIS Lab, MIT Libraries |
| OGM GIS | [schema_provider_s](https://opengeometadata.org/ogm-aardvark/#provider)| PublicationInformation | University of Wisconsin-Milwaukee |

1. **Does `geo-harvester` collect the required information (i.e., host institution)?**

   **Yes.** The Aardvark metadata schema includes a field called `schema_provider_s`, which is a single string value describing the [“organization [that] holds the resource or acts as the custodian for the metadata record and to help users understand which resources they can access”](https://opengeometadata.org/ogm-aardvark/#provider). 

   The derivation in `geo-harvester` sets `schema_provider_s` to "GIS Lab, MIT Libraries" for MIT records and the assigned name for the repo in the [OGM repositories config YAML file](https://github.com/MITLibraries/geo-harvester/blob/main/harvester/ogm_repositories_config.yaml).

2. **Does the `MITAardvark` transformer map the required information to a field in the TIMDEX data model?**

   **Yes, but its current mapping does not make the value easily accessible.** In `transmogrifier`, [the value from `schema_provider_s` is appended to `TimdexRecord.publication_information`](https://github.com/MITLibraries/transmogrifier/blob/main/transmogrifier/sources/json/aardvark.py#L382-L383), which comprises of a list of strings describing the publishing details for a given record. The contents of this field will vary by source and depending on what data is available. Trying to derive which value--from a list of strings (without any sort of identifier)--came from `schema_provider_s` is a nontrivial task.

3. **Do the other non-GIS TIMDEX sources have the required information? Are they currently mapped to existing TIMDEX fields?**

   Schemas and sample data for the other sources were explored to find other fields that may identifiy the "host institution" for a given resource:

   ---
   
   **Transformer:** [Datacite](https://schema.datacite.org/meta/kernel-4/metadata.xsd) | Zenodo
   **Source(s):** Abdul Latif Jameel Poverty Action Lab Dataverse (jpal) | Zenodo

   * `<publisher>`: The name of the entity that holds, archives, publishes prints, distributes, releases, issues, or produces the resource. This property will be used to formulate the citation, so consider the prominence of the role. **In the case of datasets, "publish" is understood to mean making the data available to the community of researchers**.
      * **TIMDEX field mapping**: [`publisher` -> `publication_information`](https://github.com/MITLibraries/transmogrifier/blob/main/transmogrifier/sources/xml/datacite.py#L249-L256)
      * **Example value(s):** As of this writing, the TIMDEX records from JPAL most likely all read "Harvard Dataverse" for this field; records from Zenodo most likely all read "Zenodo".

   **Transformer:** DspaceDim
   **Source(s):** Woodshole Open Access Server (whoas)
   * [`<dim:field mdschema="dc" element="publisher"`>](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/#http://purl.org/dc/terms/publisher): An entity responsible for making the resource available.
      * **TIMDEX field mapping:** [`publisher` -> `publication_information`](https://github.com/MITLibraries/transmogrifier/blob/main/transmogrifier/sources/xml/dspace_dim.py#L204-L207)
      * **Example value(s):** As of this writing, the TIMDEX records from WHOAS most likely all read "Woods Hole Oceanographic Institution" for this field.

   **Transformer:** DspaceMets (DSpace@MIT)
   **Source(s):** Dspace@MIT (dspace)
   * [`mods:publisher`](https://www.loc.gov/standards/mods/userguide/origininfo.html#publisher): The name of the entity that published, printed, distributed, released, issued, or produced the resource.
      * **TIMDEX field mapping:** [`publisher` -> `publication_information`](https://github.com/MITLibraries/transmogrifier/blob/main/transmogrifier/sources/xml/dspace_mets.py#L150-L152)
      * **Example value(s):** Massachusetts Institute of Technology, Springer Science and Business Media LLC, Public Library of Science (PLoS)

   
   **Transformer:** [Ead](https://www.loc.gov/ead/tglib/appendix_d.html)
   **Source(s):** MIT ArchivesSpace (aspace)
   * [`<publicationstmt><publisher>`|`<bibliography><bibref><imprint><publisher>`](https://www.loc.gov/ead/tglib/elements/publisher.html): When used in the publication statement, the name of the party responsible for issuing or distributing the encoded finding aid. Often this party is the same corporate body identified in the `<repository>` element in the finding aid. When used in a Bibliographic Reference <bibref>, the name of the party issuing a monograph or other bibliographic work cited in the finding aid.
   * [`repository`](https://www.loc.gov/ead/tglib/elements/repository.html): The institution or agency responsible for providing intellectual access to the materials being described. Although the repository providing intellectual access usually also has physical custody over the materials, this is not always the case.  When it is clear that the physical custodian does not provide intellectual access, use <physloc> to identify the custodian and <repository> to designate the intellectual caretaker. When a distinction cannot be made, assume that the custodian of the physical objects also provides intellectual access to them and should be recognized as the <repository>.
      * **TIMDEX field mapping:** [`repository` -> `publication_information`](https://github.com/MITLibraries/transmogrifier/blob/main/transmogrifier/sources/xml/ead.py#L208-L215)/
      * **Example value(s):** All records will read "Massachusetts Institute of Technology. Libraries. Department of Distinctive Collections"

   **Transformer:** Marc
   **Source(s):** MIT Alma (alma)
   * [`<datafield tag="270">`](https://www.loc.gov/marc/bibliographic/bd270.html): _Not currently used in transformer._ The contents for this data field code describe "An address (as well as electronic access information such as email, telephone, fax, TTY, etc. numbers) for contacts related to the content of the bibliographic item." However, it also reads: 
      * "For online resources, the addresses may apply to persons or agencies that are responsible for the general availability of the item."
      * "Contacts related to access to an instance of an online resource at a particular electronic location are contained in field [856 (Electronic Location and access)](https://www.loc.gov/marc/bibliographic/bd856.html) subfield $m (Contact for access assistance)".
   * [`<datafield tag="260"><subfield code="b">`](https://www.loc.gov/marc/bibliographic/bd260.html): Name of the publisher or distributor.
   * [`<datafield tag="264"><subfield code="b">`](https://www.loc.gov/marc/bibliographic/bd264.html): Name of producer, publisher, distributor, manufacturer.
      * **TIMDEX field mapping:** Text from datafield matching the tags and subfield code are joined into a single string value, separated by a single space (`" "`).
      * **Example value(s):** "Berlin ; Boston : De Gruyter Textbook, [2014]"

   **Transformer:** OaiDc/Springshare OaiDc
   **Source(s):** Research Databases (researchdatabases), LibGuides (libguides)
   * [`<dc:publisher>`](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/#http://purl.org/dc/terms/publisher): An entity responsible for making the resource available.
      * **TIMDEX field mapping:**: [`publisher` -> `publication_information`](https://github.com/MITLibraries/transmogrifier/blob/main/transmogrifier/sources/xml/oaidc.py#L91-L94)
      * **Example value(s):** For Research Databases, `publisher` isn't used; for LibGuides, this value will always read "MIT Libraries".

## Decision

**A new field called "provider" is added to the TIMDEX data model** (i.e., `TimdexRecord.provider`). This field will denote--as its name implies--the institution or organization that provides _access_ to the resource described in the TIMDEX record. This field exists at the top level of the TIMDEX data model, making it easily accessible for referencing in the UI or querying. This solution also avoids using existing fields (discussed below) in ways that obscure the TIMDEX data model.

The learnings from question 3 in the previous section suggest that for majority of the non-GIS sources on TIMDEX, the "publisher" of a resource can _sometimes_ be the "provider" of the resource as well. The addition of the "provider" field is an attempt to make a clearer distinction between these two fields, achieved by focusing the "provider" field on **who provides _access (physical or electronic)_ to the resource**.

---

### Other options that were discussed are described below:

**Option 1 - Remap Aardvark field `schema_provider_s` to `TimdexRecord.source`**

As of this writing, the `source` field derives its values from the names defined in the variable `transformer.config.SOURCE`. These names are hard-coded values that define the source of the TIMDEX resource at a higher level. This approach proposes storing lower-level values for OGM resources specifically, deviating from how the field is interpreted by other TIMDEX sources. 

Considerations for this approach:
* `MITAardvark` transformer would need to override `JSONTransformer.get_required_fields`
* `TimdexRecord.source` is a required field, but it would map data from `schema_provider_s`, which--although always derived by `geo-harvester`--_technically_ isn't required by the Aardvark metadata schema.
   * Not an issue at a technical level (i.e., can be done), but confusing at a conceptual level.


**Option 2 - Remap Aardvark field `schema_provider_s` to `TimdexRecord.holdings`**

This approach proposes mapping the values from `schema_provider_s` to `TimdexRecord.holdings` under one of two floated fields to the `Holding` data model: `location` or `institution`.

Considerations for this approach:
* As of this writing, `holdings` are only derived by the `Marc` transformer (for Alma resources).
* `Holding.location`: Existing values for this field include the physical location for a resource (e.g., "Library Storage Annex").
   * This approach would result in the values for `location` having different levels of specificity (e.g., host institution is not the same as physical location), which will be confusing.
* `Holding.institution`: This would be a new field, comprised of a single string value, that is added to the `Holding` data model.
   * There may be some resources that are aggregated by multiple institutions. The concept of "data provider" vs. "provider" was discussed. 
        * **Provider**: defined as "the institution / organization that hosts or provides access to the resource"
        * **Data provider**: the institution / organization that provided the metadata record you see before you

## Consequences

For GIS records, the UI can directly reference the values from `TimdexRecord.provider` to display the host institution for a resource on [GeoData](https://geodata.libraries.mit.edu/).

For other TIMDEX sources, given the decision and learnings outlined above, it may be worth considering whether we can map values from existing fields into `TimdexRecord.provider`. For instance:
* `aspace`: Use `repository` values.
* `jpal`: `publisher` values are likely to read "Harvard Dataverse" for all records.
* `libguides`: `publisher` values are likely to read "MIT Libraries" for all records.
* `whoas`: `publisher` values are likely to read "Woods Hole Oceanographic Institution" for all records.
* `zenodo`: `publisher` values are likely to read "Zenodo" for all records.

