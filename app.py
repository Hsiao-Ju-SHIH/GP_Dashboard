# pe_gp_dashboard.py

from shiny import App, ui, render, reactive
from shinywidgets import output_widget, render_widget
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pathlib

# ----------------------
# Sample Data
# ----------------------
funds = pd.DataFrame({
    "Fund": ["Fund I", "Fund II", "Fund III"],
    "Commitment": [100, 200, 300],
    "Called": [90, 180, 250],
    "Distributions": [60, 150, 200],
    "NAV": [40, 60, 100],
    "IRR": [12.5, 14.8, 17.3],
    "MOIC": [1.1, 1.3, 1.5],
    "DPI": [0.6, 0.75, 0.8],
    "RVPI": [0.44, 0.33, 0.4],
    "TVPI": [1.04, 1.08, 1.2]
})

companies = pd.DataFrame({
    "Company": ["Alpha", "Beta", "Gamma", "Delta"],
    "Fund": ["Fund I", "Fund II", "Fund II", "Fund III"],
    "Investment Date": ["2018", "2019", "2020", "2021"],
    "Exit Date": ["2022", None, None, None],
    "Cost": [10, 15, 12, 20],
    "Value": [25, 20, 13, 30],
    "MOIC": [2.5, 1.33, 1.08, 1.5]
})

cashflows = pd.DataFrame({
    "Date": pd.date_range("2018-01-01", periods=8, freq='QE'),
    "Type": ["Investment", "Investment", "Follow-on", "Exit", "Dividend", "Investment", "Exit", "Dividend"],
    "Amount": [-10, -15, -5, 30, 2, -20, 40, 5],
    "Fund": ["Fund I", "Fund I", "Fund I", "Fund I", "Fund I", "Fund II", "Fund II", "Fund II"]
})
cashflows['Date'] = cashflows['Date'].dt.date
cashflows['Date'] = cashflows['Date'].astype('string')


pipeline_data = pd.DataFrame({
    "Deal": ["Startup A", "Startup B", "Startup C", "Startup D", "Startup E", "Startup F"],
    "Stage": ["Screening", "Due Diligence", "IC", "Closed", "IC", "Closed"],
    "Lead Partner": ["Aditya", "Siddharth", "Adrian", "Aditya", "Adrian", "Aditya"],
})

company_kpis = pd.DataFrame({
    "Company": ["eFishery", "KitaBeli"],
    "Monthly Revenue ($K)": [200, 150],
    "User Growth (%)": [12, 18],
    "EBITDA Margin (%)": [-10, -5],
})

lp_data = pd.DataFrame({
    "LP Name": ["Sovereign Fund A", "Family Office B", "Institutional C"],
    "Commitment ($M)": [50, 10, 30],
    "Type": ["Sovereign", "Family Office", "Institution"],
    "Email": ["lpA@example.com", "lpB@example.com", "lpC@example.com"],
    "Phone": ["+62 812-3456", "+65 9123-4567", "+1 415-234-5678"],
})

# ----------------------
# UI
# ----------------------
app_ui = ui.page_sidebar(
    ui.sidebar(ui.input_selectize("fund_filter", "Select Fund(s):", choices=list(funds["Fund"]), multiple=True),
               ui.input_slider("year_filter", "Investment Year", 2015, 2025, 2025),               
    ),
    ui.tags.style("""
        h2 { color: #003366; margin-top: 1rem; }
        .shiny-input-container { margin-bottom: 1rem; }
        .nav-tabs .nav-link.active { background-color: #003366; color: white !important; }
    """),
    ui.panel_title("📊 Private Equity GP Dashboard", "h2"),
    ui.br(),
    ui.navset_tab(
        # Overview Tab
        ui.nav_panel("Portfolio Overview",
            ui.layout_columns(
                ui.card(
                    ui.card_header('Statistics'), ui.output_data_frame("summary_table"), full_screen=True
                ),
                ui.card(
                    ui.download_button('download_data', "Download Fund Data", class_ = 'btn btn-primary')
                ),col_widths=[6, 6],
            ),
            ui.layout_columns(
                ui.card(
                    output_widget("sector_alloc"), full_screen=True
                ),
                ui.card(
                    output_widget("regional_alloc"), full_screen=True
                ),col_widths=[6, 6],
            ),
        ),

        # Fund Performance
        ui.nav_panel("Fund Performance",
            ui.layout_columns(
                ui.card(
                    ui.card_header('Statistics'), ui.output_data_frame("fund_metrics"), full_screen=True
                ),
            ),
            ui.layout_columns(
                ui.card(
                    output_widget("irr_comparison"), full_screen=True
                ),
            ),
            ui.layout_columns(
                ui.card(
                    output_widget("deployment_timeline"), full_screen=True
                ),
            ),
        ),

        # Portfolio Companies
        ui.nav_panel("Portfolio Companies",
            ui.layout_columns(
                ui.card(
                    ui.card_header('Statistics'), ui.output_data_frame("company_table"), full_screen=True
                ),
            ),
            ui.layout_columns(
                ui.card(
                output_widget("value_creation"), full_screen=True     
                ),
            ),
            ui.layout_columns(
                ui.card(
                output_widget("holding_period"), full_screen=True      
                ),
            ),
        ),

        # Cash Flows
        ui.nav_panel("Cash Flow Analysis",
            ui.layout_columns(
                ui.card(
                    output_widget("cashflow_timeline"), full_screen=True
                ),
            ),
            ui.layout_columns(
                ui.card(
                    output_widget("cashflow_breakdown"), full_screen=True
                ),
            ),
            ui.layout_columns(
                ui.card(
                    output_widget("cumulative_cashflow"), full_screen=True
                ),
            ),
        )
    )
)

# ----------------------
# Server
# ----------------------
def server(input, output, session):

    @reactive.calc
    def filtered_funds():
        selected = input.fund_filter()
        return funds[funds["Fund"].isin(selected)] if selected else funds

    @reactive.calc
    def filtered_companies():
        selected = input.fund_filter()
        year = input.year_filter()
        df = companies.copy()
        df = df[df["Investment Date"].astype(int) <= year]
        if selected:
            df = df[df["Fund"].isin(selected)]
        return df

    @output
    @render.data_frame
    def summary_table():
        df = filtered_funds()
        summary = {
            "Total Commitment": df["Commitment"].sum(),
            "Total Called": df["Called"].sum(),
            "Total Distributions": df["Distributions"].sum(),
            "NAV": df["NAV"].sum()
        }
        df_summary = pd.DataFrame(summary.items(), columns=["Metric", "Value"])
        return render.DataGrid(df_summary.round(2))

    @output
    @render_widget
    def sector_alloc():
        return px.pie(names=["Tech", "Healthcare", "Energy"], values=[40, 30, 30], title="Sector Allocation", hole=0.3)

    @output
    @render_widget
    def regional_alloc():
        return px.pie(names=["North America", "Europe", "Asia"], values=[50, 30, 20], title="Regional Allocation", hole=0.3)


    @output
    @render.download(filename='company_profile.xlsx')
    def download_data():
        file_path = pathlib.Path('data/POC_output.xlsx')
        with open(file_path, 'rb') as f:
            yield f.read()


    @output
    @render.data_frame
    def fund_metrics():
        return filtered_funds()

    @output
    @render_widget
    def irr_comparison():
        df = filtered_funds()
        fig = px.bar(df, x="Fund", y="IRR", text="IRR", title="IRR Comparison")
        fig.add_hline(
                    y=15,  # 15%
                    line_dash="dash",
                    line_color="#346beb",
                    annotation_text="Benchmark 15%",
                    annotation_position="top left"
                )
        return fig

    @output
    @render_widget
    def deployment_timeline():
        df = filtered_companies()
        fig = go.Figure()
        for _, row in df.iterrows():
            fig.add_trace(go.Scatter(x=[row["Investment Date"], row["Exit Date"] or "2025"],
                                     y=[row["Company"]]*2,
                                     mode="lines+markers", name=row["Company"]))
        fig.update_layout(title="Deployment Timeline", xaxis_title="Year", yaxis_title="Company")
        return fig

    @output
    @render.data_frame
    def company_table():
        return filtered_companies()

    @output
    @render_widget
    def value_creation():
        df = filtered_companies()
        fig = px.bar(df, x="Company", y="MOIC", title="Top Performers by MOIC")
        fig.add_hline(
                    y=2,  # 2x
                    line_dash="dash",
                    line_color="#346beb",
                    annotation_text="Benchmark 2x",
                    annotation_position="top right"
                )
        return fig

    @output
    @render_widget
    def holding_period():
        df = filtered_companies()
        df["Holding"] = df["Exit Date"].fillna("2025").astype(int) - df["Investment Date"].astype(int)
        fig = px.bar(df, x="Company", y="Holding", title="Holding Period (Years)")
        fig.add_hline(
                    y=4.5,  # 4.5 years
                    line_dash="dash",
                    line_color="#346beb",
                    annotation_text="Benchmark 4.5 years",
                    annotation_position="top right"
                )
        return fig

    @output
    @render_widget
    def cashflow_timeline():
        fig = px.line(cashflows, x="Date", y="Amount", color="Fund", title="Cash Flow Timeline", markers=True)
        fig.add_hline(
                    y=0,  
                    line_dash="dash",
                    line_color="#346beb",
                )
        return fig

    @output
    @render_widget
    def cashflow_breakdown():
        df = cashflows.groupby("Type")["Amount"].sum().reset_index()
        return px.bar(df, x="Type", y="Amount", title="Cash Flow Breakdown by Type")

    @output
    @render_widget
    def cumulative_cashflow():
        df = cashflows.sort_values("Date")
        df["Cumulative"] = df.groupby("Fund")["Amount"].cumsum()
        fig = px.line(df, x="Date", y="Cumulative", color="Fund", title="Cumulative Cash Flow by Fund")
        fig.add_hline(
                    y=0,  
                    line_dash="dash",
                    line_color="#346beb",
                )
        return fig

# ----------------------
# Run App
# ----------------------
app = App(app_ui, server)
