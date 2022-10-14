"""A data model for quickstatements."""

import datetime
from typing import List, Optional, Union

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

    def get_target(self) -> str:
        return self.target


class DateQualifier(BaseModel):
    """A qualifier that points to a date string."""

    type: Literal["Date"] = "Date"
    predicate: str = Field(regex=r"^[PQS]\d+$")
    target: str

    def get_target(self) -> str:
        return self.target

    @classmethod
    def start_time(
        cls, target: Union[str, datetime.datetime], *, precision: Optional[int] = None
    ) -> "DateQualifier":
        return cls(predicate="P580", target=prepare_date(target, precision=precision))

    @classmethod
    def end_time(
        cls, target: Union[str, datetime.datetime], *, precision: Optional[int] = None
    ) -> "DateQualifier":
        return cls(predicate="P582", target=prepare_date(target, precision=precision))


def format_date(
    *,
    precision: int,
    year: int,
    month: int = 0,
    day: int = 0,
    hour: int = 0,
    minute: int = 0,
    second: int = 0,
) -> str:
    """Format the date in a way appropriate for quickstatements."""
    return f"+{year:04}-{month:02}-{day:02}T{hour:02}:{minute:02}:{second:02}Z/{precision}"


def prepare_date(target: Union[str, datetime.datetime], *, precision: Optional[int] = None) -> str:
    """Prepare a date for quickstatements."""
    if isinstance(target, str):
        return target
    if not isinstance(target, datetime.datetime):
        raise TypeError
    if precision is None:
        precision = 11
    # See section on precision in https://www.wikidata.org/wiki/Help:Dates#Precision
    if precision == 11:  # day precision
        return format_date(
            precision=precision, year=target.year, month=target.month, day=target.day
        )
    elif precision == 10:  # month precision
        return format_date(precision=precision, year=target.year, month=target.month)
    elif precision == 9:  # year precision
        return format_date(precision=precision, year=target.year)
    elif precision == 12:  # hour precision
        return format_date(
            precision=precision,
            year=target.year,
            month=target.month,
            day=target.day,
            hour=target.hour,
        )
    elif precision == 13:  # minute precision
        return format_date(
            precision=precision,
            year=target.year,
            month=target.month,
            day=target.day,
            hour=target.hour,
            minute=target.minute,
        )
    elif precision == 14:  # second precision
        return format_date(
            precision=precision,
            year=target.year,
            month=target.month,
            day=target.day,
            hour=target.hour,
            minute=target.minute,
            second=target.second,
        )
    else:
        raise ValueError(f"Invalid precision: {precision}")
    # No precision case:
    # return f"+{target.isoformat()}Z"


class TextQualifier(BaseModel):
    """A qualifier that points to a string literal."""

    type: Literal["Text"] = "Text"
    predicate: str = Field(regex=r"^[PQS]\d+$")
    target: str

    def get_target(self) -> str:
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
