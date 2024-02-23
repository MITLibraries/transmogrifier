# 3. Support Aggregations on Publisher Name

Date: 2024-02-23

## Status

Accepted

## Context

Our current data model maps data about Publisher Name, Publication Year, and Publication Location into a single multivalued field (an Array of Strings). Mapping these different concepts into a single field makes the data less meaningful and less useful than it could be with a change to our data model.

Mapping differnt types of data into a single field makes aggregation confusing as we'd see things like "1999" along side "Massachusetts Institute of Technology" which is not usable.

### Current mappings

| Source | Mappings | TIMDEX Field | Examples |
| --- | --- | --- | --- |
| Alma | [MARC 260$abcdef](https://www.loc.gov/marc/bibliographic/bd260.html) | PublicationInformation | Charlottesville : University of Virginia Press, [2015], ©2015 |
| | [MARC264$abc](https://www.loc.gov/marc/bibliographic/bd264.html) |  PublicationInformation | DeKalb, Illinois : NIU Press, 2014, ©2014 |
| |   | PublicationInformation | null |
| |   | PublicationInformation  | A.O.K. 3 |
| |   | PublicationInformation  | American Antiquarian Society Historical Periodicals |
| DSpace@MIT (METS) | XML slect array of Strings matching element `publisher` | PublicationInformation | Massachusetts Institute of Technology |
| |   | PublicationInformation  | Elsevier BV |
| |   | PublicationInformation  | null |
| |   | PublicationInformation | ACM|Creativity and Cognition |
| |   |  PublicationInformation | Cambridge, Mass. : Alfred P. Sloan School of Management, Massachusetts Institute of Technology |
| |   | PublicationInformation  | Elsevier |
| |   | PublicationInformation  | Wiley |
| ArchivesSpace | XML select array of Strings matching element `dc:publisher`  | PublicationInformation  | Massachusetts Institute of Technology. Libraries. Department of Distinctive Collections (note: this appears to be effectively a static string for all of our ASpace records) |
| MIT GIS |   | PublicationInformation |  |
| OGM GIS |   | PublicationInformation  |  |

### Proposed mappings (Option 1)

Create a new object `PublicationInfo` and map data into it. Most sources just use `Publication.name` but Alma uses additional fields.

```json
{
  publicationInfo: [{
    name: String
    location: String
    date: String (ideally dates would be dates... but that may be out of scope for now)
  }]
}
```

Notes: we should consider whether this really needs to be an array. 260 and 264 are repeatable fields in MARC, but whether they are regularly used in that way or if we could instead pick the "first" one that shows up and get a simpler model without losing any real world functionality would be worth investigating. For now it is modeled as an array of `PublicationInfo` assuming that is appropriate.

GraphQL would collapse the new object and continue to serve it as the deprecated field `PublicationInformation` until we are confident it is no longer being used.

| Source | Mappings | TIMDEX Field | Notes |
| --- | --- | --- | --- |
| Alma | [MARC 260$a](https://www.loc.gov/marc/bibliographic/bd260.html) | PublicationInfo.Location | |
| Alma | [MARC 264$a](https://www.loc.gov/marc/bibliographic/bd264.html) | PublicationInfo.Location | |
| Alma | [MARC 260$b](https://www.loc.gov/marc/bibliographic/bd260.html) | PublicationInfo.Name | |
| Alma | [MARC 264$b](https://www.loc.gov/marc/bibliographic/bd264.html) | PublicationInfo.Name | |
| Alma | [MARC 260$c](https://www.loc.gov/marc/bibliographic/bd260.html) | PublicationInfo.Date | |
| Alma | [MARC 264$c](https://www.loc.gov/marc/bibliographic/bd264.html) | PublicationInfo.Date | |
| Alma | [MARC 260$d](https://www.loc.gov/marc/bibliographic/bd260.html) | Invalid field. Don't map | |
| Alma | [MARC 260$e](https://www.loc.gov/marc/bibliographic/bd260.html) | Don't map | |
| Alma | [MARC 260$c](https://www.loc.gov/marc/bibliographic/bd260.html) | Don't map | |
| DSpace | Keep logic | Publication.Name | note: consider future work to normalize in source or during transform |
| ASpace | Keep logic | PublicationInfo.Name | |
| GIS MIT | | PublicationInfo.Name | |
| GIS OGM | | PublicationInfo.Name | |

### Proposed mappings (Option 2)

Move some of the Alma data to other existing objects, and create a new top level `Publisher` array of string.

All sources except Alma remap to use `PublicationInfo` instead of `PublicationInformation` with no other changes at this time.

This decouples our data model more from MARC where we seem to have modeled a set of data to match 260/264 in a way that doesn't seem to map to our other sources. Additionally, we already have other places for the extra info from 260/264 to map that may be more useful than as a new Object or embedded into the original String.

GraphQL would continue to serve `PublicationInformation`, but replace it with the data in the new field `Publisher`. The deprecation notice would explain that it is not a 1:1 mapping of the old field and what aspects have been moved to additional fields.


| Source | Mappings | TIMDEX Field | Notes |
| --- | --- | --- | --- |
| Alma | [MARC 260$a](https://www.loc.gov/marc/bibliographic/bd260.html) | Location.kind = Publisher Location.value=260$a | |
| Alma | [MARC 264$a](https://www.loc.gov/marc/bibliographic/bd264.html) | Location.kind = Publisher Location.value=264$a | |
| Alma | [MARC 260$b](https://www.loc.gov/marc/bibliographic/bd260.html) | Publisher | |
| Alma | [MARC 264$b](https://www.loc.gov/marc/bibliographic/bd264.html) | Publisher | |
| Alma | [MARC 260$c](https://www.loc.gov/marc/bibliographic/bd260.html) | Dates.kind=PublicationDate |  (this may already happen?) |
| Alma | [MARC 264$c](https://www.loc.gov/marc/bibliographic/bd264.html) | Dates.kind=PublicationDate |  (this may already happen?) |


## Decision

Coming soon

## Consequences

Either option will provide more normalized/consistent data. By ensuring we have a field that represents just the publisher name -- either via `PublicationInfo.name` or `Publisher` -- we will be able to add an additional mapping of `keyword` and allow for aggregation in OpenSearch/GraphQL/consuming applications such as TIMDEX UI.
