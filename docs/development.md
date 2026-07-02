# Development

## Prerequisites

Install uv:

### Windows

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### macOS / Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify the installation:

```bash
uv --version
```

Create a virtual environment:

```bash
uv venv
```

Install project dependencies:

```bash
uv sync
```

Activate the environment.

### Windows

```powershell
.venv\Scripts\activate
```

### Linux/macOS

```bash
source .venv/bin/activate
```

## Running tests

```bash
uv run pytest
```

---

## Linting

```bash
uv run ruff check .
```

Format code:

```bash
uv run ruff format .
```

---

# Install pre-commit

````bash
pre-commit install
````

---

## Managing dependencies

Add a dependency:

```bash
uv add requests
```

Add a development dependency:

```bash
uv add --dev pytest
```

Remove a dependency:

```bash
uv remove requests
```

Update the lock file:

```bash
uv lock
```

Synchronize the environment:

```bash
uv sync
```