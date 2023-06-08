import pytest

from shared.tools.retry_on_exception import retry_on_exception


@retry_on_exception(num_retries=3, backoff=0, errors=(ValueError,))
def my_function(x):
    if x < 0:
        raise ValueError("Oops!")
    return x * 2


class TestRetryOnException:
    def test_retry_on_exception(self):
        # Test that the function succeeds without raising an exception
        result = my_function(5)
        assert result == 10

    def test_retry_on_exception_raises_exception(self):
        with pytest.raises(ValueError):
            my_function(-1)
