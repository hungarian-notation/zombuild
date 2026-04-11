from zombuild.config.package import PackageConfig


import json
from pathlib import Path


def write_schema(path: Path):
    json_schema = PackageConfig.model_json_schema()
    path.write_text(json.dumps(json_schema, indent=2))
