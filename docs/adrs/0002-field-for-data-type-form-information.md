# 1. Field for Data Type / Form Information

Follows: https://mitlibraries.github.io/guides/misc/adr.html

Date: 2024-02-15

## Status

Proposed

## Context

### Need

Identify a pre-existing, or new, TIMDEX field to store information about GIS datasets that will support required facet filters, while also potentially serving other TIMDEX data sources.

### Overview
During a project that introduced geospatial data into TIMDEX, two new sources were added `gisogm` and `gismit`, both of which use the new Transmogrifier transformer 
`MITAardvark`. Records for these sources come from the [GeoHarvester](https://github.com/MITLibraries/geo-harvester) which produces [Aardvark metadata schema](https://opengeometadata.org/ogm-aardvark/) JSON records.    

During work on a new geospatial TIMDEX UI, the question was raised as to what fields should be used for two new required facet filters to mirror functionality in the [current Geoweb application](https://geodata.mit.edu/):

  * "Data Type"
    * values like: `[Polygon, Point, Raster, Image, etc.]`
  * "Format"
    * values like: `[Shapefile, TIFF, GeoTIFF, JPEG, etc.]`

This revealed a potential gap in the TIMDEX data model.  While the TIMDEX field `format` is a great fit for the "Format" values we expect to see in that facet filter, there does not appear to be 
an appropriate field to hold values that would populate the "Data Type" facet filter.

It is worth noting that the facet filter "Content Types", driven by the TIMDEX field `content_type`, is set statically for these records as `Geospatial data`.  This allows them to sit next to 
other TIMDEX records with `content_type` values like `[Language material, Musical sound recording, Thesis, etc.]`, thereby also removing `content_type` as a possible field for the issue at hand. 

Analysis of the source `MITAardvark` records suggests that the Aardvark field `gbl_resourceType_sm` contains the values we'll want for the facet filter "Data Type".  The 
Aardvark schema defines this field as:

> "...categories for classifying the spatial type or structure of a dataset"

In this way, the TIMDEX data model is lacking a field that can be used to describe the "spatial type or structure of a dataset".  Maybe stated more generally, a field that describes
the structure of the data _inside_ the format noted in `format`.

It is also worth noting that data values for both facets -- present in fields `dct_format_s` and `gbl_resourceType_sm` from the Aardvark records -- will be controlled values
when written by the GeoHarvester:

  * "Format" values:
    * https://opengeometadata.org/ogm-aardvark/#format-values (e.g. "Shapefile", "GeoTIFF", "TIFF" etc.)
  * "Data Type" values (from either list):
    * https://opengeometadata.org/ogm-aardvark/#resource-type-values-loc (e.g. "Atlases", "Cadastral maps", "Quadrangle maps")
    * https://opengeometadata.org/ogm-aardvark/#resource-type-values-ogm (e.g. "Polygon", "Raster", "Line", "Point")

### Possible Solutions

#### Option 1- Use `subjects` with `kind="Data Type"`

In this approach, "Data Type" values would be stored as `subjects` with `kind="Data Type"`.

Example:
```json
{
    "subjects": [
        {
            "value": "Polygon",
            "kind": "Data Type"
        },
        {
            "value": "Vector",
            "kind": "Data Type"
        }
    ]
}
```

Pros:
  * does not require a change to TIMDEX data model anywhere

Cons:
  * these "Data Type" values don't feel like subjects; they are not really _about_ the resource so much as describing its type/structure/form 


#### Option 2- Create new, multivalued string field `form`

In this approach, "Data Type" value would be stored in a new, multivalued string field `form`:

Example:
```json
{
    "form": ["Polygon", "Vector"]
}
```

Pros:
  * purely additive change to data model
  * simple, top level property makes aggregations very simple

Cons:
  * still require, and sit along next to, `literary_form` field for describing text sources as "Fiction" or "Nonfiction"


#### Option 3- Create new, multivalued objects field `form`; collapse `literary_form` into this

In this approach, "Data Type" value would be stored in a new, multivalued object field `form`:

Example:
```json
{
    "form": [
        {
            "value": "Polygon",
            "kind": "Data Type"
        },
        {
            "value": "Vector",
            "kind": "Data Type"
        }
    ]
}
```

Pros:
  * allows collapsing of `literary_form` field; noting some shared sentiment that this field might be too source-specific for TIMDEX
  * like other object fields, leaves the door open for adding a `uri` property at a later time

Cons:
  * would require reworking the transformations + re-indexing any sources that use `literary_form`
  * nested field type, a bit harder to query for aggregations

#### Option 4 - Use `file_formats` for current `format` values and `format` for Data Type values

In this approach, the current `MITAardvark.format` values would shift to the previously unused `MITAardvark.file_formats` property and the Data Type values would be stored in `MITAardvark.format`

Example:
```json

{
    "content_type": "Geospatial data",
    "format": ["Polygon", "Point", "Raster", "Image"],
    "file_formats": ["Shapefile", "TIFF", "GeoTIFF", "JPEG"]
}
```

Pros:
  * does not require TIMDEX data model changes

Cons:
  * `file_formats` has previously only stored MIME type values, such as `application/pdf`
  * may require explanation of the facet mapping in the UI documentation
  * may require updates of other transform classes for consistency

## Decision

It is proposed to move forward with **Option 3: Create new, multivalued objects field `form`; collapse `literary_form` into this**. 

This approach would:
  * readily support the "Data Type" values needed by the new geospatial TIMDEX UI's facet filters
  * cover values currently stored in the field `literary_form` which may have been too source-specific to begin with
  * allow future application of URIs
  * support other "form"-like values we may not have encountered yet, with the flexibility and additional granularity of the `kind` qualifier 

The decision to add a new `form` field would rely on a shared and documented understanding of how `form` differs from `format`.  Proposing a couple
shorthand distinctions:

  * `format`:
    * describes the _external_ nature of the resource
    * e.g. TIFF, Shapefile, PDF, Print book, Electronic resource, Online archival collection, etc.
  * `form`
    * describes the _internal_ structure or conceptual arrangement of the resource, regardless of its external format
    * e.g. Polygon, Image, Raster, Nonfiction, Novel, Textbook, Poetry, Biography, Reference Book, Personal papers, Organizational records, etc.

## Consequences

Adding this new field to the TIMDEX data model would require the following work and changes:
  * Transmogrifier
    * `TimdexRecord` class definition
    * any pre-existing applications of the `literay_form` field
    * check if `subjects@kind=Genre/Form` applied anywhere, if so, consider `form`
  * timdex-index-manager (TIM)
    * Opensearch mapping
  * re-run an sources that used `literary_form`
  * dynamically apply mapping update to ALL indexes to include new field `form`
    * NOTE: this action was needed already for the new field `locations.geoshape`
  * GraphQL API
    * add `form` to schema
    * add to documentation
    * deprecate `literary_form` field