def assert_lowercase(things):
    """
        @params
            things: list of string or None or character
    """
    for thing in things:
        assert thing is None or thing.islower()