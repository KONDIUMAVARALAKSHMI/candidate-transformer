from __future__ import annotations

from pathlib import Path

import typer

from candidate_transformer.pipeline import run_pipeline

app = typer.Typer(add_completion=False, no_args_is_help=True)


try:
    import click

    _original_make_metavar = click.Parameter.make_metavar

    def _make_metavar_compat(self, *args, **kwargs):
        try:
            return _original_make_metavar(self, *args, **kwargs)
        except TypeError:
            return _original_make_metavar(self, None)

    click.Parameter.make_metavar = _make_metavar_compat

except Exception:
    pass


@app.command("run")
def run(
    csv: str = typer.Option(None, "--csv", help="Path to CSV file"),
    ats: Path | None = typer.Option(None, "--ats", help="Path to ATS JSON file"),
    resume: Path | None = typer.Option(None, "--resume", help="Path to resume file"),
    config: Path | None = typer.Option(None, "--config", help="Path to config YAML"),
    output: Path | None = typer.Option(None, "--output", help="Output JSONL path"),
    projection_config: Path | None = typer.Option(
        None,
        "--projection-config",
        help="Path to projection config JSON",
    ),
) -> None:
    """
    Transform candidate records into a unified schema.
    """

    if not any([csv, ats, resume]):
        typer.echo(
            "Error: At least one of --csv, --ats, or --resume must be provided.",
            err=True,
        )
        raise typer.Exit(code=2)

    try:
        records = run_pipeline(
            csv_path=csv,
            ats_path=ats,
            resume_path=resume,
            output_path=output,
            config=config,
            projection_config=projection_config,
        )
    except (FileNotFoundError, ValueError, TypeError) as exc:
        typer.echo(f"Pipeline failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    output_path = output or Path("output/candidates_unified.jsonl")
    typer.echo(f"Wrote {len(records)} candidate record(s) to {output_path}")


if __name__ == "__main__":
    app()
