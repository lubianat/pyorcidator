import requests


def search_wikidata(search_term):

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

    first_item = wikidata_result["search"][0]

    return {
        "id": first_item["id"],
        "label": first_item["label"],
        "url": f"https://www.wikidata.org/wiki/{first_item['id']}",
    }
