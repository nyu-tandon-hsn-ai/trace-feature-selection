import numpy as np
from sklearn.preprocessing import MinMaxScaler

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

def normalize_to(data, to_low, to_high):
    """
    Normalize data

    Parameters
    ----------
    data: list[float]
    to_low: int
        Min range
    to_high: int
        Max range
    
    Returns
    -------
    `numpy.ndarray`
        Scaled data
    """

    # convert to `numpy.ndarray`
    data = np.array(data)

    # scale data
    scaled_data = MinMaxScaler(feature_range=(to_low, to_high)).fit_transform(data.reshape(-1,1)).ravel()

    # convert to int
    return scaled_data.astype(np.int32)