# Decision Log

## 2025-02-11: RAG Architecture and Infrastructure

### Context

Have Shadowrun PDF rulebooks and want to query them with natural language. Already running Ollama in Docker on a homelab machine (managed via `personal-homelab` repo at `/home/gaze/projects/github-GabrielDCelery/personal-homelab`). The homelab has an NVIDIA GPU.

Goal: Build a RAG system that can answer questions about Shadowrun lore.

### RAG Stack Options Considered

| Option                   | Pros                                                                     | Cons                                |
| ------------------------ | ------------------------------------------------------------------------ | ----------------------------------- |
| **LangChain + ChromaDB** | Well-documented, good Ollama integration, simple file-based vector store | Abstraction overhead                |
| LlamaIndex               | Purpose-built for RAG                                                    | Similar to LangChain, less familiar |
| Custom with FAISS        | More control                                                             | More work, fewer features           |
| Haystack                 | Solid option                                                             | Less Ollama-native                  |

**Decision:** LangChain + ChromaDB - good balance of simplicity and features, ChromaDB needs no extra container.

### Embedding Model Options

| Option                        | Pros                               | Cons                                   |
| ----------------------------- | ---------------------------------- | -------------------------------------- |
| **Ollama nomic-embed-text**   | Unified stack, runs on homelab GPU | Network hop for embeddings             |
| Ollama mxbai-embed-large      | Higher quality embeddings          | Shorter context (512 vs 8192)          |
| sentence-transformers locally | Fast, no network                   | Different runtime, CPU-bound on laptop |

**Decision:** Ollama `nomic-embed-text` - keeps everything on the homelab GPU, 8192 token context good for longer chunks.

### Containerization Options

| Option                                            | Pros                                    | Cons                                                      |
| ------------------------------------------------- | --------------------------------------- | --------------------------------------------------------- |
| **Single RAG container, separate from Ollama**    | Clean separation, iterate independently | Two compose files                                         |
| Add RAG to homelab compose                        | All containers in one place             | Couples infrastructure with application code              |
| No container                                      | Simpler                                 | Dependency management issues, marker-pdf has complex deps |
| Microservices (separate ingest, query, vector DB) | Flexible                                | Overkill for personal project                             |

**Decision:** Single container for RAG app, connects to existing Ollama. Keeps `personal-homelab` repo focused on infrastructure, this repo focused on application.

### Where to Run the RAG

| Option           | Pros                                             | Cons                                     |
| ---------------- | ------------------------------------------------ | ---------------------------------------- |
| **Homelab only** | Has GPU, more powerful, all compute in one place | Need to deploy                           |
| Laptop only      | No deployment                                    | Weaker hardware, Ollama is remote anyway |
| Both             | Flexibility                                      | Unnecessary complexity                   |

**Decision:** Run on homelab. Develop on laptop, deploy via script.

### Data Storage Options

| Option                                  | Pros                                | Cons                                        |
| --------------------------------------- | ----------------------------------- | ------------------------------------------- |
| **External path `/srv/shadowrun-rag/`** | Clean, outside repo, easy to backup | Need to set up on homelab                   |
| In repo                                 | Simple                              | Large files, copyright concerns, bloats git |
| Named Docker volumes                    | Container-native                    | Harder to inspect and backup                |

**Decision:** External path at `/srv/shadowrun-rag/` with subdirs for `pdfs/`, `extracted/`, and `chroma_db/`. Mounted into container as volumes.

### Deployment Workflow Options

| Option                                | Pros                                   | Cons                                      |
| ------------------------------------- | -------------------------------------- | ----------------------------------------- |
| **Git push + SSH deploy script**      | Simple, version controlled, repeatable | Manual trigger                            |
| GitHub Actions auto-deploy            | Fully automated                        | Overkill, needs homelab exposed to GitHub |
| Manual SSH every time                 | No script to maintain                  | Error-prone, tedious                      |
| Build image locally, push to registry | Production-like                        | Need registry, slower iteration           |

**Decision:** Git push + `deploy.sh` script that SSHs to homelab, pulls, builds, and restarts. Simple and good enough for personal use.

### Repo Separation

**Question:** Should RAG code live in `personal-homelab` repo or separate?

| Option                       | Pros                                                | Cons                                  |
| ---------------------------- | --------------------------------------------------- | ------------------------------------- |
| **Separate repo (this one)** | Clean separation of concerns, independent iteration | Two repos to manage                   |
| In homelab repo              | Everything in one place                             | Mixes infrastructure with application |

**Decision:** Keep separate. `personal-homelab` manages infrastructure and shared services (Ollama, Glances). This repo is a standalone application that consumes those services.

---

## 2025-02-11: AI Context File Structure

### Context

Want to preserve project context and decisions so future Claude sessions can pick up without re-hashing discussions.

### Options Considered

| Option                        | Pros                                        | Cons                                   |
| ----------------------------- | ------------------------------------------- | -------------------------------------- |
| **CLAUDE.md + .claude/docs/** | Auto-read summary + detailed reference docs | Two places to maintain                 |
| CLAUDE.md only                | Simple, one file                            | Gets bloated with decisions            |
| README.md                     | Human-readable too                          | Not Claude-specific, different purpose |
| Code comments only            | Close to code                               | Scattered, no overview                 |

**Decision:**

- `CLAUDE.md` at project root - concise current state, auto-read by Claude Code
- `.claude/docs/decisions.md` - detailed decision log (this file)
- `README.md` - human-focused quick start (separate concern)

---

## Template for Future Decisions

```markdown
## YYYY-MM-DD: Decision Title

### Context

What situation or problem prompted this decision?

### Options Considered

| Option   | Pros | Cons |
| -------- | ---- | ---- |
| Option A | ...  | ...  |
| Option B | ...  | ...  |

### Decision

What we chose and the primary reasoning.
```
