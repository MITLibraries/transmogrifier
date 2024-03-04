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
  "publicationInfo": [
    {
      "name": "String",
      "location": "String",
      "date": "String (ideally dates would be dates... but that may be out of scope for now)"
    }
  ]
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

Create a new top level `Publisher` array of strings.

All sources (including Alma) would begin to write the publisher name to the new multivalued string `Publisher` field.

Additionally, any sources (most commonly Alma) that have publisher date or location information, could extract and write that data to other appropriate fields, e.g. `Dates` or `Locations` with a qualifier like `@kind="Published"`.

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

### Proposed mappings (Option 3)

This option is a combination of Option 1 and 2.

In this scenario:
- **From Option 1**: all sources write publisher information to a multivalued object field `PublicationInfo` with fields like `[name, date, location, etc.]` 
  - there is no normalization or parsing of the data; strings are written as found from the original record
- **From Option 2**: where data is available (most commonly with Alma) sources extract date and location from the publisher information and write those values to `Dates` and `Locations` respectively, with a `@kind=Publisher` qualifier
  - in the case of dates, we _could_ normalize and validate the date string to ensure it's a valid and meaningful Opensearch date

Advantages of this option:
- all information for a specific publisher (e.g. name, date, location) is contextualized together as a complex object under `PublicationInfo`
  - e.g. we can know "the published date via the 'Great Writings' publisher is 1930" 
- for TIMDEX UI search and item pages, and GraphQL aggregations, there is no need to dig into complex objects
  - simply look to `Dates` or `Locations` for that information where this data has been duplicated
- logic for extracting dates and locations from publisher information could be shared across all Transmogrifier sources
  - e.g. it could be an automatically applied, secondary step after the `PublicationInfo` objects are created, pulling from `PublicationInfo.date` and `Publication.location`
  - allows for more thorough date parsing for `Dates` entries, without losing meaningful strings from the source record that can remain in the `PublicationInfo` object

Example record:
```json
{
  "publication_info": [
    {
      "name": "Great Writings",
      "date": "1930",
      "location": "Bend, OR"
    },
    {
      "name": "Amazon Reprints",
      "date": "2020",
      "location": "Seattle, WA"
    },
    {
      "name": "Ebooks Inc.",
      "date": "Circa 2023?"
    }
  ],
  "dates": [
    {
      "kind": "Published",
      "value": "1930"
    },
    {
      "kind": "Published",
      "value": "2020"
    }
  ],
  "locations": [
    {
      "kind": "Published",
      "value": "Bend, OR"
    },
    {
      "kind": "Published",
      "value": "Seattle, WA"
    }
  ]
}
```
- note that bad or missing data from publisher "Ebooks Inc." is skipped for `dates` and `locations` extraction

This avoids some subtle but potentially confusing scenarios:

- **Option 1**: a user clicks date facet "1910" in search UI but does not see "1910" under "Dates" in the item page
  - **Reason**: the UI item page didn't know it should reach into `PublicationInfo` objects for dates to show under "Dates", as this was custom logic applied to GraphQL aggregations and search facets
  - **Option 3 fix**: GraphQL, UI search, and UI item pages all pull publishers from publishers, dates from dates, locations from locations, etc., no logic required

- **Option 2**: a user is viewing an item page for the geospatial record "Fires in 1999 Dataset" but sees a strange "2020" under the "Dates" section
  - **Reason**: the item page "Publisher" section only shows "GIS Pro Inc.", as "2020" was decoupled from the publisher (`Date` object would contain `@kind=Published` qualifier, but we'd need to then include that in the item page)
  - **Option 3 fix**: the "Publisher" section in the item page clearly also shows "2020", because still part of a complex object, thereby contextualizing that date

Option 3 achieves data where and when needed, and with the appropriate amount of context, by _extracting and duplicating_ some data like dates and locations:  

- a user wants details about a publisher, look at full and complex `PublicationInfo` object in the record
- the API or UI wants to pull all meaningful dates or locations from a record, look to the `Dates` or `Locations` fields

In either situation, no additional logic, mapping, or documentation is needed. 

## Decision

Coming soon

## Consequences

Either option will provide more normalized/consistent data. By ensuring we have a field that represents just the publisher name -- either via `PublicationInfo.name` or `Publisher` -- we will be able to add an additional mapping of `keyword` and allow for aggregation in OpenSearch/GraphQL/consuming applications such as TIMDEX UI.
