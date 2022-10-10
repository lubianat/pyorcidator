from typing import List, Optional

from pydantic import BaseModel, Field

import requests
import pystow
import json
from pathlib import Path

HERE = Path(__file__).parent.resolve()
EXAMPLE_PATH = HERE.joinpath("charlie_orcid.json")


class OrcidIdentifier(BaseModel):
    uri: str
    path: str
    host: str


class Preferences(BaseModel):
    locale: str


class ValueStr(BaseModel):
    value: str


class ValueInt(BaseModel):
    value: int


class Source(BaseModel):
    source_orcid: OrcidIdentifier = Field(alias="source-orcid")
    source_client_id: Optional[str] = Field(alias='source-client-id')
    source_name: ValueStr = Field(alias='source-name')


class OtherName(BaseModel):
    path: str
    visibility: str
    content: str
    created_date: ValueInt = Field(alias="created-date")
    last_modified_date: ValueInt = Field(alias="last-modified-date")
    source: Source


class OtherNames(BaseModel):
    path: str
    last_modified_date: ValueInt = Field(alias="last-modified-date")
    other_name: List[OtherName] = Field(alias="other-name")


class PersonName(BaseModel):
    path: str
    created_date: ValueInt = Field(alias="created-date")
    last_modified_date: ValueInt = Field(alias="last-modified-date")
    given_names: ValueStr = Field(alias="given-names")
    family_name: ValueStr = Field(alias="family-name")
    credit_name: ValueStr = Field(alias="credit-name")
    visibility: str


class ExternalIdentifier(BaseModel):
    type: str = Field(alias="external-id-type")
    value: str = Field(alias="external-id-url")
    url: ValueStr = Field(alias="external-id-url")


class ExternalIdentifiers(BaseModel):
    path: str
    last_modified_date: ValueInt = Field(alias="last-modified-date")
    external_identifier: List[ExternalIdentifier] = Field(alias='external-identifier')


class Person(BaseModel):
    path: str
    last_modified_date: ValueInt = Field(alias="last-modified-date")
    name: PersonName
    other_names: OtherNames = Field(alias="other-names")
    external_identifiers: ExternalIdentifiers = Field(alias="external-identifiers")


class Response(BaseModel):
    path: str
    orcid_identifier: OrcidIdentifier = Field(alias="orcid-identifier")
    preferences: Preferences
    person: Person


def get_orcid_data(orcid: str) -> Response:
    # From https://pub.orcid.org/v3.0/#!/Public_API_v2.0/viewRecord
    # url = "https://pub.orcid.org/v2.0/"
    res_json = requests.get(
        f"https://orcid.org/{orcid}",
        headers={"Accept": "application/json"},
    ).json()
    return Response.parse_obj(res_json)


def main():
    if EXAMPLE_PATH.is_file():
        j = json.loads(EXAMPLE_PATH.read_text())
    else:
        j = requests.get(
            "https://orcid.org/0000-0003-4423-4370",
            headers={"Accept": "application/json"},
        ).json()
        EXAMPLE_PATH.write_text(json.dumps(j, indent=True))
    print(EXAMPLE_PATH)
    obj = Response.parse_obj(j)
    print(repr(obj))


if __name__ == '__main__':
    main()
