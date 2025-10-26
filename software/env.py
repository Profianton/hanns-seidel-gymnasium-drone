from typing import TypedDict
import pathlib
import json

try:
    import pydantic as pydantic

    PYDANTIC_INSTALLED = True
except ImportError:
    PYDANTIC_INSTALLED = False


try:
    assert __file__
except Exception:
    __file__ = "env.py"


def pydantic_system(schema_dump: bool = False):
    from pydantic import TypeAdapter

    config = TypeAdapter(Config)
    schema_file_path = pathlib.Path(__file__).parent / "env.generated.schema.json"

    def write_schema():
        with open(schema_file_path, "w") as f:
            json.dump(config.json_schema(), f)

    if schema_dump:
        write_schema()

    if not schema_file_path.exists():
        write_schema()
    if env_file_path.exists():
        with open(env_file_path, "r") as f:
            d = json.load(f)
    else:
        d = {"WLAN": None}

    should_be_dict = {"$schema": str(schema_file_path.name)}
    should_be_dict.update(config.dump_python(config.validate_python(d)))
    if should_be_dict != d:
        with open(env_file_path, "w") as f:
            json.dump(
                should_be_dict,
                f,
                indent="\t",
            )


class WLANConfig(TypedDict):
    SSID: str
    PASSWORD: str


class Config(TypedDict):
    WLAN: WLANConfig | None
    WSURI: str | None


env_file_path = pathlib.Path(__file__).parent / "env.json"


def load_env() -> Config:
    if PYDANTIC_INSTALLED:
        pydantic_system()
    with open(str(env_file_path), "r") as f:
        d = json.load(f)
    return Config(d)


if __name__ == "__main__":
    pydantic_system(schema_dump=True)


env = load_env()
