# Test suite documentation

## Description

- The following tests are discovered and ran using `pytest`
- Test files should be named `test_<something>.py`
- It tries to mimic the directory structure of the `managedtenants/` package but this is not a hard requirement
- Two special directories are:
  - `testdata/` :: contains mock data to load an `Addon` from the filesystem
  - `testutils/` :: python module to help running tests

## `conftest.py`

Pytest utilizes this file to configure itself. It currently sets some `hypothesis` profiles depending on where the test suite is executed (local machine, CI, nightly build, etc.).

**Override default settings**

It is always possible to [override any settings for a single test](https://hypothesis.readthedocs.io/en/latest/settings.html#settings):

```python
from hypothesis import given, settings

@given(integers())
@settings(max_examples=500)
def test_this_thoroughly(x):
    pass
```
