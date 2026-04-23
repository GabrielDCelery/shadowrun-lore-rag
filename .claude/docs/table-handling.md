# Table Handling

Technical notes on extracting, validating, chunking, and embedding table data from Shadowrun
sourcebooks.

## The Problem

Shadowrun books are dense with stat tables — weapons, gear, skills, modifiers, cyberware costs, etc.
These are the most query-valuable content in the books. The current pipeline handles them poorly:

1. **Extraction**: marker-pdf converts tables to markdown (`| col | col |`) — this part is fine
2. **Chunking**: `MarkdownTextSplitter` cuts through tables at character boundaries, producing
   mid-table fragments with no headers — useless for retrieval
3. **Embedding**: Raw markdown table syntax is noise to embedding models trained on prose

---

## Step 1: Table Validation

Before investing in pipeline changes, validate extraction quality on the actual books.

### What to detect

**Structural issues (definitive failures):**

- Inconsistent column counts across rows
- Missing or malformed separator row (`| --- | --- |`)
- Single-column tables (likely a parse failure)
- Empty tables

**Content quality heuristics:**

- High ratio of special characters in cells (OCR garbage)
- Numeric columns containing mostly text values (merged/split cells)
- Last rows have fewer filled cells than the rest (truncated table)

### Output format

```
shadowrun_core.md line 4521: inconsistent columns (header=6, row 3 has 4)
sr5_chrome_flesh.md line 892: missing separator row
street_grimoire.md line 2103: single-column table (possible parse failure)
```

### Implementation sketch

```python
import re

def validate_tables(markdown_text: str, source_file: str) -> list[dict]:
    issues = []
    lines = markdown_text.splitlines()
    in_table = False
    table_start = 0
    header_cols = 0
    has_separator = False

    for i, line in enumerate(lines):
        is_table_row = bool(re.match(r'\s*\|', line))

        if is_table_row and not in_table:
            in_table = True
            table_start = i
            header_cols = line.count('|') - 1
            has_separator = False

        elif is_table_row and in_table:
            # Check for separator row
            if re.match(r'[\s|:-]+$', line):
                has_separator = True
                continue
            col_count = line.count('|') - 1
            if col_count != header_cols:
                issues.append({
                    "file": source_file,
                    "line": i + 1,
                    "issue": f"inconsistent columns (header={header_cols}, row={col_count})"
                })

        elif not is_table_row and in_table:
            if not has_separator:
                issues.append({
                    "file": source_file,
                    "line": table_start + 1,
                    "issue": "missing separator row"
                })
            if header_cols == 1:
                issues.append({
                    "file": source_file,
                    "line": table_start + 1,
                    "issue": "single-column table (possible parse failure)"
                })
            in_table = False

    return issues
```

---

## Step 2: Table-Aware Chunking

Replace `MarkdownTextSplitter` with a two-pass approach:

1. Parse markdown, identify table blocks (contiguous `|`-prefixed lines)
2. Extract tables as atomic units — never split mid-table
3. Prepend the nearest preceding heading for context
4. Run normal `MarkdownTextSplitter` on non-table prose sections

### Key rule

Tables stay intact even if they exceed `chunk_size`. A 2000-character table is better as one chunk
than two broken halves.

### Implementation sketch

```python
import re
from langchain_core.documents import Document

def split_markdown_preserving_tables(text: str, source: str, chunk_size: int, chunk_overlap: int):
    chunks = []
    lines = text.splitlines(keepends=True)
    prose_buffer = []
    table_buffer = []
    last_heading = ""
    in_table = False

    def flush_prose():
        prose = "".join(prose_buffer)
        if prose.strip():
            splitter = MarkdownTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            for chunk in splitter.create_documents([prose], metadatas=[{"source": source}]):
                chunks.append(chunk)
        prose_buffer.clear()

    def flush_table():
        table = "".join(table_buffer)
        if table.strip():
            content = f"{last_heading}\n\n{table}" if last_heading else table
            chunks.append(Document(page_content=content, metadata={"source": source, "type": "table"}))
        table_buffer.clear()

    for line in lines:
        is_table_row = bool(re.match(r'\s*\|', line))

        if re.match(r'#+\s', line):
            last_heading = line.strip()

        if is_table_row:
            if not in_table:
                flush_prose()
                in_table = True
            table_buffer.append(line)
        else:
            if in_table:
                flush_table()
                in_table = False
            prose_buffer.append(line)

    if in_table:
        flush_table()
    else:
        flush_prose()

    return chunks
```

---

## Step 3: Row-as-Sentence Conversion

For large stat tables, convert each row to a natural language sentence before embedding. This
significantly improves semantic matching since embedding models are trained on prose, not pipe-
delimited syntax.

### Format

Raw markdown:

```
| Ares Predator V | 8P | -1 | 9R | 725¥ |
```

Converted:

```
Ares Predator V: Damage 8P, AP -1, Availability 9R, Cost 725¥.
```

### When to apply

- Large tables (> 5 rows) with clear column headers
- Tables where rows represent distinct items (weapons, gear, skills)
- Skip small reference tables (2-3 rows) — not worth the complexity

### Implementation sketch

```python
def table_to_sentences(markdown_table: str, context_heading: str = "") -> list[Document]:
    lines = [l.strip() for l in markdown_table.strip().splitlines() if l.strip()]
    if len(lines) < 3:
        return []

    headers = [h.strip() for h in lines[0].split('|') if h.strip()]
    documents = []

    for row_line in lines[2:]:  # skip header and separator
        cells = [c.strip() for c in row_line.split('|') if c.strip()]
        if not cells:
            continue
        pairs = [f"{h} {v}" for h, v in zip(headers, cells) if v and v != '-']
        sentence = (f"{context_heading}: " if context_heading else "") + ", ".join(pairs) + "."
        documents.append(Document(
            page_content=sentence,
            metadata={"source": context_heading, "type": "table_row"}
        ))

    return documents
```

---

## Step 4: Comparative Queries (Future Work)

RAG cannot answer comparative/filtering queries ("cheapest weapon", "highest damage", "availability
under 6") — these require reasoning over all rows simultaneously.

### Planned approach: DuckDB parallel store

```
markdown tables ──→ row sentences ──→ ChromaDB  (semantic queries)
                └─→ structured rows → DuckDB    (comparative queries)
```

**Query router** detects intent:

- "stats for Ares Predator V" → ChromaDB
- "cheapest pistol under availability 6" → DuckDB (LLM generates SQL)

**Why DuckDB:**

- In-process, no extra container
- Can query directly from Python
- `llama3.1:8b` can generate basic SQL from natural language

### Table schema example

```sql
CREATE TABLE weapons (
    name TEXT,
    category TEXT,
    damage TEXT,
    ap INTEGER,
    availability TEXT,
    restriction TEXT,
    cost INTEGER,
    source TEXT
);
```

This is significant added complexity. Implement after chunking and row conversion are validated.
