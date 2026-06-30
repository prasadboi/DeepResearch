#!/usr/bin/env python3
"""Lightweight document quality checks for LitGraph build-control docs."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = [
    'CLAUDE.md',
    '.github/copilot-instructions.md',
    'project_control/current_milestone.yaml',
    'docs/00_PRODUCT_BRIEF.md',
    'docs/01_ARCHITECTURE.md',
    'docs/02_GLOBAL_INVARIANTS.md',
    'docs/03_MILESTONE_GATES.md',
    'docs/04_TASK_SPECS.md',
    'docs/05_TESTING_AND_EVALUATION.md',
    'docs/06_DATA_AND_SCHEMA_CONTRACTS.md',
    'docs/07_MCP_TOOL_CONTRACT.md',
    'docs/08_BENCHMARKING_AND_ASTABENCH_PATH.md',
    'docs/09_CLOUD_AND_OPERATIONS.md',
    'docs/10_COPILOT_TASK_PROMPT_TEMPLATE.md',
    'docs/11_HUMAN_REVIEW_CHECKLIST.md',
    'docs/adr/TEMPLATE.md',
]

REQUIRED_TASK_SECTIONS = [
    'Product goal',
    'Inputs',
    'Outputs',
    'Non-goals',
    'Programming invariants',
    'Construction tests',
    'Evaluation gate',
    'Human checkpoint',
]

GLOBAL_TERMS = [
    'snapshot_id',
    'schema_version',
    'canonical_paper_id',
    'MCP',
    'Non-goals',
    'Construction tests',
    'Evaluation gate',
]


def fail(msg: str) -> None:
    print(f'FAIL: {msg}')
    sys.exit(1)


def main() -> None:
    for rel in REQUIRED_FILES:
        if not (ROOT / rel).exists():
            fail(f'missing required file: {rel}')

    task_doc = (ROOT / 'docs/04_TASK_SPECS.md').read_text(encoding='utf-8')
    task_headers = re.findall(r'^### Task ([0-9]+\.[0-9]+):', task_doc, flags=re.MULTILINE)
    if len(task_headers) < 20:
        fail(f'expected at least 20 task specs, found {len(task_headers)}')

    chunks = re.split(r'^### Task [0-9]+\.[0-9]+: .*$', task_doc, flags=re.MULTILINE)[1:]
    for idx, chunk in enumerate(chunks, start=1):
        for section in REQUIRED_TASK_SECTIONS:
            if f'#### {section}' not in chunk:
                fail(f'task chunk {idx} missing section: {section}')

    combined = '\n'.join((ROOT / rel).read_text(encoding='utf-8') for rel in REQUIRED_FILES if (ROOT / rel).suffix in {'.md', '.yaml'})
    for term in GLOBAL_TERMS:
        if term not in combined:
            fail(f'missing important term across docs: {term}')

    prohibited_patterns = [
        r'build everything',
        r'arbitrary Cypher is allowed',
        r'query-time ingestion is allowed',
    ]
    lower = combined.lower()
    for pat in prohibited_patterns:
        if re.search(pat, lower):
            fail(f'prohibited phrase found: {pat}')

    print('PASS: document quality checks passed')


if __name__ == '__main__':
    main()
