from pyorcidator.wikidata_lookup import parse_wikidata_result


def test_parsing(wikidata_api_result):

    expected = {
        "id": "Q835960",
        "label": "University of São Paulo",
        "description": "public state university in Brazil",
        "url": "https://www.wikidata.org/wiki/Q835960",
    }

    parsed = parse_wikidata_result(wikidata_api_result)

    assert parsed == expected
