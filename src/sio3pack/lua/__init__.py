import os


def get_script(name: str, templates: dict[str, str] = None) -> str:
    """
    Get the script for the given name and replace templates with the given replacements.

    :param name: The name of the script.
    :param templates: The templates to replace.
    """
    script = os.path.join(os.path.dirname(__file__), "scripts", f"{name}.lua")
    if not os.path.exists(script):
        raise FileNotFoundError(f"Script {name} not found.")
    with open(script, "r") as f:
        script = f.read()
    if templates:
        for key, value in templates.items():
            script = script.replace(key, value)
    return script


def to_lua_map(data: dict[str, str]) -> str:
    """
    Convert a dictionary to a Lua map.

    :param data: The dictionary to convert.
    """
    lua_map = "{"
    for key, value in data.items():
        lua_map += f'"{key}" = "{value}", '
    lua_map = lua_map.rstrip(", ") + "}"
    return lua_map
