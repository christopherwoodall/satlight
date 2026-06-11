from satlight.satellite_classifiers import available_classifications, classify


def test_starlink_classification():
    assert classify("STARLINK-1007", 44713) == "STARLINK"


def test_iss_by_norad_and_name():
    assert classify("ISS (ZARYA)", 25544) == "ISS"
    assert classify("SOME ALIAS", 25544) == "ISS"


def test_fallback_other():
    assert classify("RANDOM SAT", 12345) == "OTHER"


def test_available_classifications_contains_all():
    labels = available_classifications()
    assert {"STARLINK", "ISS", "OTHER"} <= set(labels)
