# 1. Introduction / Welcome

Thanks for your interest in Qonscious. You are welcomed to contribute with improvements, fixes, and extensions. Just keep in mind that Qonscious is in active development and it is part of a research project. In that context, we may not be able (or willing to) integrate all proposals. However, you can work on you own version of Qonsiocus is you cite this work.  

# 2.	Code of Conduct (link or summary)

* Be nice.
* Be prepare for APIs to change. 
* If you use Qonscious (or find it interesting), reference it.
* If you write an article talking about or using Qonscious, cite one of the articles listed in the project's home page. 

# 3.	How to Contribute

* Report bugs and suggest features as Github issues.
* Asking questions by email to any of the maintainers.
* Use (piecemeal) pull request to propose changes.
* Document your code as described below.

# 4.    What to contribute

Qonscious is an experimentation platform. As such, it already foresees a few extension points (where you can hang your contributions). Each of these extension point is present in the design as an abstract class, dictype or protocol that you can extend. 

* **Adapters**: Adapters (backend adapters) give Qonscious users independence from specific vendor APIs. Using adapters makes a tradeoff between abstraction (polimorphic APIs) and control (using QPU specific features). 

* **Functions of merit**: Functions of Merit (FoM's) capture the charateristics of a quantum computing platform (QPU or Simulator) that are relevant for computing. Creating and using FoM's is Qonscious way on reflecting and learning about quantum computation resources in the NISQ era.

**Notebooks**: You can also contribute with usage examples in the form of Jupyter notebooks that use Qonscious. 

**Merit compliance checks** You often use FoM's to check if a given backend (i.e., adapted backend) offers the resources your use case needs. Checks (implementes as instances of the MeritComplianceCheck class) combine a FoM with a callback function that takes the result of checking that FoM on the backend and resutls true of false. Writing these checks is a bit convoluted so having many examples is useful.

# 5.    Versioning and releasing

In the current phase of development, the design of Qonscious will change often. As we create new FoMs, provide new backend adapters, and explore usage scenarios, the API will change. There will be no PyPI version you can install with pip. For the time being, you install with `pip install -e`

## Versioning (SemVer)
- MAJOR.MINOR.PATCH (tag `vX.Y.Z`)
- Pre-releases: `vX.Y.Z-rc.N`

## Steps
1. Update code and docs.
2. Update CHANGELOG.md.
3. Choose version bump:
   - Feature: MINOR
   - Bugfix: PATCH
4. Update version in toml file
5. Commit those changes (do not yet push)
6. Tag: `git tag vX.Y.Z && git push origin vX.Y.Z`
7. Push to main
8. Manually run CI action and iof tests pass, then manually run the release action

Git: use v prefix for clarity: e.g., v0.1.0.

We use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) (feat:, fix:, docs:, refactor:…) to evantually enable automated version bump.

# 6.	Development notes

## Setting up dependencies

This project is organized with a [pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) file, so there is no longer a need for a requirements.txt file.

Python version is set in .python-version

We recommend working in a Python virtual environment. The following snippet of code provides examples of most of the tasks you'll need to complete. 

```bash
python -m venv .venv 
source .venv/bin/activate
pip install -U pip wheel
pip install -e ".[dev,notebooks,viz,docs]" # you can leave notebooks and viz out if you are only working on the framework.
```

The **-e flag** in pip install tells pip to install Qonscious as a dependency so you can import from any Jupyter notebook working on the same venv while letting you edit the framework.

## Typing

This project uses pyright as a typechecker (In VSCode it will work via PyLance). Settings are defined in pyrightconfig.json

## Formating and linting

This project uses ruff for formating, linting, etc.

pyproject.toml includes default configurations for ruff

Ruff is part of the [dev] dependencies.

To use ruff from the command line (and let ruff format, and tidy up code),  do as follows:

```python
ruff check . --fix
ruff format .
```

## Testing

Make sure that any extensions/improvement/changes you contribute are covered by unit tests.

Mark test methods that interact with IBM's backend (thus requiring a token) with the annotation `@pytest.mark.ibm_token_required` or `@pytest.mark.ionq_apikey_required` if they interact with IONQ's backend. 

Use:
* `pytest` : to run all tests
* `pytest -m "not (ibm_token_required or ionq_apikey_required)"` : to only run tests that to not interact with IBM's or IONQ`sbackend
* `pytest -m "ibm_token_required"` : to only run tests that that do interact with IBM's backend
* `pytest -m "ionq_apikey_required"` : to only run tests that that do interact with IONQ'S backend


## VisualStudio Code

There is a _vscode_example_settings.json file that you can rename to .vscode/settings.json . It provides most default settings that help VSC find tests, work with notebooks, etc. 


## ruff

pyproject.toml includes default configurations for ruff (linting, etc.). Ruff is part of the [dev] dependencies.

To use ruff from the command line (and let ruff format and tidy up code),  do as follows:

```python
ruff check . --fix
ruff format .
```

## pyright

This project uses pyright as a typechecker (In VSCode it will work via PyLance).

Settings are defined in pyrightconfig.json


# Keep documentation up to date

We use mkdocs + mkdocstrings to generate documentation.

## Write good docstrings + type hints
- Use [Google style](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html) consistently.
- Public APIs should document: summary, Args, Returns, Raises, Examples.

## Preview locally while writing

```bash
mkdocs serve
```
