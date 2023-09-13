# 1. Dedicated Transformation Methods for each TimdexRecord Field

Date: 2023-09-12

## Status

Proposed

## Context

Currently, all transformations in Transmogrifier extend the base `Transformer` class.  This base class has a handful of methods that transformations extending this class optionally, or are required to, extend.

The most heavily used and customized method is `get_optional_fields()`.  This method is functionally the entrypoint into a transformation’s meaningful and unique logic for that source.  This method has historically been organized as a block of imperative code that works through each `TimdexRecord` field, commenting on those skipped, eventually returning a dictionary of mapped values from the source record.

In some transformations, where the logic was complex for a given field, it was broken out into a dedicated, standalone method.  In this way, there is already an emerging convention of breaking field-specific logic into a field-specific method.

Acknowledging this approach has been very successful for sources to date, it has also presented some issues:

  * there are some hardcoded assumptions about the relationship of unique identifiers to accessible source URLs defined in methods not designed to be overridden
  * there is an emerging pattern (as mentioned above) to breakout complex logic into methods, but is not consistently applied in naming or approach across sources
  * extending a base transformers can be tricky if the `get_optional_fields()` is complex or reused variables across fields
    * having functionally a single entrypoint like `get_optional_fields()` limits inheritance, without adjusting other transformations, to a single parent transformation
  * documentation for handling a particular field, unless broken out into a standalone method, was confined to inline comments
  * testing transformations requires testing the full, final outputted record that `get_optional_fields()` contributes to

Additionally, there has been a desire to document how a source is mapped from the original "raw" record into a TIMDEX record.  The `get_optional_fields()` approach does not lend itself well to documentation as it relies heavily on inline comments and/or ad-hoc methods to breakout complex logic.  If every transformation had methods dedicated to particular fields, thereby providing a space for docstrings to explain the logic of that field handling, this might eventually support programmatic documentation of how fields are mapped for a source.

Moving to a method-per-field approach will also allow for more granular logging.

### Transformation Inheritance

Something alluded to above but warrants a bit more discussion is how refactoring to have one method per field, might better support transformation class inheritance.  

Currently, extending another transformation usually means accepting its `get_optional_fields()` approach, and if methods are defined in _that_, overriding those for more specific behavior.   The limitation here is that a) those hooks might not exist which would require modifying that "parent" transformation, and b) when they are, it's understandably inconsistent across different transformations.

In a situation where methods are defined targeting specific `TimdexRecord` fields, it would be straight-forward to extend transformations as you'd know precisely which field logic (methods) you'd like to keep or override.

And, you could extend _multiple_ classes with the same understanding; based on [python's MRO](https://www.python.org/download/releases/2.3/mro/), the classes extended would provide those field methods in predictable pattern of defining / overriding.

## Decision

### 1- Refactor the base `Transformer` class to have all `TimdexRecord` fields as dedicated methods

At the time of writing, the `TimdexRecord` has 30 fields:

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
    * `publication_information`
    * `related_items`
    * `rights`
    * `subjects`
    * `summary`

The base `Transformer` class will have a dedicated method for each of these 30 `TimdexRecord` fields, providing a clear and modular approach to defining logic for setting those fields. 

The required fields will be an `@abstractmethod`, meaning any extending classes will be required to define them.

The rest of the optional fields will receive an `@optional_field("<FIELD_NAME>")` decorator that will identify them as a) methods meant to parsing data for a given field, and b) the name of that field.  Using a decorator provides a few of benefits:

1. It can be programmatically determined which transformations define logic, for which fields, even into inheritance
2. Hard-coding method-to-field invocations, or using method naming conventions, are not needed
3. Decorators could eventually pass more information to methods if needed (e.g. state)
4. Self-documenting that methods have an explicit purpose

From there, transformations will extend `Transformer` and override methods for specific fields, with logic specific to that transformation.  Multiple inheritance is also simplified in this approach, where extending classes continue to refine the behavior for a specific target field.

### 2- Refactor pre-existing transformations to use this new approach

With the new structure in place, refactor pre-existing source transformations to use it.  This may include revisiting some of the transformation inheritance if there is an opportunity for smaller, intermediate transformations that could be combined and used (as discussed in "Transformation Inheritance" above).

The end goal should be transformations that are identical to the original versions, only the structure of the transformations will have changed in this first pass.

### 3- Refactor tests to unit test the field methods where possible

With dedicated methods for each field, it will be possible to refactor the tests to test only how that method behaves.  

For example, given source `A` a test could confirm that given an input XML record, it returns an expected value for the `TimdexRecord.dates` field by calling the method registered with `@optional_field("dates")`.

## Consequences

One consequence is that the logic for a single field should be as isolated as possible.  While it's possible that logic may require more than just the source XML record, e.g. the results of _another_ field, that should be minimized where possible.  

While a concerted effort will be made, for each source, to have the post-refactor record be identical to the pre-refactor record, it's possible there may be changes that pre-existing tests are not picking up.  



