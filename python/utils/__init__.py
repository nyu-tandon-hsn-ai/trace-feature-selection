def assert_lowercase(things):
    """
        @params
            things: list of strings or characters
    """
    for thing in things:
        assert thing.islower()

def assert_all_different(things):
    """
        @params
            things: list of objects
    """
    assert len(things) == len(set(things))