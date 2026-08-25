import duckdb
from tabulate import tabulate


def inspect_database():
    conn = duckdb.connect("spatial_data.duckdb")

    print("\n" + "=" * 80)
    print(" 📊 TABELAS E CONTAGEM DE REGISTROS NO BANCO DE DADOS")
    print("=" * 80)
    counts = []
    for table in ["stg_zoning", "stg_parcels", "fct_parcels_enriched", "agent_loop_audits"]:
        cnt = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        counts.append({"Tabela": table, "Total de Registros": cnt})
    print(tabulate(counts, headers="keys", tablefmt="fancy_grid"))

    print("\n" + "=" * 80)
    print(" 🤖 AUDITORIA DOS AGENTES E SAFETY LOOPS (TABELA: agent_loop_audits)")
    print("=" * 80)
    audits_df = conn.execute(
        "SELECT phase_order, agent_name, loop_name, status, duration_ms, records_count FROM agent_loop_audits ORDER BY phase_order"
    ).df()
    print(tabulate(audits_df, headers="keys", tablefmt="fancy_grid", showindex=False))

    print("\n" + "=" * 80)
    print(" 🏙️ LOTES RESIDENCIAIS > 1 ACRE GRAVADOS (TABELA: fct_parcels_enriched)")
    print("=" * 80)
    res_df = conn.execute("""
        SELECT parcel_id, subdivision, zone_code, zone_name, ROUND(calculated_area_acres, 2) AS acres, match_status
        FROM fct_parcels_enriched
        WHERE is_residential = TRUE AND calculated_area_acres > 1.0
    """).df()
    if not res_df.empty:
        print(tabulate(res_df, headers="keys", tablefmt="fancy_grid", showindex=False))
    else:
        print("Nenhum lote residencial > 1 acre encontrado.")
    print("\n")


if __name__ == "__main__":
    inspect_database()
