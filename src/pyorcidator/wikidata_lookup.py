import requests
from SPARQLWrapper import JSON, SPARQLWrapper

__all__ = [
    "query_wikidata",
    "search_wikidata",
    "parse_wikidata_result",
]


def query_wikidata(query):
    """Run a query against wikidata."""
    sparql = SPARQLWrapper(
        "https://query.wikidata.org/sparql",
        agent="PyORCIDator (https://github.com/lubianat/pyorcidator)",
    )
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    return results["results"]["bindings"]


def search_wikidata(search_term):
    """
    Looks up string for institution on Wikidata
    """

    base_url = "https://www.wikidata.org/w/api.php"
    payload = {
        "action": "wbsearchentities",
        "search": search_term,
        "language": "en",
        "format": "json",
        "origin": "*",
    }

    res = requests.get(base_url, params=payload)

    parsed_res = parse_wikidata_result(res.json())
    return parsed_res


def parse_wikidata_result(wikidata_result):
    # Workaround for when finding no results
    if len(wikidata_result["search"]) == 0:
        return {
            "id": "NONE",
            "label": "NONE",
            "description": "NONE",
            "url": f"https://www.wikidata.org/wiki/NONE",
        }

    first_item = wikidata_result["search"][0]

    return {
        "id": first_item["id"],
        "label": first_item["label"],
        "description": first_item["description"],
        "url": f"https://www.wikidata.org/wiki/{first_item['id']}",
    }
