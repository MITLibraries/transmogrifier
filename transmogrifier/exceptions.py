class DeletedRecordEvent(Exception):  # noqa: N818
    """Exception raised for records with a deleted status.

    Attributes:
        timdex_record_id: The TIMDEX record ID (not the source record ID) for the record.
    """

    def __init__(self, timdex_record_id: str) -> None:
        self.timdex_record_id = timdex_record_id


class SkippedRecordEvent(Exception):  # noqa: N818
    """Exception raised for records that should be skipped.

    Attributes:
        source_record_id: The ID for the source record.
    """

    def __init__(self, message: str | None = None, source_record_id: str | None = None):
        super().__init__(message)
        self.source_record_id = source_record_id


class CriticalError(Exception):
    """Exception raised for critical errors that should terminate the run."""

    def __init__(self, message: str | None = None):
        super().__init__(message)
