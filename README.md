## Developer Performance Reviewer

A small tool that reads a developer’s public GitHub footprint and turns it into a clear, recruiter‑ready summary with actionable feedback. It looks at recent activity (commits, PRs, issues, reviews), basic quality signals (merge rate, resolution speed), and rough language/framework usage. It also adds context from the web.

### What it does

- **Pulls activity**: recent commits, PRs, issues, and reviews from GitHub’s public API
- **Spots trends**: simple month‑over‑month style deltas (e.g., “commits up 35%”)
- **PR/Issue metrics**: merge rate and median time to close
- **Language signals**: rough breakdown of languages and common frameworks
- **External context**: a quick DuckDuckGo skim for relevant mentions
- **Readable output**: a short summary suitable for a recruiter screen

### Requirements

- Python 3.10+ (macOS Sonoma and Linux tested)
- An OpenAI API key in `.env` as `OPENAI_API_KEY=...`
- Optional: a GitHub token in `.env` as `GITHUB_TOKEN=...` for higher rate limits

### Setup

```bash
cd github-reviewer
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```
OPENAI_API_KEY=your_key_here
# Optional for higher GitHub rate limits
GITHUB_TOKEN=your_github_token
```

### Run

The script currently uses a hardcoded username. Open `langchain_pipeline.py` and set the value near the bottom:

```python
username = "octocat"  # change this
```

Then run:

```bash
python langchain_pipeline.py
```

You’ll see console output and a `debug.json` written to the project root with captured search results for quick inspection.

### What to expect

- A markdown‑style profile analysis printed to the console logs
- Basic trend lines (events/commits/PRs/issues/reviews) for the last ~30 days
- Rough PR merge‑rate and median time‑to‑close estimates
- A short “recruiter‑ready” paragraph summarizing strengths

### Troubleshooting

- **Import error for `langchain_community.tools`**: ensure these are installed in your active virtualenv:

  ```bash
  pip install langchain-community duckduckgo-search
  ```

  Some environments expose DuckDuckGo under `ddg_search`. If needed, switch the import to:

  ```python
  from langchain_community.tools.ddg_search import DuckDuckGoSearchRun
  ```

  and call it with a dict, e.g. `{ "query": "...", "max_results": 5 }`.

- **PEP 668 / “externally‑managed environment”**: use a virtual environment (see Setup) instead of system Python.

- **GitHub rate limiting**: add `GITHUB_TOKEN` to `.env`.

### Notes

- This project only reads public GitHub data. Private activity isn’t considered.
- Benchmarks are coarse defaults. Treat them as rough context, not a performance rating.

### Roadmap

- [ ] CLI arg for `--username` instead of editing the file
- [ ] Save generated report to `reports/<username>.md`
- [ ] Stronger language/framework detection using repo languages and topics
- [ ] Better benchmarks sourced from public datasets (by language/role)
- [ ] Deeper PR/issue stats by fetching individual PR details
