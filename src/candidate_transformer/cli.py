from __future__ import annotations

from pathlib import Path

import typer

from candidate_transformer.pipeline import run_pipeline

app = typer.Typer(add_completion=False, no_args_is_help=True)


@app.command("run")
def run(
    csv: Path | None = typer.Option(None, "--csv", help="Path to the CSV source file."),
    ats: Path | None = typer.Option(None, "--ats", help="Path to the ATS JSON source file."),
    resume: Path | None = typer.Option(None, "--resume", help="Path to the resume PDF source file."),
    config: Path | None = typer.Option(None, "--config", help="Path to the YAML config file."),
    output: Path | None = typer.Option(None, "--output", help="Path to write the JSONL output file."),
    projection_config: Path | None = typer.Option(
        None,
        "--projection-config",
        help="Path to the JSON projection configuration file.",
    ),
) -> None:
    """Transform candidate records from CSV, ATS JSON, and resume PDFs into a unified JSON output."""

    if not any([csv, ats, resume]):
        typer.echo("At least one of --csv, --ats, or --resume must be provided.", err=True)
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

    output_path = output or "output/candidates_unified.jsonl"
    typer.echo(f"Wrote {len(records)} candidate record(s) to {output_path}")


if __name__ == "__main__":
    app()
