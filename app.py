import os
import sqlite3
import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go

DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "medicamentos.db"))


def sql_df(query, params=None):
    with sqlite3.connect(DB_PATH) as con:
        return pd.read_sql_query(query, con, params=params or [])


def money(x):
    if x is None or pd.isna(x):
        return "$0"
    return f"${x:,.0f}".replace(",", ".")


def get_filter_options():
    groups = sql_df("""
        SELECT DISTINCT grupo_fco_economico AS value
        FROM dispensacion
        WHERE TRIM(COALESCE(grupo_fco_economico,'')) <> ''
        ORDER BY value
    """)["value"].tolist()
    regions = sql_df("""
        SELECT DISTINCT regional_caf AS value
        FROM dispensacion
        WHERE TRIM(COALESCE(regional_caf,'')) <> ''
        ORDER BY value
    """)["value"].tolist()
    years = sql_df("""
        SELECT DISTINCT CAST(substr(fecha_entrega,1,4) AS INTEGER) AS value
        FROM dispensacion ORDER BY value
    """)["value"].tolist()
    return groups, regions, years


def where_clause(group, year, month, region):
    clauses = ["1=1"]
    params = []
    if group:
        clauses.append("grupo_fco_economico = ?")
        params.append(group)
    if year:
        clauses.append("substr(fecha_entrega,1,4) = ?")
        params.append(str(year))
    if month:
        clauses.append("CAST(substr(fecha_entrega,6,2) AS INTEGER) = ?")
        params.append(int(month))
    if region:
        clauses.append("regional_caf = ?")
        params.append(region)
    return " AND ".join(clauses), params


groups, regions, years = get_filter_options()
months = [
    {"label": n, "value": i}
    for i, n in enumerate(
        ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"],
        start=1,
    )
]

app = Dash(__name__)
server = app.server
app.title = "Medicamentos dispensados EPS"

CARD = {
    "background": "white",
    "borderRadius": "14px",
    "padding": "18px",
    "boxShadow": "0 2px 10px rgba(0,0,0,.08)",
}

app.layout = html.Div(
    style={"fontFamily": "Arial, sans-serif", "background": "#f4f6f9", "minHeight": "100vh", "padding": "22px"},
    children=[
        html.H1("Tablero de medicamentos dispensados 2020-2021", style={"marginBottom": "4px"}),
        html.P("EPS - análisis de dispensación, costos y segmentación", style={"color": "#5f6b7a", "marginTop": 0}),
        html.Div(
            style={**CARD, "marginBottom": "18px"},
            children=[
                html.H3("Filtros"),
                html.Div(
                    style={"display": "grid", "gridTemplateColumns": "repeat(4, minmax(180px,1fr))", "gap": "12px"},
                    children=[
                        dcc.Dropdown(groups, placeholder="Grupo farmacológico", id="f-group", clearable=True),
                        dcc.Dropdown(years, placeholder="Año", id="f-year", clearable=True),
                        dcc.Dropdown(months, placeholder="Mes", id="f-month", clearable=True),
                        dcc.Dropdown(regions, placeholder="Regional CAF", id="f-region", clearable=True),
                    ],
                ),
            ],
        ),
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "repeat(3,1fr)", "gap": "14px", "marginBottom": "18px"},
            children=[
                html.Div([html.Div("Personas con dispensaciones", style={"color": "#6b7280"}), html.H2(id="kpi-personas"), html.Small("personas", style={"color": "#9ca3af"})], style=CARD),
                html.Div([html.Div("Fórmulas distintas", style={"color": "#6b7280"}), html.H2(id="kpi-formulas"), html.Small("fórmulas", style={"color": "#9ca3af"})], style=CARD),
                html.Div([html.Div("Costo promedio por fórmula", style={"color": "#6b7280"}), html.H2(id="kpi-promedio"), html.Small("COP", style={"color": "#9ca3af"})], style=CARD),
            ],
        ),
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1.3fr 1fr", "gap": "14px", "marginBottom": "14px"},
            children=[
                html.Div(dcc.Graph(id="g-tiempo"), style=CARD),
                html.Div(dcc.Graph(id="g-top"), style=CARD),
            ],
        ),
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "repeat(3,1fr)", "gap": "14px", "marginBottom": "18px"},
            children=[
                html.Div(dcc.Graph(id="g-pbs"), style=CARD),
                html.Div(dcc.Graph(id="g-municipio"), style=CARD),
                html.Div(dcc.Graph(id="g-entrega"), style=CARD),
            ],
        ),
        html.Div(
            style={**CARD, "marginTop": "18px"},
            children=[
                html.H2("Análisis especial: ANTIDIABÉTICOS"),
                html.P(
                    "Nota metodológica: en 2020 el campo grupo_fco_economico está vacío. Para comparar 2020 con 2021 se usa como aproximación el conjunto de descripciones que sí están clasificadas como ANTIDIABETICOS en 2021 y se buscan esas mismas descripciones en 2020.",
                    style={"color": "#5f6b7a"},
                ),
                html.Div(
                    style={"display": "grid", "gridTemplateColumns": "repeat(3,1fr)", "gap": "14px", "marginBottom": "12px"},
                    children=[
                        html.Div([html.Div("Variación estimada 2020-2021"), html.H2(id="anti-var")], style={**CARD, "boxShadow": "none", "border": "1px solid #e5e7eb"}),
                        html.Div([html.Div("Medicamento de mayor costo (2021)"), html.H4(id="anti-top")], style={**CARD, "boxShadow": "none", "border": "1px solid #e5e7eb"}),
                        html.Div([html.Div("Costo promedio por fórmula (2021)"), html.H2(id="anti-prom")], style={**CARD, "boxShadow": "none", "border": "1px solid #e5e7eb"}),
                    ],
                ),
                dcc.Graph(id="anti-trend"),
            ],
        ),
        html.P("Fuente: medicamentos.db, tabla dispensacion.", style={"color": "#7b8491", "fontSize": "12px", "marginTop": "18px"}),
    ],
)


@app.callback(
    Output("kpi-personas", "children"),
    Output("kpi-formulas", "children"),
    Output("kpi-promedio", "children"),
    Output("g-tiempo", "figure"),
    Output("g-top", "figure"),
    Output("g-pbs", "figure"),
    Output("g-municipio", "figure"),
    Output("g-entrega", "figure"),
    Output("anti-var", "children"),
    Output("anti-top", "children"),
    Output("anti-prom", "children"),
    Output("anti-trend", "figure"),
    Input("f-group", "value"),
    Input("f-year", "value"),
    Input("f-month", "value"),
    Input("f-region", "value"),
)
def update_dashboard(group, year, month, region):
    where, params = where_clause(group, year, month, region)

    kpi = sql_df(f"""
        SELECT COUNT(DISTINCT id) personas, COUNT(DISTINCT formula) formulas
        FROM dispensacion WHERE {where}
    """, params).iloc[0]
    prom = sql_df(f"""
        SELECT AVG(costo_formula) promedio
        FROM (
            SELECT formula, SUM(costo_total) costo_formula
            FROM dispensacion
            WHERE {where} AND formula IS NOT NULL
            GROUP BY formula
        )
    """, params).iloc[0]["promedio"]

    tiempo = sql_df(f"""
        SELECT substr(fecha_entrega,1,7) periodo,
               COUNT(*) dispensaciones,
               SUM(costo_total) costo_total
        FROM dispensacion
        WHERE {where}
        GROUP BY periodo ORDER BY periodo
    """, params)
    fig_t = px.line(tiempo, x="periodo", y="dispensaciones", markers=True, title="Dispensaciones en el tiempo")
    fig_t.update_layout(xaxis_title="Mes", yaxis_title="Número de dispensaciones", margin=dict(l=65,r=25,t=55,b=45), height=520)

    top = sql_df(f"""
        SELECT descripcion, SUM(costo_total) costo_total
        FROM dispensacion
        WHERE {where}
        GROUP BY descripcion
        ORDER BY costo_total DESC LIMIT 10
    """, params).sort_values("costo_total")
    fig_top = px.bar(top, x="costo_total", y="descripcion", orientation="h", title="Top 10 medicamentos por costo total")
    fig_top.update_layout(
        xaxis_title="Costo total (COP)", yaxis_title="",
        margin=dict(l=260, r=30, t=60, b=45),
        height=520
    )
    fig_top.update_yaxes(automargin=True, tickfont=dict(size=11))
    fig_top.update_xaxes(tickformat="~s")

    pbs = sql_df(f"""
        SELECT CASE WHEN TRIM(COALESCE(pbs,''))='' THEN 'SIN DATO' ELSE pbs END pbs,
               SUM(costo_total) costo_total
        FROM dispensacion WHERE {where}
        GROUP BY 1 ORDER BY costo_total DESC
    """, params)
    fig_pbs = px.pie(pbs, names="pbs", values="costo_total", title="Costo según PBS / No PBS", hole=.45)
    fig_pbs.update_layout(margin=dict(l=20,r=20,t=55,b=20), height=470)

    muni = sql_df(f"""
        SELECT CASE WHEN TRIM(COALESCE(municipio_caf,''))='' OR TRIM(CAST(municipio_caf AS TEXT))='0' THEN 'SIN DATO' ELSE municipio_caf END municipio_caf,
               SUM(costo_total) costo_total
        FROM dispensacion WHERE {where}
        GROUP BY 1 ORDER BY costo_total DESC LIMIT 12
    """, params).sort_values("costo_total")
    fig_m = px.bar(muni, x="costo_total", y="municipio_caf", orientation="h", title="Costo por municipio de dispensación")
    fig_m.update_layout(
        xaxis_title="Costo total (COP)", yaxis_title="",
        margin=dict(l=120, r=20, t=55, b=50), height=470
    )
    fig_m.update_yaxes(automargin=True)
    fig_m.update_xaxes(tickformat="~s")

    ent = sql_df(f"""
        SELECT CASE WHEN TRIM(COALESCE(tipo_entrega,''))='' THEN 'SIN DATO' ELSE tipo_entrega END tipo_entrega,
               SUM(costo_total) costo_total
        FROM dispensacion WHERE {where}
        GROUP BY 1 ORDER BY costo_total DESC
    """, params)
    fig_e = px.bar(ent, x="tipo_entrega", y="costo_total", title="Costo según tipo de entrega")
    fig_e.update_layout(xaxis_title="Tipo de entrega", yaxis_title="Costo total (COP)", margin=dict(l=55,r=20,t=55,b=85))
    fig_e.update_xaxes(tickangle=-25)
    fig_e.update_yaxes(tickformat="~s")

    # Análisis ANTIDIABÉTICOS. Se deja fijo e independiente de los filtros globales.
    anti_year = sql_df("""
        WITH anti AS (
            SELECT DISTINCT descripcion FROM dispensacion
            WHERE grupo_fco_economico='ANTIDIABETICOS'
        )
        SELECT substr(fecha_entrega,1,4) anio, SUM(costo_total) costo_total
        FROM dispensacion
        WHERE descripcion IN (SELECT descripcion FROM anti)
        GROUP BY anio ORDER BY anio
    """)
    c20 = anti_year.loc[anti_year["anio"]=="2020", "costo_total"]
    c21 = anti_year.loc[anti_year["anio"]=="2021", "costo_total"]
    variacion = ((c21.iloc[0] / c20.iloc[0]) - 1) * 100 if len(c20) and len(c21) and c20.iloc[0] else None

    anti_top_df = sql_df("""
        SELECT descripcion, SUM(costo_total) costo_total
        FROM dispensacion
        WHERE grupo_fco_economico='ANTIDIABETICOS'
        GROUP BY descripcion ORDER BY costo_total DESC LIMIT 1
    """)
    anti_top_text = "Sin datos"
    if not anti_top_df.empty:
        anti_top_text = f"{anti_top_df.iloc[0]['descripcion']} - {money(anti_top_df.iloc[0]['costo_total'])}"

    anti_prom_df = sql_df("""
        SELECT AVG(costo_formula) promedio
        FROM (
            SELECT formula, SUM(costo_total) costo_formula
            FROM dispensacion
            WHERE grupo_fco_economico='ANTIDIABETICOS' AND formula IS NOT NULL
            GROUP BY formula
        )
    """)
    anti_prom = anti_prom_df.iloc[0]["promedio"]

    anti_month = sql_df("""
        SELECT substr(fecha_entrega,1,7) periodo, SUM(costo_total) costo_total
        FROM dispensacion
        WHERE grupo_fco_economico='ANTIDIABETICOS'
        GROUP BY periodo ORDER BY periodo
    """)
    anti_fig = px.line(anti_month, x="periodo", y="costo_total", markers=True, title="Costo mensual de ANTIDIABÉTICOS (clasificación disponible en 2021)")
    anti_fig.update_layout(xaxis_title="Mes", yaxis_title="Costo total (COP)", margin=dict(l=70,r=30,t=60,b=50), height=500)
    anti_fig.update_yaxes(tickformat="~s")

    return (
        f"{int(kpi['personas']):,}".replace(",", "."),
        f"{int(kpi['formulas']):,}".replace(",", "."),
        money(prom),
        fig_t,
        fig_top,
        fig_pbs,
        fig_m,
        fig_e,
        f"{variacion:+.1f}% (estimada)" if variacion is not None else "No calculable",
        anti_top_text,
        money(anti_prom),
        anti_fig,
    )


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 8050)))
