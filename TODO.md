# TODO - YAML for Humans

## Active Tasks

_No active tasks_

## Recently Completed

### Bug Fix: Kubernetes Secret Type Path Delimiter Issue ✅
**Completed**: 2025-12-19
**Status**: DONE

Fixed path delimiter bug where Kubernetes Secret types containing `/` or `\` caused file write errors when outputting to a directory. See TODO-complete.md for full details.

**Files modified**:
- `src/yaml_for_humans/cli.py`
- `tests/test_k8s_filename_helpers.py`
- `CHANGELOG.md`
