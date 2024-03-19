# 1. Springshare Source Naming

Date: 2023-07-26

## Status

Approved

## Context

While working on adding two new sources to TIMDEX pipeline, there was some discussion and constraints around what source names should be used.

Both data sources are both from Springshare, Libguides and the AZ list of databases, and are retrieved via OAI-PMH.

At this time, source names are a string that accompany the records throughout the TIMDEX pipeline:
  * `transmogrifier`: defined in `transmogrifier.config.SOURCES`
    * drives what transformer class to use
    * saved to TIMDEX record as field
    * used for S3 key (folder structure + filename) 
  * `timdex-pipeline-lambdas`: defined in `lambdas.config.INDEX_ALIASES`
    * promotes a newly created index to specific aliases if configured
    * used for S3 key (folder structure + filename)
  * `timdex-index-manager`: defined in `tim.config.VALID_SOURCES`
    * prevents indexing of sources if not present in this list
    * used for index name created in OpenSearch

Two distinct areas of consideration emerged when deciding on a source name:
  * **meaningful**
    * does it suggest what the original data source is?
    * does it have value or meaning to end users of the API?
  * **technically viable**
    * does it have special characters?  are they allowed?
    * does it result in predictable S3 key naming conventions throughout?
    * is it an allowed OpenSearch index name?

## Decision

The following source names were decided on:
  * `libguides`: the Libguides data source
    * oai set: `guides`
  * `researchdatabases`: the AZ list databases
    * oai set: `az`

### `libguides` 

Pretty self-explanatory, satisfies both "meaningful" and "technically viable" requirements.

### `researchdatabases`

This one was a bit thornier.

It was suggested that `az` was not terribly helpful for understanding where the data came from, and was very unhelpful for end users.  

The first agreed upon alternative was `research_databases`.  `databases` was also floated, but could be ambiguous from the POV of an end user.

For a variety of reasons, attempting to keep these words distinct in the name failed:  `research_databases`, `research-databases`, and `researchDatabases`.  The reasons are outlined in [this Jira ticket comments](https://mitlibraries.atlassian.net/browse/TIMX-19?focusedCommentId=107019):
  * `research_databases`: index name not correctly parsed in `timdex-index-manager`
  * `research-databases`: files not saved correctly to S3 in `timdex-pipeline-lambdas`
  * `researchDatabases`: not a valid Opensearch index name

And so, the final decided upon source name was `researchdatabases`; no hyphens, underscores, or camelCasing.

## Consequences

The source name `researchdatabases` reflects some compromises that must be made for sources:
  * if the source name is meaningful to end users, it may lose fidelity about the source origin
  * if the source name is technically viable, it may lose some human readability

