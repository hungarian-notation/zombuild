from zombuild.config import PackageModel


import json
from pathlib import Path


def write_schema(path: Path):
    json_schema = PackageModel.model_json_schema()
    path.write_text(json.dumps(json_schema, indent=2))
