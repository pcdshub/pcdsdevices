tag_to_explanation = {
    'protected': 'May require additional privileges to change.',
}


def get_valid_tags():
    """Return a list of all valid variety tags."""
    return list(tag_to_explanation)


def explain_tag(tag_name):
    """Return a user-friendly explanation of a tag's meaning."""
    return tag_to_explanation[tag_name]
