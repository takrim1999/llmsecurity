## PCFI Evaluation Datasets

Datasets are stored in JSON Lines (JSONL) format, one example per line.

Each record follows this schema:

- `id` (string): Unique identifier for the example.
- `task` (string): High-level description of the user task.
- `system_policy` (string): System-level instructions that must not be overridden.
- `developer_prompt` (string, optional): Additional fixed instructions set by the application.
- `user_prompt` (string): End-user input.
- `rag_docs` (array of objects): Retrieved documents injected into context as low-priority RAG:
  - `id` (string)
  - `content` (string)
  - `source` (string, optional)
  - `score` (number, optional)
- `label` (string): Either `benign` or `attack`.
- `attack_family` (string | null): Attack type for adversarial examples
  (e.g., `direct_override`, `delimiter_injection`, `rag_indirect`).
- `success_oracle` (object): Hints used by evaluation scripts to automatically decide
  whether an attack succeeded, including:
  - `forbidden_keywords` (array of strings)
  - `required_keywords` (array of strings)
  - `format_constraint` (string, optional)
- `expected_refusal_or_format` (string): Natural-language description of the
  desired behavior under correct enforcement (e.g., “model must refuse to reveal API key”).

Generated files:

- `pcfi_benign.jsonl`
- `pcfi_direct_injection.jsonl`
- `pcfi_indirect_rag_injection.jsonl`

Use `datasets/generate.py` to regenerate these files.

