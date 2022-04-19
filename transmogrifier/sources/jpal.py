from transmogrifier.datacite import create_kwargs_from_datacite_xml
from transmogrifier.models import TimdexRecord


def create_timdex_json_from_jpal_xml(
    datacite_xml_string: str,
) -> TimdexRecord:
    """
    Create a TimdexRecord instance from JPAL Datacite XML.
    Args:
        datacite_xml_string: A Datacite XML string to parse for values.
    """
    kwargs = create_kwargs_from_datacite_xml(
        datacite_xml_string,
        "https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:",
    )
    kwargs["source"] = "Abdul Latif Jameel Poverty Action Lab Dataverse"
    return TimdexRecord(**kwargs)
