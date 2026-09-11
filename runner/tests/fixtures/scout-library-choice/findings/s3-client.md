# Findings: s3-client

**Brief**: Which S3-compatible Python client library fits our async/size/maintenance constraints?
**Status**: complete
**Date**: 2025-01-15

## Answer

`minioclient` fits all constraints. `boto3` fails the size constraint (28MB); `aioboto` is unmaintained (last commit 11 months ago).

## Comparison

| Option | Fits constraints? | Key tradeoff | Evidence |
| --- | --- | --- | --- |
| minioclient 7.2 | yes | smaller community, but API is S3-compatible | PyPI: 1.2MB, async since v7, last commit 12d ago |
| boto3 1.34 | no (size) | 28MB installed; no native async (needs aiobotocore) | PyPI metadata |
| aioboto 0.9 | no (maintenance) | last commit 2024-02-03; open CVE unfixed | GitHub insights |

## Recommendation

minioclient — only option that satisfies all four constraints simultaneously.

## Notes

- Verified MinIO compat: minioclient README lists MinIO as primary target
- Checked async: `minioclient.aio` module since v7.0.0 (2024-06-01)
- No C extensions: pure Python (confirmed via setup.cfg `ext_modules = []`)
