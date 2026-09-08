# Project Context

Read these files before proceeding:

File         | Purpose
-------------|-------------------------------------
`README.md`  | Project overview.

## Programming Standards

Follow these instructions when writing code.

### Python

All Python code lives in the `/backend` directory. Use `uv`
for dependency management and testing instead of `pip`.

Right:

```powershell
cd backend
uv add pandas
uv run fastapi dev
```

Wrong:

```powershell
cd backend
pip install pandas
fastapi dev
```

Write Google-style docstrings. Include type hints. Create
`pydantic` `BaseModel` classes to model complex data
structures which cannot be captured by a primitive type.

Lint your code with `ruff`.

```powershell
cd backend
uvx run ruff check .
```

## Git Standards

When you are asked to develop a new feature, do not commit
directly to the `main` branch. Create a new branch to
develop your feature if you are on the `main` branch.

```powershell
git status
> On branch main
> ...
git checkout -b your_feature_name
```

Once your feature is ready for deployment, create a pull
request to merge your branch back into `main`.'

Committing directly to `main` is acceptable when fixing bugs
or adjusting the user interface for existing features which
have **already been merged**, but is not acceptable for new
features in development.

Always name your commits using the following style:
`VIBE: <Short description of changes>`.

## Writing Standards

When writing in English, use UK spelling and grammar. Use
Title Case for headings and sentence case for body text.

Use widely understood terms to describe software components.
Describe procedures and sequences using logically organised
paragraphs rather than unordered lists.

Do not use metaphors. Do not use the words 'golden example'
or 'happy path' to describe intended or exemplar
functionality. Do not use the word 'sidecar' to describe
supporting software components. Do not use the word 'shape'
to describe the design, structure, or function of software.

Do not use jargon and avoid using acronyms without first
providing their definition, unless the acronym is this list:

Term | Definition
-----|------------------------------------
API  | Application Programming Interface
GCP  | Google Cloud Platform
CW1  | CargoWise One
MCP  | Model Context Protocol
SQL  | Structured Query Language
DB   | Database

Do not use **boldface**, *italics*, or 'quotation marks' for
emphasis.

If you are asked to describe the structure or function of a
software component in simple, lay language, use generic
terms such as 'API', 'frontend', 'backend', 'server', or
'DB' rather than metaphors.

Do not include a version history in any documentation or
describe legacy behaviour which has been removed. Delete all
documentation which no longer reflects the current state of
the software.

When updating documentation to reflect changes made to the
software, remove all documentation describing the old
behaviour and add new documentation describing the new
behaviour. Never include a revision history.