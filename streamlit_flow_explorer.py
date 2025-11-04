
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio
import streamlit as st

# ------------ Page Config ------------
st.set_page_config(page_title="WRMM QA/QC Explorer", layout="wide")

# ------------ Header ------------
st.title("🌊 WRMM QA/QC Explorer")

# ------------ File Upload Section ------------
st.sidebar.header("📁 Data Upload")
uploaded_file = st.sidebar.file_uploader(
    "Upload your data file",
    type=["csv", "xlsx", "xls"],
    help="Upload a CSV or Excel file with columns: Date, River_basin_name, Station_name, Raw_median, Step_2_median, Final_median"
)

# Add option to select sheet name for Excel files
sheet_name = "Combined"
if uploaded_file and uploaded_file.name.endswith(('.xlsx', '.xls')):
    sheet_name = st.sidebar.text_input("Sheet name", value="Combined", help="Enter the name of the sheet to read from Excel file")

# ------------ Load Data ------------
@st.cache_data
def load_data(file, sheet=None):
    """Load data from uploaded file"""
    try:
        # Determine file type and read accordingly
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file, sheet_name=sheet)
        else:
            st.error(f"Unsupported file type: {file.name}")
            return None, None
        
        # Convert Date column
        df["Date"] = pd.to_datetime(df["Date"])
        
        # Derive basin -> ordered station list
        basin_to_stations = (
            df[["River_basin_name", "Station_name"]]
            .dropna()
            .drop_duplicates()
            .groupby("River_basin_name")["Station_name"]
            .apply(list)
            .to_dict()
        )
        
        return df, basin_to_stations
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return None, None

# ------------ Main App Logic ------------
if uploaded_file is None:
    # Show instructions when no file is uploaded
    st.info("👆 Please upload a data file from the sidebar to get started!")
    
    st.markdown("""
    ### Expected File Format
    
    Your file should contain the following columns:
    - **Date**: Date of observation (any standard date format)
    - **River_basin_name**: Name of the river basin
    - **Station_name**: Station identifier
    - **Raw_median**: Raw flow measurement (optional)
    - **Step_2_median**: Step 2 flow measurement (optional)
    - **Final_median**: Final flow measurement (optional)
    - **OBS**: Observation values (optional, for BC vs Observation tab)
    - **BC_Factor**: Bias correction factor (optional, for BC vs Observation tab)

    """)
    
    st.stop()  # Stop execution until file is uploaded

# Load the data
df, basin_to_stations = load_data(uploaded_file, sheet_name)

if df is None or basin_to_stations is None:
    st.error("Failed to load data. Please check your file format.")
    st.stop()

# Show data info in sidebar
st.sidebar.success(f"✅ Loaded {len(df):,} rows")
st.sidebar.info(f"📊 {len(basin_to_stations)} basins found")
st.sidebar.info(f"📍 {df['Station_name'].nunique()} unique stations")

# Add data preview option
if st.sidebar.checkbox("Preview data", value=False):
    st.sidebar.dataframe(df.head(10), height=300)

all_basins = sorted(basin_to_stations.keys())
metric_options = ["Raw_median", "Step_2_median", "Final_median"]

# Filter to only show metrics that exist in the data
available_metrics = [m for m in metric_options if m in df.columns]
if not available_metrics:
    st.error("No valid metric columns found in the data. Expected: Raw_median, Step_2_median, or Final_median")
    st.stop()

# ------------ Controls ------------
col1, col2, col3 = st.columns([1, 1.5, 1])

with col1:
    selected_basin = st.selectbox(
        "Basin",
        options=all_basins,
        index=0 if all_basins else None
    )

with col2:
    available_stations = sorted(basin_to_stations.get(selected_basin, []))
    selected_stations = st.multiselect(
        "Stations",
        options=available_stations,
        default=available_stations  # Auto-select all stations
    )

with col3:
    selected_metrics = st.multiselect(
        "Metric(s)",
        options=available_metrics,
        default=[available_metrics[0]] if available_metrics else []
    )

# ------------ Tabs ------------
tab1, tab2, tab3, tab4 = st.tabs(["📈 Time-series", "📊 Pairwise Differences", "🔄 BC vs Observation", "📋 Per-Station Summary"])

# Filter data
if selected_basin and selected_stations:
    sub = df[(df["River_basin_name"] == selected_basin) & (df["Station_name"].isin(selected_stations))].copy()
else:
    sub = pd.DataFrame()

# ------------ TAB 1: Time Series ------------
with tab1:
    if sub.empty:
        st.warning("Select at least one station to view data.")
    elif not selected_metrics:
        st.warning("Select at least one metric.")
    else:
        ycols = [c for c in selected_metrics if c in sub.columns]
        if ycols:
            # Melt to long for multi-metric plotting
            plot_df = sub.melt(
                id_vars=["Date", "Station_name"],
                value_vars=ycols,
                var_name="Metric",
                value_name="Flow",
            )
            fig = px.line(
                plot_df,
                x="Date",
                y="Flow",
                color="Station_name",
                line_dash="Metric",
                markers=True,
                title=f"{selected_basin} – Time Series",
            )
            fig.update_layout(
                legend_title_text="Station • Metric",
                yaxis_title="Flow (CMS)",
                height=600
            )
            st.plotly_chart(fig, use_container_width=True)

# ------------ TAB 2: Pairwise Differences ------------
with tab2:
    if not sub.empty:
        # Difference controls
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            diff_metric = st.selectbox(
                "Difference metric",
                options=available_metrics,
                index=0
            )
        
        with col_b:
            up_station = st.selectbox(
                "Upstream station (for custom difference)",
                options=[None] + available_stations,
                format_func=lambda x: "(Optional)" if x is None else x
            )
        
        with col_c:
            down_station = st.selectbox(
                "Downstream station (for custom difference)",
                options=[None] + available_stations,
                format_func=lambda x: "(Optional)" if x is None else x
            )
        
        st.markdown("---")
        
        # Custom pair difference
        if up_station and down_station and up_station != down_station:
            up = df[(df["River_basin_name"] == selected_basin) & (df["Station_name"] == up_station)][["Date", diff_metric]]
            down = df[(df["River_basin_name"] == selected_basin) & (df["Station_name"] == down_station)][["Date", diff_metric]]
            m = pd.merge(up, down, on="Date", suffixes=("_up", "_down"))
            m["Diff"] = m[f"{diff_metric}_up"] - m[f"{diff_metric}_down"]
            
            fig = px.line(
                m, x="Date", y="Diff",
                title=f"{selected_basin} – Difference ({diff_metric}): {up_station} - {down_station}",
                markers=True
            )
            fig.update_layout(yaxis_title="Difference (CMS)", height=600)
            st.plotly_chart(fig, use_container_width=True)
        
        # Consecutive differences
        elif len(selected_stations) >= 2:
            stations_in_basin = basin_to_stations.get(selected_basin, [])
            order = [s for s in stations_in_basin if s in selected_stations]
            
            # Wide table for chosen metric
            wide = (
                df[(df["River_basin_name"] == selected_basin) & (df["Station_name"].isin(order))]
                .pivot_table(index="Date", columns="Station_name", values=diff_metric, aggfunc="first")
                .reindex(columns=order)
                .sort_index()
            )
            
            # Build a long frame with Dk columns
            rows = []
            for i in range(len(order) - 1):
                a, b = order[i], order[i + 1]
                dname = f"D{i+1}: {a} - {b}"
                series = wide[a] - wide[b]
                rows.append(series.rename(dname))
            
            if rows:
                diff_df = pd.concat(rows, axis=1).reset_index()
                long_df = diff_df.melt("Date", var_name="Pair", value_name="Diff")
                
                fig = px.line(
                    long_df, x="Date", y="Diff", color="Pair",
                    title=f"{selected_basin} – Consecutive Pairwise Differences ({diff_metric})",
                    markers=True
                )
                fig.update_layout(yaxis_title="Difference (CMS)", height=600)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Select at least two stations (or choose a custom pair above).")
    else:
        st.warning("Select at least one station to view differences.")

# ------------ TAB 3: BC vs Observation ------------
with tab3:
    if sub.empty:
        st.warning("Select at least one station to view data.")
    elif "OBS" not in sub.columns or "BC_Factor" not in sub.columns:
        st.warning("OBS / BC_Factor columns not found in the data.")
    else:
        fig = px.scatter(
            sub, x="OBS", y="BC_Factor", color="Station_name",
            trendline="ols", trendline_scope="overall",
            title=f"{selected_basin} – BC Factor vs OBS"
        )
        fig.update_layout(xaxis_title="OBS", yaxis_title="BC_Factor", height=600)
        st.plotly_chart(fig, use_container_width=True)

# ------------ TAB 4: Per-Station Summary ------------
with tab4:
    if sub.empty:
        st.warning("Select at least one station to view summary.")
    else:
        # Only use metrics that exist in the data
        summary_metrics = [m for m in ["Raw_median", "Step_2_median", "Final_median"] if m in sub.columns]
        
        if summary_metrics:
            sums = (
                sub.groupby("Station_name")[summary_metrics]
                .sum(min_count=1).reset_index()
            )
            avgs = (
                sub.groupby("Station_name")[summary_metrics]
                .mean().reset_index()
            )
            sums["Type"] = "Sum"
            avgs["Type"] = "Average"
            summary = pd.concat([sums, avgs], ignore_index=True)
            summary = summary.melt(
                id_vars=["Station_name", "Type"],
                value_vars=summary_metrics,
                var_name="Metric",
                value_name="Value"
            )
            
            fig = px.bar(
                summary, x="Station_name", y="Value", color="Metric",
                facet_col="Type", barmode="group",
                title=f"{selected_basin} – Per-Station Sums & Averages"
            )
            fig.update_layout(yaxis_title="Flow (CMS)", height=600)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No valid metrics found for summary.")

# ------------ Export Section ------------
st.markdown("---")
st.subheader("📥 Export Options")

col_export1, col_export2 = st.columns(2)

with col_export1:
    if st.button("Download Filtered Data as CSV", type="secondary"):
        if not sub.empty:
            csv = sub.to_csv(index=False)
            st.download_button(
                label="📄 Download CSV",
                data=csv,
                file_name=f"{selected_basin}_filtered_data.csv",
                mime="text/csv"
            )
        else:
            st.warning("No data to export. Select stations first.")

# ------------ Footer ------------
st.markdown("---")
st.caption("WRMM QA/QC Explorer | Built with Streamlit | 🌊 Upload your data to get started")