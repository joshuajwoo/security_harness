# Refactor Repo

A data processing pipeline that loads CSV data, cleans it, transforms values,
and saves the result. The `process_data` function works correctly but is a
single monolithic function that needs to be refactored into smaller pieces.

## Running tests

```bash
python -m pytest test_data_pipeline.py -v
```
