# 1. Field methods refactor

Date: 2024-05-14

## Status

Accepted

## Context

### Goal
Simplify the application by refactoring it to use field methods to populate a `TimdexRecord` instance.

### Background
A `TimdexRecord` contains the following fields: 

* REQUIRED
    * `source`
    * `source_link`
    * `timdex_record_id`
    * `title`

  * OPTIONAL
    * `alternate_titles`
    * `call_numbers`
    * `citation`
    * `content_type`
    * `contents`
    * `contributors`
    * `dates`
    * `edition`
    * `file_formats`
    * `format`
    * `funding_information`
    * `holdings`
    * `identifiers`
    * `languages`
    * `links`
    * `literary_form`
    * `locations`
    * `notes`
    * `numbering`
    * `physical_description`
    * `publication_frequency`
    * `publishers`
    * `related_items`
    * `rights`
    * `subjects`
    * `summary`

Currently much of the transformation logic for each source is found in the `get_optional_fields` method which extracts data for all optional fields. This results in very large methods as well as inefficient orchestration and testing. 

A field method approach would address many of these complications, where each `TimdexRecord` field has a corresponding method containing all of the logic related to extracting and formatting the values for that field. All of the required fields have dedicated field methods as well as some of the complex fields that are called by `get_optional_fields`. This refactor can be seen as an extension of that approach.

## Decision

Refactor each source transform to use dedicated methods for each field (e.g. `get_dates`,`get_contributors`, `get_title`) with associated unit tests to cover the expected data scenarios. 


## Consequences
Field methods should ultimately simplfy the source transforms, and the overall application, by providing an easily repeatable structure with method docstrings offering additional context for the more complicated logic required for some fields. 

Testing should also be significantly improved. The current testing suite is built around very large fixtures and unit tests meant to encompass the expected data scenarios for each source's records. They are not easy to parse and can be a barrier to new developers trying to understand the application. Separate tests for each field method should simplfy the testing infrastructure and make it easier to maintain.

Logging and associated analytics should also be easier to manage and provide a better view of the data transformed by this application. During orchestration of the transform, the field methods will provide a consistent and shared way of reporting errors or outlier behavior when transforming fields.

During this refactor, there should be no changes to the records produced the application. However, the code changes will benefit developers by making the application easier to maintain, extend, and test.