"""Pydantic models for task.toml. Structure only; file checks live in validate.py."""

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

SEMVER = r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(-[0-9A-Za-z.-]+)?(\+[0-9A-Za-z.-]+)?$"
KEBAB = r"^[a-z0-9]+(-[a-z0-9]+)*$"
NONBLANK = r"\S"  # at least one non-whitespace character

Track = Literal["a-prompts", "b-arabic-in-code", "c-rtl-ui", "d-output-language"]
Dialect = Literal["levantine", "gulf", "egyptian", "maghrebi", "iraqi", "sudanese", "other"]


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Prompt(_Model):
    file: str = Field(pattern=NONBLANK)
    lang: Literal["en", "ar"]
    kind: Literal["en", "msa", "dialect", "code-switched"]
    dialect: Dialect | None = None
    script: Literal["arabic", "latin"] = "arabic"
    review_status: Literal["draft", "native_authored", "native_reviewed"]

    @model_validator(mode="after")
    def _dialect_iff_kind(self) -> Self:
        if (self.kind == "en") != (self.lang == "en"):
            raise ValueError("lang: kind 'en' requires lang 'en'; other kinds require lang 'ar'")
        if self.script == "latin" and self.lang != "ar":
            raise ValueError(
                "script: 'latin' requires lang 'ar' (Arabizi is Arabic in Latin letters)"
            )
        if self.kind == "dialect" and self.dialect is None:
            raise ValueError("dialect: required when kind is 'dialect'")
        if self.kind != "dialect" and self.dialect is not None:
            raise ValueError("dialect: only allowed when kind is 'dialect'")
        return self


class Grader(_Model):
    type: Literal["tests", "arabic-integrity", "rtl", "language-id"]
    entry: str = Field(pattern=NONBLANK)
    timeout_seconds: int = Field(gt=0)


class Solutions(_Model):
    reference: str = Field(pattern=NONBLANK)
    known_bad: str = Field(pattern=NONBLANK)


class TaskSpec(_Model):
    schema_version: Literal["1"]
    id: str = Field(pattern=KEBAB)
    version: str = Field(pattern=SEMVER)
    track: Track
    title: str = Field(pattern=NONBLANK)
    difficulty: Literal["easy", "medium", "hard"]
    split: Literal["public", "heldout"]
    pair_id: str | None = Field(default=None, pattern=NONBLANK)
    stack: list[str] = []
    prompts: dict[str, Prompt]
    grader: Grader
    solutions: Solutions

    @model_validator(mode="after")
    def _prompt_coverage(self) -> Self:
        langs = {p.lang for p in self.prompts.values()}
        arabic_script = any(p.lang == "ar" and p.script == "arabic" for p in self.prompts.values())
        if "en" not in langs:
            raise ValueError("prompts: needs at least one variant with lang = 'en'")
        if not arabic_script:
            raise ValueError(
                "prompts: needs at least one variant with lang = 'ar' and script = 'arabic' "
                "(Arabizi alone does not count)"
            )
        return self
