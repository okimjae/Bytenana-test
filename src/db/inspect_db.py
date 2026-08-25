import duckdb
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()


def inspect_database():
    conn = duckdb.connect("spatial_data.duckdb")

    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]🏦 DATABASE INSPECTION & METRICS[/bold cyan]\n"
            "[dim]Buda & Hays County Spatial Data Engine[/dim]",
            border_style="cyan",
            box=box.ROUNDED,
        )
    )

    # 1. Table Record Counts
    table_counts = Table(
        title="[bold yellow]📊 Tables & Record Counts[/bold yellow]",
        box=box.ROUNDED,
        header_style="bold magenta",
        title_justify="left",
    )
    table_counts.add_column("Table Name", style="bold white")
    table_counts.add_column("Type / Layer", style="dim cyan")
    table_counts.add_column("Total Records", justify="right", style="bold green")

    layers = {
        "stg_zoning": "Raw Zoning Staging (Buda ArcGIS)",
        "stg_parcels": "Raw Parcels Staging (Hays County)",
        "fct_parcels_enriched": "Enriched Fact Layer (Spatial Join)",
        "agent_loop_audits": "Safety Loops & Agent Audits",
    }

    for table_name, layer_desc in layers.items():
        cnt = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        table_counts.add_row(table_name, layer_desc, f"{cnt:,}")

    console.print(table_counts)
    console.print()

    # 2. Agent & Safety Loop Audits
    table_audits = Table(
        title="[bold yellow]🤖 Multi-Agent Orchestration & Closed Safety Loops[/bold yellow]",
        box=box.ROUNDED,
        header_style="bold blue",
        title_justify="left",
    )
    table_audits.add_column("Phase", justify="center", style="dim")
    table_audits.add_column("Agent Name", style="bold white")
    table_audits.add_column("Safety Loop Gate", style="cyan")
    table_audits.add_column("Status", justify="center")
    table_audits.add_column("Duration", justify="right", style="yellow")
    table_audits.add_column("Processed", justify="right", style="green")

    audits = conn.execute(
        "SELECT phase_order, agent_name, loop_name, status, duration_ms, records_count FROM agent_loop_audits ORDER BY phase_order"
    ).fetchall()

    for p_order, a_name, l_name, status, dur, recs in audits:
        status_badge = "[bold green]✅ PASSED[/bold green]" if status == "PASSED" else "[bold red]❌ FAILED[/bold red]"
        table_audits.add_row(
            f"#{p_order}",
            a_name,
            l_name,
            status_badge,
            f"{dur:.1f} ms",
            f"{recs} rows",
        )

    console.print(table_audits)
    console.print()

    # 3. Residential Parcels > 1 Acre
    table_res = Table(
        title="[bold yellow]🏙️ Residential Parcels > 1 Acre (Computed Geodesic Acreage)[/bold yellow]",
        box=box.ROUNDED,
        header_style="bold green",
        title_justify="left",
    )
    table_res.add_column("Parcel ID", style="bold cyan")
    table_res.add_column("Subdivision", style="white")
    table_res.add_column("Zoning Code", justify="center", style="bold magenta")
    table_res.add_column("Zoning Name", style="dim")
    table_res.add_column("Computed Acres", justify="right", style="bold green")
    table_res.add_column("Match Status", style="blue")

    res_parcels = conn.execute("""
        SELECT parcel_id, subdivision, zone_code, zone_name, ROUND(calculated_area_acres, 2) AS acres, match_status
        FROM fct_parcels_enriched
        WHERE is_residential = TRUE AND calculated_area_acres > 1.0
        ORDER BY calculated_area_acres DESC
    """).fetchall()

    if res_parcels:
        for pid, subdiv, zcode, zname, acres, match in res_parcels:
            table_res.add_row(
                pid,
                subdiv,
                zcode or "N/A",
                zname or "N/A",
                f"{acres:.2f} ac",
                f"[dim]{match}[/dim]",
            )
        console.print(table_res)
    else:
        console.print("[dim yellow]No residential parcels > 1 acre found.[/dim yellow]")

    console.print()


if __name__ == "__main__":
    inspect_database()
