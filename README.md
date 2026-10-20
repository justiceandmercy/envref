# envref

Compare environment variable references in source code with `.env.example` and report missing or unused entries.

## Features

- Scans common source files for environment variable references.
- Detects references in Python, JavaScript/TypeScript, Go, Ruby, and shell scripts.
- Reports variables used in code but absent from `.env.example`.
- Reports variables declared in `.env.example` but never referenced.
- Emits machine-readable JSON for CI pipelines.
- Uses only the Python standard library.

## Install

Clone the repository and install it:

```bash
git clone <repository-url>
cd envref
python -m pip install .
```

Or run it directly without installation:

```bash
python envref.py .
```

## Usage

```bash
envref .
envref src --env-file config/.env.example
envref . --json
```

By default the command exits with status 1 when variables are referenced in code but missing from the template. Use `--fail-on unused`, `--fail-on any`, or `--fail-on none` to change that behavior.

## License

MIT
