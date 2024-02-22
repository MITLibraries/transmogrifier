# 2. Data Model Fields to Support "Format" and "Data Type" UI Filters

Follows: https://mitlibraries.github.io/guides/misc/adr.html

Date: 2024-02-15

## Status

Proposed

## Context

### Goal

Identify TIMDEX fields to store information about GIS resources that will support "Format" and "Data Type" UI facet filters for the GDT project.

### Overview

With the addition of geospatial data to TIMDEX, and a new "geo" focused UI, the question was raised as to what fields should be used for two new UI facet filters:

  * "Data Type"
    * values like: `[Polygon, Point, Raster, Image, ...]`
  * "Format"
    * values like: `[Shapefile, TIFF, GeoTIFF, JPEG, ...]`

This would mirror functionality in the [current "Geoweb" application](https://geodata.mit.edu/) that is slated to be sunsetted.

The source records come from a new [GeoHarvester](https://github.com/MITLibraries/geo-harvester), which normalizes geospatial metadata from a variety of formats to the
geospatial, discovery scoped metadata format [Aardvark](https://opengeometadata.org/ogm-aardvark/).  Transmogrifier then converts these Aardvark records into TIMDEX records.

Data for both UI filters will be controlled terms in the Aardvark records created by GeoHarvester:

  * UI filter "Format" from Aardvark field `dct_format_s`:
    * https://opengeometadata.org/ogm-aardvark/#format-values (e.g. "Shapefile", "GeoTIFF", "TIFF" etc.)
  * UI filter "Data Type" from Aardvark field `gbl_resourceType_sm` (from either list):
    * https://opengeometadata.org/ogm-aardvark/#resource-type-values-loc (e.g. `[Atlases, Cadastral maps, Quadrangle maps]`)
    * https://opengeometadata.org/ogm-aardvark/#resource-type-values-ogm (e.g. `[Polygon data, Raster data, Line data, Point data]`)

The first iteration mapped in the following way:
  * `TIMDEX.content_type` = "Geospatial data" (static value for all records)
  * `TIMDEX.format` = values from `Aardvark.dct_format_s`
  * `TIMDEX.subjects@kind="Subject scheme not provided"` = values from `Aardvark.gbl_resourceType_sm`

This resulted in a TIMDEX record like:
```json
{
    "content_type": "Geospatial data",
    "format": "Shapefile",
    "subjects": [
        {
            "value": "Polygon data",
            "kind": "Subject scheme not provided"
        },
        {
            "value": "Vector data",
            "kind": "Subject scheme not provided"
        }
    ]
}
```

#### 1- The static value "Geospatial data" for `content_type` removes `content_type` as an option for these other data points

It was originally thought that `content_type` was a very high level bucket, allowing various TIMDEX sources to share a facet with values like,
[Geospatial data, Language materials, Musical sound recording, Projected medium, ...].

However, on further analysis it was observed that `content_type` _could_ be a good fit for values like `Polygon data` or `Raster data`, as the long tail of the current `content_type` data shows quite a few examples
of hierarchically and thematically similar values for other sources like [Thesis, Article, Diaries, Scrapbooks, ...].  These values are concerned with the conceptual or structural makeup of the resource,
not the container or external form which field `format` is more aligned with.

#### 2- DSpace is currently the only TIMDEX source that writes to `format` with a hardcoded value `electronic resource`

Analyzing the use of `format` revealed that _only_ the DSpace source was writing to this TIMDEX field.  This obscured the possibility that some external/container oriented terms
currently found in `content_type` -- from various pre-existing TIMDEX sources -- might make more sense as `format` values.  And, that other TIMDEX sources could begin writing to this field for 
the first time.

Better understanding this, the external container values found in `Aardvark.dct_format_s` like "Shapefile" or "GeoTIFF" seems aligned with the `format` field.  And, what should
not be ignored, this results in naming parity across all hops: `Aardvark.dct_format_s --> TIMDEX.format --> UI:Format`.

#### 3- The "resource type" data (from `Aardvark.gbl_resourceType_sm`) are arguably not subjects, and furthermore do not have a qualifier that allows cherry-picking them for aggregation

While it was initially convenient to place values from `Aardvark.gbl_resourceType_sm` in `subjects`, it was generally agreed upon that they are not subjects.  Furthermore, even
with a `kind` qualifier, it would be awkward at best to access them, or at worst reduce the meaning and usefulness of `subjects` across all TIMDEX sources.

Still thinking that `content_type` was tied up with the static "Geospatial data" value, this was a primary blocker.  `content_type` is ultimately a better fit for these values, is already
multivalued, and has precedence with other source mappings like source `datacite` where a source metadata field `ResourceType.resourceTypeGeneral` maps to `content_type` (note the metadata 
field naming parity with Aaardvark).

#### 4- Where do we encode "Geospatial data" then?

Considering all above, where then _can_ we encode "Geospatial data" to differentiate 100k GIS records from 1m ebooks in Alma?  How can a user quickly cull _all_ of TIMDEX down to just records that
likely have geospatial data (i.e. GIS layers) without needing to immediately jump to much more granular distinctions like "Polygon data" or "Raster data", thereby also removing relevant records from their
search/browsing?

This might indicate an area where the TIMDEX data model could grow: adding a higher level, highly controlled, "categorical" field that would group records at this level.  An
example is Primo, which has a "Resource Type" filter which filters at this level (ignoring the naming collision of Aardvark's `gbl_resourceType_sm` field which has a narrower scope).  While 
TIMDEX is not Primo, it is also not _not_ Primo insofar as it aggregates metadata records from fairly disparate platforms and sources.  This act of aggregation might require an additional level of 
categorical hierarchy to filter records by.  

A potentially important note: we might _not_ expect to find the values/terms for this high level, categorical field in the metadata records themselves, because their descriptive focus is not 
concerned with that level of description.

Examples:
- a GIS FGDC XML file does not need to indicate "Geospatial data" anywhere in the record
- an ArchivesSpace EAD record does not need to indicate "Archival material" anywhere in the record
- Alma is trickier: MARC records often _do_ attempt to classify at this high level, and some of these have ended up in `content_type` and likely could be "pushed up" to this new field

Given the presence of `content_type` already, to model after other aggregation platforms and metadata schemas, this new field might be something along the lines of `content_class`.  These values may 
be static per TIMDEX source (e.g. ASpace = "Archival Materials", GIS = "Geospatial data") or the source's metadata records may contribute to the logic (e.g. MARC's `006` and `008` field relationship 
that might provide `content_class` level terms like ["Books", "Music", "Visual Materials", "Maps", ...]).

It is likely beyond the scope of this ADR to propose the addition of that field, but introducing it as a thought experiment takes some conceptual pressure off of `content_type` which could operate
as intended, and to some degree already is, as more granular "type" or "form" information about the resource.

## Decision

- GIS TIMDEX sources
  - continue to map Aardvark `dct_format_s` to TIMDEX `format`, driving the new "Format" UI filter
  - map Aardvark `gbl_resourceType_sm` to TIMDEX `content_type`, driving the new "Data Type" UI filter
    - this "Data Type" UI filter, pulling from `content_type`, likely only makes sense in the Geo TIMDEX UI context
    - a "Content Type" facet filter across all TIMDEX records would have values like ["Short stories", "Polygon data", "Thesis", ...] sitting next to each other
  - accept that "Geospatial data" is not an available, high level value to facet on until a field like `content_class` is modeled and added

- Other TIMDEX sources
  - DSpace
    - remove blanket `format=electronic resource` and instead derive `format` values from available `file_formats` mimetypes for friendly forms
    - e.g. `application/pdf` suggests "PDF", or `text/csv` suggests "CSV", to name a couple example
    - there are python libraries that can handle 90% of these conversions, if a friendly form is not present in the library

## Consequences

For GIS records, both the "Format" and "Data Type" UI filters will mirror those same filters in the legacy "Geoweb" system, with the same or highly similar values.

For other TIMDEX sources, given the decision outlined above, there should be little to no effect.  However, as discussed, the inability to encode "Geospatial data" may suggest that a new, higher level
TIMDEX categorical field would be beneficial, and this would require work in Transmogrifier to provide a meaningful value for this new field for all sources.