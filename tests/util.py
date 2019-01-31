
import mock
from collections import namedtuple

Result = namedtuple("Result", ["status_code"])


def side_effect(*args, **kwargs):
    return Result(200)


class MockGet():
    def __init__(self):
        self.call_counter = 0
        self.calls = []
        self.get = mock.patch('sxapi.low.BaseAPI.get')
        self.get.side_effect = side_effect

    def __enter__(self):
        return self.get.__enter__()

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.get.__exit__()

    def calls(self):
        return self.get.call_args_list


class MockPost():
    def __init__(self):
        self.call_counter = 0
        self.calls = []
        self.post = mock.patch('sxapi.low.BaseAPI.post')
        self.post.side_effect = side_effect

    def __enter__(self):
        return self.post.__enter__()

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.post.__exit__()

    def calls(self):
        return self.post.call_args_list


class MockPut():
    def __init__(self):
        self.call_counter = 0
        self.calls = []
        self.put = mock.patch('sxapi.low.BaseAPI.put')
        self.put.side_effect = side_effect

    def __enter__(self):
        return self.put.__enter__()

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.put.__exit__()

    def calls(self):
        return self.put.call_args_list
