import json
import urllib.parse
import urllib
from pathlib import Path

from pydantic import ValidationError

from zombuild._exception import ZombuildConfigException, ZombuildException
from zombuild._schema import write_schema
from .config import PackageModel


def is_uri_with_schema(string):
    parsed = urllib.parse.urlparse(string)
    return parsed.scheme is not None and parsed.scheme != ""


def resolve_package(project: Path | PackageModel) -> PackageModel:
    if isinstance(project, PackageModel):
        return project

    search_path = [project / "zombuild.json", project / "zombmod.json"]

    if project.is_dir():
        for path in search_path:
            if path.is_file():
                project = path

    if not project.is_file():
        e = ZombuildException(f"missing zombuild.json at project root")
        for path in search_path:
            e.add_note(f"tried: {path}")
        raise e

    package_json = json.loads(project.read_text())

    try:
        package = PackageModel(**package_json, source=project)
    except ValidationError as e:
        raise ZombuildConfigException(validation_error=e)

    schema = package.schema_reference

    if schema is not None and not is_uri_with_schema(schema):
        schema_path = Path(schema).resolve()
        if schema_path.is_relative_to(project.parent):
            write_schema(schema_path)

    return package
