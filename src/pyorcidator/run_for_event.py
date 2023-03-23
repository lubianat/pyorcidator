import click
from urllib.parse import quote
from SPARQLWrapper import SPARQLWrapper, JSON
from pyorcidator.import_info import render_orcid_qs


def get_orcids_for_event(event_qid):
    endpoint_url = "https://query.wikidata.org/sparql"

    query = f"""
    SELECT DISTINCT ?orcid WHERE {{
      wd:{event_qid} wdt:P823 ?speaker.
      ?speaker wdt:P496 ?orcid.
    }}
    """

    sparql = SPARQLWrapper(endpoint_url)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    orcids = [result["orcid"]["value"] for result in results["results"]["bindings"]]
    return orcids


@click.command(name="parse_event")
@click.option(
    "--event_qid",
    prompt="Event QID",
    help="The QID of the event you are interested in",
)
def import_orcids_from_event(event_qid: str):
    orcids = get_orcids_for_event(event_qid)

    qs = ""
    for orcid in orcids:
        print(f"===== Runing for {orcid} ======")
        qs = render_orcid_qs(orcid)
        quoted_qs = quote(qs.replace("\t", "|").replace("\n", "||"), safe="")
        url = f"https://quickstatements.toolforge.org/#/v1={quoted_qs}\\"
        print(qs)
        print(url)
        mock = input("Enter anything to continue.")


if __name__ == "__main__":
    import_orcids_from_event()
