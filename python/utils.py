def assert_lowercase(things):
    """
        @params
            things: list of strings or characters
    """
    for thing in things:
        assert thing.islower()