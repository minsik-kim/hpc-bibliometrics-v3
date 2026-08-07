from __future__ import annotations

from pathlib import Path

import typer

from .collector import YearResult, collect_venue
from .config import VENUES, get_venue
from .openalex import OpenAlexClient

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="Fast, cached bibliometric collection for HPC conferences.",
)


@app.command("check-auth")
def check_auth() -> None:
    """Validate OPENALEX_API_KEY before starting a collection."""

    try:
        with OpenAlexClient() as client:
            client.check_auth()
    except RuntimeError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from None

    typer.echo("OpenAlex authentication: OK")


@app.command()
def collect(
    venue: str = typer.Argument(..., help="Venue key, for example: ipdps"),
    from_year: int = typer.Option(2016, "--from", "--from-year", min=1900),
    to_year: int = typer.Option(2025, "--to", "--to-year", min=1900),
    cache_dir: Path = typer.Option(Path("cache"), "--cache-dir", file_okay=False),
    workers: int = typer.Option(4, "--workers", "-j", min=1, max=10),
    refresh: bool = typer.Option(False, "--refresh", help="Replace existing yearly caches."),
) -> None:
    """Collect a venue's OpenAlex records into yearly Parquet files."""

    try:
        spec = get_venue(venue)
        typer.echo(
            f"Collecting {spec.key.upper()} {from_year}-{to_year} "
            f"with {workers} worker(s)..."
        )

        def report_year(item: YearResult) -> None:
            state = "cached" if item.cached else "downloaded"
            typer.echo(f"{item.year}: {item.count:4d} works [{state}]")

        result = collect_venue(
            spec,
            from_year=from_year,
            to_year=to_year,
            cache_root=cache_dir,
            workers=workers,
            refresh=refresh,
            on_year=report_year,
        )
    except (ValueError, RuntimeError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from None

    typer.echo(f"Source: {result.source['display_name']} ({result.source['id']})")
    typer.echo(f"Total: {result.total_count} works")
    typer.echo(f"Manifest: {result.manifest}")


@app.command("list-venues")
def list_venues() -> None:
    """List configured conference keys."""

    for key, venue in sorted(VENUES.items()):
        typer.echo(f"{key:10s} {venue.display_name}")


if __name__ == "__main__":
    app()
