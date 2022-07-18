from transmogrifier.sources.dspace_dim import DspaceDim


class Whoas(DspaceDim):
    """Whoas transformer class."""

    @classmethod
    def valid_content_types(cls, content_type_list: list[str]) -> bool:
        """
        Validate a list of content_type values from a Dspace DIM XML record.

        Overrides the base DSpaceDim.valid_content_types() method.

        Args:
            content_type_list: A list of content_type values.
        """
        unaccepted_content_types = [
            "Article",
            "Authority List",
            "Book",
            "Book chapter",
            "Course",
            "Preprint",
            "Presentation",
            "Technical Report",
            "Thesis",
            "Working Paper",
        ]
        if all(item in unaccepted_content_types for item in content_type_list):
            return False
        else:
            return True
