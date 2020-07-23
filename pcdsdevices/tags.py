tag_to_explanation = {
    'protected': 'May require additional privileges to change.',
    'confirm': 'User should confirm changes.',
}


def get_valid_tags():
    """Return a set of all valid variety tags."""
    return set(tag_to_explanation)


def explain_tag(tag_name):
    """Return a user-friendly explanation of a tag's meaning."""
    return tag_to_explanation[tag_name]
