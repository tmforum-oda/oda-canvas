# -------------------------------------------------- HELPER FUNCTIONS -------------------------------------------------- #


def safe_get(default_value, dictionary, *paths):
    if dictionary is None:
        return default_value
    result = dictionary
    for path in paths:
        if path not in result:
            return default_value
        result = result[path]
    return result


# -------------------------------------------------- ---------------- -------------------------------------------------- #
