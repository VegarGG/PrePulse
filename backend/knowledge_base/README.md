# PrePulse Knowledge Base

The chatbot at `/api/chat` answers product questions by reading every `.md`
file in this directory at server startup. Drop additional documents here to
extend its scope — no code changes required.

Conventions:
- One topic per file. Filenames sort alphabetically; the chatbot sees them in
  that order, so prefix with `NN_` if order matters (e.g. `01_overview.md`).
- Keep each file under ~4 KB. The full corpus is injected into the system
  prompt; total budget should stay under ~30 KB to leave room for chat
  history.
- Use plain Markdown. No frontmatter required.
- The chatbot will refuse questions that fall outside this corpus.

This README itself is **not** loaded into the corpus (the loader skips
`README.md`).
