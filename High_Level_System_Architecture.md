```
                        USER
                         │
                         ▼
              ┌─────────────────────┐
              │     APPLICATION     │
              │                     │
              │   CLI / API / UI    │
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │   REPAIR WORKFLOW   │
              │                     │
              │ Investigate         │
              │ Diagnose            │
              │ Repair              │
              │ Verify              │
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │    AGENT RUNTIME    │
              │                     │
              │ Control Loop        │
              │ State Management    │
              │ Execution Budgets   │
              │ Termination         │
              └──────────┬──────────┘
                         │
           ┌─────────────┴─────────────┐
           │                           │
           ▼                           ▼
┌────────────────────┐     ┌────────────────────┐
│   CONTEXT ENGINE   │     │    TOOL SYSTEM     │
│                    │     │                    │
│ Repository Context │     │ Tool Registry      │
│ Prompt Compilation │     │ Tool Executor      │
│ Token Management   │     │ Policy Enforcement │
└──────────┬─────────┘     └──────────┬─────────┘
           │                          │
           ▼                          ▼
┌────────────────────┐     ┌────────────────────┐
│    MODEL GATEWAY   │     │   REPO WORKSPACE   │
│                    │     │                    │
│ Local LLM          │     │ File Operations    │
│ Remote LLM         │     │ Git Operations     │
│ Model Routing      │     │ Patch Application  │
│ Structured Output  │     │ Isolated Test Runs │
└────────────────────┘     └────────────────────┘

             CROSS-CUTTING COMPONENTS

┌─────────────────────────────────────────────────┐
│ State Persistence                               │
│ Event Ledger                                    │
│ Observability                                   │
│ Evaluation & Benchmarking                       │
│ Safety & Authorization                          │
└─────────────────────────────────────────────────┘
```

---

| Component            | Responsibility                    | Fundamental concepts                 |
| -------------------- | --------------------------------- | ------------------------------------ |
| Application          | Accept tasks and present results  | CLI, APIs, application design        |
| Repair Workflow      | Define the repair lifecycle       | Orchestration, state machines        |
| Agent Runtime        | Execute the reasoning/action loop | Agent control, termination, state    |
| Context Engine       | Construct effective model inputs  | Retrieval, context engineering       |
| Model Gateway        | Abstract model inference          | LLM serving, structured outputs      |
| Tool System          | Execute validated agent actions   | Tool contracts, authorization        |
| Repository Workspace | Safely inspect and modify code    | Git, isolation, verification         |
| Persistence          | Preserve execution history        | Events, reducers, durability         |
| Evaluation           | Quantify agent capabilities       | Benchmarks, metrics, experimentation |

---

## Target Repo Structure

```
repo-repair-assistant/
│
├── pyproject.toml
├── README.md
├── .env.example
│
├── src/
│   └── repo_repair/
│       │
│       ├── app/
│       │   └── cli.py
│       │
│       ├── agent/
│       │   ├── contracts.py
│       │   ├── control_loop.py
│       │   ├── state.py
│       │   └── termination.py
│       │
│       ├── models/
│       │   ├── gateway.py
│       │   ├── contracts.py
│       │   └── providers/
│       │       ├── local.py
│       │       └── remote.py
│       │
│       ├── context/
│       │   ├── compiler.py
│       │   ├── repository_context.py
│       │   └── token_budget.py
│       │
│       ├── tools/
│       │   ├── contracts.py
│       │   ├── registry.py
│       │   ├── executor.py
│       │   └── implementations/
│       │       ├── search_code.py
│       │       ├── read_file.py
│       │       ├── apply_patch.py
│       │       └── run_tests.py
│       │
│       ├── workspace/
│       │   ├── manager.py
│       │   ├── repository.py
│       │   └── sandbox.py
│       │
│       ├── workflow/
│       │   ├── repair.py
│       │   └── verification.py
│       │
│       ├── persistence/
│       │   ├── events.py
│       │   └── store.py
│       │
│       └── evaluation/
│           ├── harness.py
│           └── metrics.py
│
├── tests/
│
├── benchmarks/
│   ├── tasks/
│   └── results/
│
└── examples/
    └── broken-python-api/
```
