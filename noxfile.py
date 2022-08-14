from pathlib import Path
from typing import Iterator

import nox
from nox import Session

BASEPATH = Path(__file__).parent.resolve()

nox.options.sessions = [
    "clean",
    "fix",
    "pylint",
    "mypy",
    "unit",
    "coverage",
]


@nox.session(python=False)
def clean(_: Session) -> None:
    coverage_file = BASEPATH / ".coverage"
    coverage_file.unlink(missing_ok=True)


@nox.session(python=False)
def fix(session: Session) -> None:
    def _python_files(path: Path) -> Iterator[str]:
        files = filter(lambda path: "dist" not in path.parts, BASEPATH.glob("**/*.py"))
        files = filter(lambda path: ".eggs" not in path.parts, files)
        files = filter(lambda path: "venv" not in path.parts, files)
        return (f"{p}" for p in files)

    session.run(
        "python",
        "-m",
        "pyupgrade",
        "--py38-plus",
        "--exit-zero-even-if-changed",
        *_python_files(BASEPATH),
    )
    session.run("python", "-m", "isort", "-v", f"{BASEPATH}")
    session.run("python", "-m", "black", f"{BASEPATH}")


@nox.session(python=False)
def pylint(session: Session) -> None:
    session.run("python", "-m", "pylint", f'{BASEPATH / "konfy" / "konfy.py"}')


@nox.session(python=False)
def unit(session: Session) -> None:
    session.env["COVERAGE"] = "coverage"
    session.env["COVERAGE_FILE"] = f'{BASEPATH / ".coverage"}'
    session.run(
        "python",
        "-m",
        "coverage",
        "run",
        "-a",
        f'--rcfile={BASEPATH / "pyproject.toml"}',
        "-m",
        "pytest",
        "--doctest-modules",
        f"{BASEPATH}",
    )


@nox.session(python=False)
def mypy(session: Session) -> None:
    session.run(
        "python",
        "-m",
        "mypy",
        "--strict",
        "--show-error-codes",
        "--pretty",
        "--show-column-numbers",
        "--show-error-context",
        "--scripts-are-modules",
    )


@nox.session(python=False)
def coverage(session: Session) -> None:
    session.env["COVERAGE"] = "coverage"
    session.env["COVERAGE_FILE"] = f'{BASEPATH / ".coverage"}'
    session.run("coverage", "report", "--fail-under=97")
    session.run("coverage", "lcov")


PROJECTS = ['konfy']


@nox.session(python=False)
def publish(session: Session) -> None:
    args = list(session.posargs)
    project = args[0]
    if project not in PROJECTS:
        session.error(f"Unknown project: {project}")
    project = Path(project)
    with session.chdir(project):
        session.run("python", "setup.py", "sdist")
        session.run("python", "setup.py", "bdist_wheel")
        session.run("twine", "upload", "dist/*")
