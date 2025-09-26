
## Comment Preservation Implementation Issues 🔧 **NEEDS ARCHITECTURAL FIX**

**Current Status**: Partially implemented with CLI integration complete, but critical positioning/spacing issues.

**Broken Behavior in `tests/test-data/kustomization.yaml`:**
- `# these` (line 9) should appear directly before `labels:` (line 10) - currently misplaced
- `# this` (line 12) should be end-of-line with `includeSelectors: true` - currently appears as standalone
- `# whee` (line 17) should appear with blank line 18 preserved before `images:` (line 19) - spacing lost

**Root Cause**: Built separate comment metadata system (`CommentMetadata` class, comment-specific markers) instead of integrating with existing proven blank line preservation architecture.

**Key Insight**: Existing blank line system already correctly tracks line positions and spacing. Comments should be integrated into that system rather than building parallel infrastructure.

**Technical Context**:
- Current: Separate `CommentMetadata` class, `CommentCapturingScanner`, comment-specific markers
- Should: Extend `FormattingMetadata.empty_lines_before` to handle any line content type
- Files affected: `formatting_aware.py`, `formatting_emitter.py`, `dumper.py`, `cli.py`
- Association rule: comments always associate with next non-comment, non-blank line
- Scanner entry: `CommentCapturingScanner.scan_to_next_token()`
- Output processing: `_process_comment_markers()` function

**Solution**: Refactor to unified line preservation approach rather than parallel comment system.
