# Kalybrate Verification Criteria

This document explains exactly how each criterion is verified during skill evaluation.

## Code Output Criteria

### `code_extracted`
**How**: Regex pattern `r'```(\w+)?\n(.*?)```'` searches for fenced code blocks.

**Verification**: Always verified - we can definitively say whether code blocks exist.

**Pass condition**: At least one code block found in response.

**Verification note**: `"verified"`

---

### `code_compiles`
**How**: Depends on the detected language of the code block.

**Block selection**: Uses `_get_best_code_block()` which:
1. First looks for blocks tagged with compilable languages (python, py, typescript, ts, javascript, js)
2. Falls back to first block with >50 chars
3. Last resort: first block

| Language | Command | Pass Condition |
|----------|---------|----------------|
| `python`, `py` | `compile(code, '<string>', 'exec')` | No SyntaxError raised |
| `typescript`, `ts` | `tsc --noEmit --skipLibCheck {file}` | Exit code 0 |
| `javascript`, `js` | `node --check {file}` | Exit code 0 |
| Other | N/A | Cannot verify |

**Verification notes**:
- `"verified"` - Compiler ran successfully
- `"syntax error: {details}"` - Compiler found errors (verified failure)
- `"compilation error: {details}"` - Compiler found errors (verified failure)
- `"unverified - TypeScript compiler not available"` - tsc not installed
- `"unverified - Node.js not available"` - node not installed
- `"unverified - no {language} compiler available"` - Unknown language

---

### `has_type_annotations`
**How**: String pattern matching on the best code block.

**Verification**: Always verified - pattern search is deterministic.

**Pass condition**: Code contains ANY of:
- `: string`
- `: number`
- `: boolean`
- `: void`
- `: any`
- `): ` (return type annotation)
- `<T>` (generics)
- `interface ` (interface declaration)
- `type ` (type alias)

**Verification note**: `"verified"`

**Limitation**: This is a heuristic - doesn't parse AST. Could false-positive on comments containing these strings.

---

### `has_docstrings`
**How**: String pattern matching on the best code block.

**Verification**: Always verified - pattern search is deterministic.

**Pass condition**: Code contains ANY of:
- `"""` (Python docstring)
- `'''` (Python docstring)
- `/**` (JSDoc comment)

**Verification note**: `"verified"`

---

## File Output Criteria

### `file_created`
**How**: `os.listdir()` + `os.path.isfile()` on the work directory.

**Verification**: Always verified - file system check is deterministic.

**Pass condition**: At least one file with expected extension exists in work directory.

**Verification note**: `"verified"`

---

### `file_valid`
**How**: Depends on file type. Opens file with appropriate library.

| File Type | Library | Pass Condition |
|-----------|---------|----------------|
| `.xlsx` | `openpyxl.load_workbook()` | No exception raised |
| `.docx` | `docx.Document()` | No exception raised |
| `.pptx` | `pptx.Presentation()` | No exception raised |
| `.pdf` | `os.path.getsize() > 0` | File not empty |
| Other | `os.path.getsize() > 0` | File not empty |

**Verification note**: `"verified"`

---

### `has_formula` (Excel only)
**How**: Iterates all cells, checks if any cell value starts with `=`.

**Verification**: Always verified - cell inspection is deterministic.

**Pass condition**: At least one cell contains a formula (starts with `=`).

**Verification note**: `"verified"`

---

### `min_rows` (Excel only)
**How**: Counts rows where at least one cell has a non-None value.

**Verification**: Always verified.

**Pass condition**: Non-empty row count >= specified minimum.

---

### `min_columns` (Excel only)
**How**: Counts columns where at least one cell has a non-None value.

**Verification**: Always verified.

**Pass condition**: Non-empty column count >= specified minimum.

---

### `has_chart` (Excel/PowerPoint)
**How**:
- Excel: `len(ws._charts) > 0`
- PowerPoint: Iterates shapes, checks `shape.has_chart`

**Verification**: Always verified.

**Pass condition**: At least one chart object found.

---

### `min_paragraphs` (Word only)
**How**: Counts paragraphs where `text.strip()` is not empty.

**Verification**: Always verified.

**Pass condition**: Non-empty paragraph count >= specified minimum.

---

### `min_words` (Word only)
**How**: `sum(len(p.text.split()) for p in doc.paragraphs)`

**Verification**: Always verified.

**Pass condition**: Total word count >= specified minimum.

---

### `has_table` (Word/PowerPoint)
**How**:
- Word: `len(doc.tables) > 0`
- PowerPoint: Iterates shapes, checks `shape.has_table`

**Verification**: Always verified.

---

### `has_image` (Word/PowerPoint)
**How**:
- Word: Checks `doc.part.rels` for image references
- PowerPoint: Iterates shapes, checks `shape.shape_type == 13` (PICTURE)

**Verification**: Always verified.

---

### `min_slides` (PowerPoint only)
**How**: `len(prs.slides)`

**Verification**: Always verified.

**Pass condition**: Slide count >= specified minimum.

---

## Text Output Criteria

### `response_exists`
**How**: `len(response_text.strip()) > 0`

**Verification**: Always verified.

**Pass condition**: Response is not empty/whitespace-only.

---

## Verification Levels

Each task gets a `verification_level`:

| Level | Meaning |
|-------|---------|
| `full` | All criteria were actually verified (compiler ran, files inspected, etc.) |
| `partial` | Some criteria were verified, some couldn't be (e.g., no Clojure compiler) |
| `unverified` | No criteria could be verified (shouldn't happen in practice) |

## Scoring Impact

**Only verified criteria count toward the task pass rate.**

Example:
- Task has 2 criteria: `code_extracted`, `code_compiles`
- `code_extracted`: verified, passed
- `code_compiles`: unverified (no Clojure compiler)
- Result: 1/1 verified criteria passed = 100% for this task

This ensures we're honest about what we actually tested.
