"""A data model for quickstatements."""

import datetime
from typing import List, Union

from pydantic import BaseModel, Field
from typing_extensions import Annotated, Literal

__all__ = [
    "EntityQualifier",
    "DateQualifier",
    "TextQualifier",
    "Qualifier",
    "CreateLine",
    "TextLine",
    "EntityLine",
    "Line",
]


class EntityQualifier(BaseModel):
    """A qualifier that points to Wikidata entity."""

    type: Literal["Entity"] = "Entity"
    predicate: str = Field(regex=r"^[PQS]\d+$")
    target: str = Field(regex=r"^[PQS]\d+$")

    def get_target(self):
        return self.target


class DateQualifier(BaseModel):
    """A qualifier that points to a date string."""

    type: Literal["Date"] = "Date"
    predicate: str = Field(regex=r"^[PQS]\d+$")
    target: str

    def get_target(self):
        return self.target

    @classmethod
    def start_time(cls, target: Union[str, datetime.datetime]) -> "DateQualifier":
        return cls(predicate="S580", target=cls._handle_date(target))

    @classmethod
    def end_time(cls, target: Union[str, datetime.datetime]) -> "DateQualifier":
        return cls(predicate="S582", target=cls._handle_date(target))

    @staticmethod
    def _handle_date(target: Union[str, datetime.datetime]) -> str:
        if isinstance(target, str):
            return target
        elif isinstance(target, datetime.datetime):
            # See section on precision in https://www.wikidata.org/wiki/Help:Dates#Precision
            return f"+{target.isoformat()}Z"
        else:
            raise TypeError


class TextQualifier(BaseModel):
    """A qualifier that points to a string literal."""

    type: Literal["Text"] = "Text"
    predicate: str = Field(regex=r"^[PQS]\d+$")
    target: str

    def get_target(self):
        return f'"{self.target}"'


#: A union of the qualifier types
Qualifier = Annotated[
    Union[EntityQualifier, DateQualifier, TextQualifier], Field(discriminator="type")
]


class BaseLine(BaseModel):
    subject: str = Field(regex=r"^(LAST)|(Q\d+)$")
    predicate: str = Field(regex=r"^(P\d+)|(Len)|(Den)$")
    qualifiers: List[Qualifier] = Field(default_factory=list)

    def get_target(self):
        return self.target

    def get_line(self) -> str:
        """Get the quickstatement as a line."""
        parts = [self.subject, self.predicate, self.get_target()]
        for qualifier in self.qualifiers:
            parts.append(qualifier.predicate)
            parts.append(qualifier.get_target())
        return "|".join(parts)


class CreateLine(BaseModel):
    """A trivial model representing the CREATE line."""

    type: Literal["Create"] = "Create"

    def get_line(self):
        return "CREATE"


class EntityLine(BaseLine):
    """A line whose target is a string literal."""

    type: Literal["Entity"] = "Entity"
    target: str = Field(regex=r"^(Q\d+)$")


class TextLine(BaseLine):
    """A line whose target is a Wikidata entity."""

    type: Literal["Text"] = "Text"
    target: str

    def get_target(self):
        return f'"{self.target}"'


#: A union of the line types
Line = Annotated[Union[CreateLine, EntityLine, TextLine], Field(discriminator="type")]
