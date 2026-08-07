from __future__ import annotations

from pathlib import Path
import typer
from .analyze import analyze_collaboration
from .collector import YearResult, collect_venue
from .config import VENUES, get_venue
from .enrich import enrich_venue
from .openalex import OpenAlexClient

app = typer.Typer(no_args_is_help=True, add_completion=False, help="Fast, cached bibliometric collection for HPC conferences.")

@app.command("check-auth")
def check_auth() -> None:
    try:
        with OpenAlexClient() as client: client.check_auth()
    except RuntimeError as exc:
        typer.echo(f"Error: {exc}", err=True); raise typer.Exit(code=1) from None
    typer.echo("OpenAlex authentication: OK")

@app.command()
def collect(venue: str = typer.Argument(...), from_year: int = typer.Option(2016, "--from", "--from-year", min=1900),
            to_year: int = typer.Option(2025, "--to", "--to-year", min=1900), cache_dir: Path = typer.Option(Path("cache"), "--cache-dir", file_okay=False),
            workers: int = typer.Option(4, "--workers", "-j", min=1, max=10), refresh: bool = typer.Option(False, "--refresh")) -> None:
    try:
        spec = get_venue(venue); typer.echo(f"Collecting {spec.key.upper()} {from_year}-{to_year} from DBLP with {workers} worker(s)...")
        def report_year(item: YearResult) -> None: typer.echo(f"{item.year}: {item.count:4d} papers [{'cached' if item.cached else 'downloaded'}]")
        result = collect_venue(spec, from_year=from_year, to_year=to_year, cache_root=cache_dir, workers=workers, refresh=refresh, on_year=report_year)
    except (ValueError, RuntimeError) as exc:
        typer.echo(f"Error: {exc}", err=True); raise typer.Exit(code=1) from None
    typer.echo(f"Roster: {result.source['provider']} - {result.source['display_name']}")
    typer.echo(f"Total: {result.total_count} papers"); typer.echo(f"Manifest: {result.manifest}")

@app.command()
def enrich(venue: str = typer.Argument(...), from_year: int = typer.Option(2016, "--from", min=1900),
           to_year: int = typer.Option(2025, "--to", min=1900), cache_dir: Path = typer.Option(Path("cache"), "--cache-dir", file_okay=False),
           workers: int = typer.Option(4, "--workers", "-j", min=1, max=10), refresh: bool = typer.Option(False, "--refresh")) -> None:
    try:
        get_venue(venue); typer.echo(f"Enriching {venue.upper()} {from_year}-{to_year} with OpenAlex using {workers} worker(s)...")
        result = enrich_venue(venue.lower(), from_year=from_year, to_year=to_year, cache_root=cache_dir, workers=workers, refresh=refresh)
    except (ValueError, RuntimeError) as exc:
        typer.echo(f"Error: {exc}", err=True); raise typer.Exit(code=1) from None
    typer.echo(f"Total: {result.total} papers"); typer.echo(f"Matched: {result.matched}; missing DOI: {result.missing_doi}; unmatched: {result.unmatched}")
    typer.echo(f"Enrichment: {result.path}")

@app.command()
def analyze(venue: str = typer.Argument(...), from_year: int = typer.Option(2016, "--from", min=1900),
            to_year: int = typer.Option(2025, "--to", min=1900), cache_dir: Path = typer.Option(Path("cache"), "--cache-dir", file_okay=False)) -> None:
    """Classify institutions and summarize DOE National Lab collaboration."""
    try:
        get_venue(venue); result = analyze_collaboration(venue.lower(), from_year=from_year, to_year=to_year, cache_root=cache_dir)
    except (ValueError, RuntimeError) as exc:
        typer.echo(f"Error: {exc}", err=True); raise typer.Exit(code=1) from None
    typer.echo(f"Total: {result.total} papers")
    typer.echo(f"National Lab papers: {result.lab_papers}")
    typer.echo(f"National Lab + University papers: {result.lab_university_papers}")
    typer.echo(f"Yearly: {result.yearly_path}"); typer.echo(f"Institutions: {result.institutions_path}"); typer.echo(f"Papers: {result.papers_path}")

@app.command("list-venues")
def list_venues() -> None:
    for key, venue in sorted(VENUES.items()): typer.echo(f"{key:10s} {venue.display_name}")

if __name__ == "__main__": app()
