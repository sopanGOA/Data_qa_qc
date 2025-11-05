
# import pandas as pd
# import numpy as np
# import plotly.express as px
# import plotly.io as pio
# import streamlit as st

# # ------------ Page Config ------------
# st.set_page_config(page_title="WRMM QA/QC Explorer", layout="wide")

# # ------------ Header ------------
# st.title("🌊 WRMM QA/QC Explorer")

# # ------------ File Upload Section ------------
# st.sidebar.header("📁 Data Upload")
# uploaded_file = st.sidebar.file_uploader(
#     "Upload your data file",
#     type=["csv", "xlsx", "xls"],
#     help="Upload a CSV or Excel file with columns: Date, River_basin_name, Station_name, Raw_median, Step_2_median, Final_median"
# )

# # Add option to select sheet name for Excel files
# sheet_name = "Combined"
# if uploaded_file and uploaded_file.name.endswith(('.xlsx', '.xls')):
#     sheet_name = st.sidebar.text_input("Sheet name", value="Combined", help="Enter the name of the sheet to read from Excel file")

# # ------------ Load Data ------------
# @st.cache_data
# def load_data(file, sheet=None):
#     """Load data from uploaded file"""
#     try:
#         # Determine file type and read accordingly
#         if file.name.endswith('.csv'):
#             df = pd.read_csv(file)
#         elif file.name.endswith(('.xlsx', '.xls')):
#             df = pd.read_excel(file, sheet_name=sheet)
#         else:
#             st.error(f"Unsupported file type: {file.name}")
#             return None, None
        
#         # Convert Date column
#         df["Date"] = pd.to_datetime(df["Date"])
        
#         # Derive basin -> ordered station list
#         basin_to_stations = (
#             df[["River_basin_name", "Station_name"]]
#             .dropna()
#             .drop_duplicates()
#             .groupby("River_basin_name")["Station_name"]
#             .apply(list)
#             .to_dict()
#         )
        
#         return df, basin_to_stations
#     except Exception as e:
#         st.error(f"Error loading file: {str(e)}")
#         return None, None

# # ------------ Main App Logic ------------
# if uploaded_file is None:
#     # Show instructions when no file is uploaded
#     st.info("👆 Please upload a data file from the sidebar to get started!")
    
#     st.markdown("""
#     ### Expected File Format
    
#     Your file should contain the following columns:
#     - **Date**: Date of observation (any standard date format)
#     - **River_basin_name**: Name of the river basin
#     - **Station_name**: Station identifier
#     - **Raw_median**: Raw flow measurement (optional)
#     - **Step_2_median**: Step 2 flow measurement (optional)
#     - **Final_median**: Final flow measurement (optional)
#     - **OBS**: Observation values (optional, for BC vs Observation tab)
#     - **BC_Factor**: Bias correction factor (optional, for BC vs Observation tab)

#     """)
    
#     st.stop()  # Stop execution until file is uploaded

# # Load the data
# df, basin_to_stations = load_data(uploaded_file, sheet_name)

# if df is None or basin_to_stations is None:
#     st.error("Failed to load data. Please check your file format.")
#     st.stop()

# # Show data info in sidebar
# st.sidebar.success(f"✅ Loaded {len(df):,} rows")
# st.sidebar.info(f"📊 {len(basin_to_stations)} basins found")
# st.sidebar.info(f"📍 {df['Station_name'].nunique()} unique stations")

# # Add data preview option
# if st.sidebar.checkbox("Preview data", value=False):
#     st.sidebar.dataframe(df.head(10), height=300)

# all_basins = sorted(basin_to_stations.keys())
# metric_options = ["Raw_median", "Step_2_median", "Final_median"]

# # Filter to only show metrics that exist in the data
# available_metrics = [m for m in metric_options if m in df.columns]
# if not available_metrics:
#     st.error("No valid metric columns found in the data. Expected: Raw_median, Step_2_median, or Final_median")
#     st.stop()

# # ------------ Controls ------------
# col1, col2, col3 = st.columns([1, 1.5, 1])

# with col1:
#     selected_basin = st.selectbox(
#         "Basin",
#         options=all_basins,
#         index=0 if all_basins else None
#     )

# with col2:
#     available_stations = sorted(basin_to_stations.get(selected_basin, []))
#     selected_stations = st.multiselect(
#         "Stations",
#         options=available_stations,
#         default=available_stations  # Auto-select all stations
#     )

# with col3:
#     selected_metrics = st.multiselect(
#         "Metric(s)",
#         options=available_metrics,
#         default=[available_metrics[0]] if available_metrics else []
#     )

# # ------------ Tabs ------------
# tab1, tab2, tab3, tab4 = st.tabs(["📈 Time-series", "📊 Pairwise Differences", "🔄 BC vs Observation", "📋 Per-Station Summary"])

# # Filter data
# if selected_basin and selected_stations:
#     sub = df[(df["River_basin_name"] == selected_basin) & (df["Station_name"].isin(selected_stations))].copy()
# else:
#     sub = pd.DataFrame()

# # ------------ TAB 1: Time Series ------------
# with tab1:
#     if sub.empty:
#         st.warning("Select at least one station to view data.")
#     elif not selected_metrics:
#         st.warning("Select at least one metric.")
#     else:
#         ycols = [c for c in selected_metrics if c in sub.columns]
#         if ycols:
#             # Melt to long for multi-metric plotting
#             plot_df = sub.melt(
#                 id_vars=["Date", "Station_name"],
#                 value_vars=ycols,
#                 var_name="Metric",
#                 value_name="Flow",
#             )
#             fig = px.line(
#                 plot_df,
#                 x="Date",
#                 y="Flow",
#                 color="Station_name",
#                 line_dash="Metric",
#                 markers=True,
#                 title=f"{selected_basin} – Time Series",
#             )
#             fig.update_layout(
#                 legend_title_text="Station • Metric",
#                 yaxis_title="Flow (CMS)",
#                 height=600
#             )
#             st.plotly_chart(fig, use_container_width=True)

# # ------------ TAB 2: Pairwise Differences ------------
# with tab2:
#     if not sub.empty:
#         # Difference controls
#         col_a, col_b, col_c = st.columns(3)
        
#         with col_a:
#             diff_metric = st.selectbox(
#                 "Difference metric",
#                 options=available_metrics,
#                 index=0
#             )
        
#         with col_b:
#             up_station = st.selectbox(
#                 "Upstream station (for custom difference)",
#                 options=[None] + available_stations,
#                 format_func=lambda x: "(Optional)" if x is None else x
#             )
        
#         with col_c:
#             down_station = st.selectbox(
#                 "Downstream station (for custom difference)",
#                 options=[None] + available_stations,
#                 format_func=lambda x: "(Optional)" if x is None else x
#             )
        
#         st.markdown("---")
        
#         # Custom pair difference
#         if up_station and down_station and up_station != down_station:
#             up = df[(df["River_basin_name"] == selected_basin) & (df["Station_name"] == up_station)][["Date", diff_metric]]
#             down = df[(df["River_basin_name"] == selected_basin) & (df["Station_name"] == down_station)][["Date", diff_metric]]
#             m = pd.merge(up, down, on="Date", suffixes=("_up", "_down"))
#             m["Diff"] = m[f"{diff_metric}_up"] - m[f"{diff_metric}_down"]
            
#             fig = px.line(
#                 m, x="Date", y="Diff",
#                 title=f"{selected_basin} – Difference ({diff_metric}): {up_station} - {down_station}",
#                 markers=True
#             )
#             fig.update_layout(yaxis_title="Difference (CMS)", height=600)
#             st.plotly_chart(fig, use_container_width=True)
        
#         # Consecutive differences
#         elif len(selected_stations) >= 2:
#             stations_in_basin = basin_to_stations.get(selected_basin, [])
#             order = [s for s in stations_in_basin if s in selected_stations]
            
#             # Wide table for chosen metric
#             wide = (
#                 df[(df["River_basin_name"] == selected_basin) & (df["Station_name"].isin(order))]
#                 .pivot_table(index="Date", columns="Station_name", values=diff_metric, aggfunc="first")
#                 .reindex(columns=order)
#                 .sort_index()
#             )
            
#             # Build a long frame with Dk columns
#             rows = []
#             for i in range(len(order) - 1):
#                 a, b = order[i], order[i + 1]
#                 dname = f"D{i+1}: {a} - {b}"
#                 series = wide[a] - wide[b]
#                 rows.append(series.rename(dname))
            
#             if rows:
#                 diff_df = pd.concat(rows, axis=1).reset_index()
#                 long_df = diff_df.melt("Date", var_name="Pair", value_name="Diff")
                
#                 fig = px.line(
#                     long_df, x="Date", y="Diff", color="Pair",
#                     title=f"{selected_basin} – Consecutive Pairwise Differences ({diff_metric})",
#                     markers=True
#                 )
#                 fig.update_layout(yaxis_title="Difference (CMS)", height=600)
#                 st.plotly_chart(fig, use_container_width=True)
#         else:
#             st.warning("Select at least two stations (or choose a custom pair above).")
#     else:
#         st.warning("Select at least one station to view differences.")

# # ------------ TAB 3: BC vs Observation ------------
# with tab3:
#     if sub.empty:
#         st.warning("Select at least one station to view data.")
#     elif "OBS" not in sub.columns or "BC_Factor" not in sub.columns:
#         st.warning("OBS / BC_Factor columns not found in the data.")
#     else:
#         fig = px.scatter(
#             sub, x="OBS", y="BC_Factor", color="Station_name",
#             trendline="ols", trendline_scope="overall",
#             title=f"{selected_basin} – BC Factor vs OBS"
#         )
#         fig.update_layout(xaxis_title="OBS", yaxis_title="BC_Factor", height=600)
#         st.plotly_chart(fig, use_container_width=True)

# # ------------ TAB 4: Per-Station Summary ------------
# with tab4:
#     if sub.empty:
#         st.warning("Select at least one station to view summary.")
#     else:
#         # Only use metrics that exist in the data
#         summary_metrics = [m for m in ["Raw_median", "Step_2_median", "Final_median"] if m in sub.columns]
        
#         if summary_metrics:
#             sums = (
#                 sub.groupby("Station_name")[summary_metrics]
#                 .sum(min_count=1).reset_index()
#             )
#             avgs = (
#                 sub.groupby("Station_name")[summary_metrics]
#                 .mean().reset_index()
#             )
#             sums["Type"] = "Sum"
#             avgs["Type"] = "Average"
#             summary = pd.concat([sums, avgs], ignore_index=True)
#             summary = summary.melt(
#                 id_vars=["Station_name", "Type"],
#                 value_vars=summary_metrics,
#                 var_name="Metric",
#                 value_name="Value"
#             )
            
#             fig = px.bar(
#                 summary, x="Station_name", y="Value", color="Metric",
#                 facet_col="Type", barmode="group",
#                 title=f"{selected_basin} – Per-Station Sums & Averages"
#             )
#             fig.update_layout(yaxis_title="Flow (CMS)", height=600)
#             st.plotly_chart(fig, use_container_width=True)
#         else:
#             st.warning("No valid metrics found for summary.")

# # ------------ Export Section ------------
# st.markdown("---")
# st.subheader("📥 Export Options")

# col_export1, col_export2 = st.columns(2)

# with col_export1:
#     if st.button("Download Filtered Data as CSV", type="secondary"):
#         if not sub.empty:
#             csv = sub.to_csv(index=False)
#             st.download_button(
#                 label="📄 Download CSV",
#                 data=csv,
#                 file_name=f"{selected_basin}_filtered_data.csv",
#                 mime="text/csv"
#             )
#         else:
#             st.warning("No data to export. Select stations first.")

# # ------------ Footer ------------
# st.markdown("---")
# st.caption("WRMM QA/QC Explorer | Built with Streamlit | 🌊 Upload your data to get started")


import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
from datetime import datetime
import re

# ------------ Page Config ------------
st.set_page_config(page_title="WRMM Forecast Explorer", layout="wide")

# ------------ Header ------------
st.title("🌊 WRMM Forecast Explorer")

# ------------ Sidebar: File Upload Section ------------
st.sidebar.header("📁 Data Upload")

# Upload QA/QC data
st.sidebar.subheader("1. QA/QC Data")
qa_file = st.sidebar.file_uploader(
    "Upload QA/QC data file",
    type=["csv", "xlsx", "xls"],
    help="Upload a CSV or Excel file with columns: Date, River_basin_name, Station_name, Raw_median, Step_2_median, Final_median",
    key="qa_upload"
)

# Upload Forecast data
st.sidebar.subheader("2. Forecast Data")
forecast_file = st.sidebar.file_uploader(
    "Upload forecast data file",
    type=["csv", "xlsx", "xls"],
    help="Upload a CSV or Excel file with forecast data (Tmin, Tmax, Precip)",
    key="forecast_upload"
)

# Add option to select sheet name for Excel files
sheet_name_qa = "Combined"
sheet_name_forecast = "All_Stations_Enhanced_Format"

if qa_file and qa_file.name.endswith(('.xlsx', '.xls')):
    sheet_name_qa = st.sidebar.text_input("QA/QC Sheet name", value="Combined", help="Sheet name for QA/QC data")

if forecast_file and forecast_file.name.endswith(('.xlsx', '.xls')):
    sheet_name_forecast = st.sidebar.text_input("Forecast Sheet name", value="All_Stations_Enhanced_Format", help="Sheet name for forecast data")

# ------------ Helper Functions ------------
def parse_forecast_dates_from_filename(filename):
    """Extract forecast start and end dates from filename format: Data_for_Dashboard_YYYYMMDD_YYYYMMDD"""
    match = re.search(r'(\d{8})_(\d{8})', filename)
    if match:
        start_str = match.group(1)
        end_str = match.group(2)
        forecast_start = pd.to_datetime(start_str, format='%Y%m%d')
        forecast_end = pd.to_datetime(end_str, format='%Y%m%d')
        return forecast_start, forecast_end
    return None, None

@st.cache_data
def load_qa_data(file, sheet=None):
    """Load QA/QC data from uploaded file"""
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file, sheet_name=sheet)
        else:
            st.error(f"Unsupported file type: {file.name}")
            return None, None
        
        df["Date"] = pd.to_datetime(df["Date"])
        
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
        st.error(f"Error loading QA/QC file: {str(e)}")
        return None, None

@st.cache_data
def load_forecast_data(file, sheet=None):
    """Load forecast data from uploaded file"""
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file, sheet_name=sheet)
        else:
            st.error(f"Unsupported file type: {file.name}")
            return None, None, None, None
        
        df["Date"] = pd.to_datetime(df["Date"])
        
        # Parse forecast dates from filename
        forecast_start, forecast_end = parse_forecast_dates_from_filename(file.name)
        
        # Get unique stations - check multiple possible column names
        station_col = None
        for col_name in ['Station', 'Stations', 'Station_name', 'station', 'stations']:
            if col_name in df.columns:
                station_col = col_name
                break
        
        if station_col:
            stations = sorted(df[station_col].unique())
            # Standardize to 'Station' for consistency
            if station_col != 'Station':
                df = df.rename(columns={station_col: 'Station'})
        else:
            stations = []
        
        return df, forecast_start, forecast_end, stations
    except Exception as e:
        st.error(f"Error loading forecast file: {str(e)}")
        return None, None, None, None

def detect_metric_columns(df):
    """Detect available metric columns and their types"""
    metrics = {}
    
    # Standard forecast format
    for base in ['Precip', 'Tmax', 'Tmin']:
        if f'{base} M' in df.columns:
            metrics[base] = {
                'median': f'{base} M',
                'lq': f'{base} LQ' if f'{base} LQ' in df.columns else None,
                'uq': f'{base} UQ' if f'{base} UQ' in df.columns else None,
                'historical': f'Historical_{base}' if f'Historical_{base}' in df.columns else None,
                'name': base
            }
    
    # Generic format (Median, UL, LL)
    if 'Median' in df.columns:
        metrics['Generic'] = {
            'median': 'Median',
            'lq': 'LL' if 'LL' in df.columns else None,
            'uq': 'UL' if 'UL' in df.columns else None,
            'historical': None,
            'name': 'Value'
        }
    
    return metrics

def create_forecast_plot(df, metric_config, metric_name, forecast_start, stations_filter=None, show_confidence=True, show_historical=False):
    """Create a plotly figure with historical (light) and forecast (bright) data"""
    
    # If no forecast_start, use the midpoint of the date range
    if forecast_start is None:
        date_range = df['Date'].max() - df['Date'].min()
        forecast_start = df['Date'].min() + date_range / 2
    
    # Filter by stations if specified
    if stations_filter:
        df = df[df['Station'].isin(stations_filter)].copy()
    
    if df.empty:
        return None
    
    metric_col = metric_config['median']
    lq_col = metric_config['lq']
    uq_col = metric_config['uq']
    historical_col = metric_config.get('historical', None)
    
    # Split into historical and forecast based on date
    df_historical = df[df['Date'] < forecast_start].copy()
    df_forecast = df[df['Date'] >= forecast_start].copy()
    
    fig = go.Figure()
    
    # Get unique stations
    stations = df['Station'].unique()
    colors = px.colors.qualitative.Plotly
    
    for i, station in enumerate(stations):
        color = colors[i % len(colors)]
        
        # Historical data - only plot if show_historical is True
        if show_historical:
            if historical_col and historical_col in df.columns:
                # Use the dedicated historical column for all dates before forecast start
                hist_data = df_historical[df_historical['Station'] == station]
                if not hist_data.empty:
                    fig.add_trace(go.Scatter(
                        x=hist_data['Date'],
                        y=hist_data[historical_col],
                        mode='lines+markers',
                        name=f'{station} (Historical)',
                        line=dict(color=color, width=2, dash='dot'),
                        marker=dict(size=5, opacity=0.6),
                        opacity=0.6,
                        legendgroup=station,
                        showlegend=True
                    ))
            else:
                # Fallback: use median column for historical period
                hist_data = df_historical[df_historical['Station'] == station]
                if not hist_data.empty and metric_col in hist_data.columns:
                    fig.add_trace(go.Scatter(
                        x=hist_data['Date'],
                        y=hist_data[metric_col],
                        mode='lines+markers',
                        name=f'{station} (Historical)',
                        line=dict(color=color, width=2, dash='dot'),
                        marker=dict(size=5, opacity=0.6),
                        opacity=0.6,
                        legendgroup=station,
                        showlegend=True
                    ))
        
        # Forecast data (bright color) - always show
        forecast_data = df_forecast[df_forecast['Station'] == station]
        if not forecast_data.empty and metric_col in forecast_data.columns:
            fig.add_trace(go.Scatter(
                x=forecast_data['Date'],
                y=forecast_data[metric_col],
                mode='lines+markers',
                name=f'{station} (Forecast)',
                line=dict(color=color, width=3),
                marker=dict(size=6),
                opacity=1.0,
                legendgroup=station,
                showlegend=True
            ))
        
        # Add confidence intervals if requested and available
        if show_confidence and lq_col and uq_col:
            forecast_data_conf = df_forecast[df_forecast['Station'] == station]
            if not forecast_data_conf.empty:
                # Upper quartile line
                fig.add_trace(go.Scatter(
                    x=forecast_data_conf['Date'],
                    y=forecast_data_conf[uq_col],
                    mode='lines',
                    name=f'{station} (UQ)',
                    line=dict(color=color, width=1.5, dash='dash'),
                    opacity=0.5,
                    legendgroup=station,
                    showlegend=False
                ))
                
                # Lower quartile line
                fig.add_trace(go.Scatter(
                    x=forecast_data_conf['Date'],
                    y=forecast_data_conf[lq_col],
                    mode='lines',
                    name=f'{station} (LQ)',
                    line=dict(color=color, width=1.5, dash='dash'),
                    opacity=0.5,
                    legendgroup=station,
                    showlegend=False
                ))
    
    # Add vertical line at forecast start (only if showing historical data)
    if show_historical:
        fig.add_shape(
            type="line",
            x0=forecast_start,
            x1=forecast_start,
            y0=0,
            y1=1,
            yref="paper",
            line=dict(color="red", width=2, dash="dash")
        )
        
        fig.add_annotation(
            x=forecast_start,
            y=1,
            yref="paper",
            text="Forecast Start",
            showarrow=False,
            yshift=10,
            font=dict(color="red", size=12)
        )
    
    # Set x-axis range based on show_historical toggle
    if show_historical:
        # Show full time range (historical + forecast)
        x_range = None  # Auto range
    else:
        # Show only forecast period
        if not df_forecast.empty:
            x_range = [df_forecast['Date'].min(), df_forecast['Date'].max()]
        else:
            x_range = None
    
    title_suffix = " - Historical vs Forecast" if show_historical else " - Forecast"
    
    fig.update_layout(
        title=f"{metric_name}{title_suffix}",
        xaxis_title="Date",
        yaxis_title=metric_name,
        height=600,
        hovermode='x unified',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.01
        )
    )
    
    # Apply x-axis range if specified
    if x_range:
        fig.update_xaxes(range=x_range)
    
    return fig

# ------------ Main App ------------

# Show welcome message if no files uploaded
if forecast_file is None and qa_file is None:
    st.info("👆 Please upload data files from the sidebar to get started!")
    
    st.markdown("""
    ### 📊 Available Dashboards
    
    #### 1. **Forecast Data Dashboard** (Upload Forecast Data)
    - The input data file name should be `Data_for_Dashboard_yyyymmdd_yyyymmdd.xlsx`
    - Visualize precipitation and temperature forecasts
    - Compare historical vs forecast data
    - View confidence intervals (LQ, M, UQ)
    - Multiple stations support
    
    #### 2. **QA/QC Dashboard** (Upload QA/QC Data)
    - Input filename should be `RiverBasin_Flows_Combined_yyyymmdd_yyyymmdd.xlsx`
    - Time-series analysis
    - Pairwise differences
    - BC vs Observation analysis
    - Per-station summaries
    """)
    
    st.stop()

# ------------ FORECAST DATA DASHBOARD ------------
if forecast_file is not None:
    st.header("📈 Forecast Data Dashboard")
    
    # Load forecast data
    forecast_df, forecast_start, forecast_end, forecast_stations = load_forecast_data(forecast_file, sheet_name_forecast)
    
    if forecast_df is None:
        st.error("Failed to load forecast data. Please check your file format.")
    else:
        # Detect available metrics
        available_metrics = detect_metric_columns(forecast_df)
        
        # Show data info
        col_info1, col_info2, col_info3, col_info4 = st.columns(4)
        with col_info1:
            st.metric("Total Records", f"{len(forecast_df):,}")
        with col_info2:
            st.metric("Stations", len(forecast_stations))
        with col_info3:
            if forecast_start:
                st.metric("Forecast Start", forecast_start.strftime('%Y-%m-%d'))
            else:
                st.warning("⚠️ Dates not detected")
        with col_info4:
            st.metric("Date Range", f"{(forecast_df['Date'].max() - forecast_df['Date'].min()).days} days")
        
        # Check if stations were found
        if not forecast_stations:
            st.error("❌ No stations found in the data. Please check that your file has a 'Station', 'Stations', or 'Station_name' column.")
            st.info("**Available columns:** " + ", ".join(forecast_df.columns.tolist()))
            st.stop()
        
        # Check if metrics were found
        if not available_metrics:
            st.error("❌ No recognized metric columns found in the data.")
            st.info("Expected columns like: Precip M, Tmax M, Tmin M OR Median, UL, LL")
            st.info("**Available columns:** " + ", ".join(forecast_df.columns.tolist()))
            st.stop()
        
        # Station filter
        st.subheader("Station Selection")
        selected_stations = st.multiselect(
            "Select stations to display",
            options=forecast_stations,
            default=forecast_stations[:5] if len(forecast_stations) > 5 else forecast_stations,
            help="Select one or more stations to display in the charts"
        )
        
        # Validate station selection
        if not selected_stations:
            st.warning("⚠️ Please select at least one station to display the charts.")
            st.stop()
        
        # Display options
        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            show_historical = st.checkbox("Show historical data", value=False, help="Toggle to show historical data along with forecast")
        with col_opt2:
            show_confidence = st.checkbox("Show confidence intervals (LQ/UQ or LL/UL)", value=True)
        
        # Create tabs based on available metrics
        if 'Precip' in available_metrics and 'Tmax' in available_metrics and 'Tmin' in available_metrics:
            # Standard format with Precip, Tmax, Tmin
            tab_precip, tab_tmax, tab_tmin, tab_data = st.tabs([
                "🌧️ Precipitation",
                "🌡️ Temperature Max",
                "❄️ Temperature Min",
                "📋 Data Table"
            ])
            
            with tab_precip:
                fig = create_forecast_plot(
                    forecast_df,
                    available_metrics['Precip'],
                    'Precipitation (mm)',
                    forecast_start if forecast_start else forecast_df['Date'].min(),
                    selected_stations,
                    show_confidence,
                    show_historical
                )
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.subheader("Summary Statistics")
                    filtered_df = forecast_df[forecast_df['Station'].isin(selected_stations)]
                    if forecast_start:
                        forecast_data = filtered_df[filtered_df['Date'] >= forecast_start]
                    else:
                        forecast_data = filtered_df
                    
                    if not forecast_data.empty:
                        metric_col = available_metrics['Precip']['median']
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Average", f"{forecast_data[metric_col].mean():.2f} mm")
                        with col2:
                            st.metric("Max", f"{forecast_data[metric_col].max():.2f} mm")
                        with col3:
                            st.metric("Total", f"{forecast_data[metric_col].sum():.2f} mm")
            
            with tab_tmax:
                fig = create_forecast_plot(
                    forecast_df,
                    available_metrics['Tmax'],
                    'Temperature Max (°C)',
                    forecast_start if forecast_start else forecast_df['Date'].min(),
                    selected_stations,
                    show_confidence,
                    show_historical
                )
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.subheader("Summary Statistics")
                    filtered_df = forecast_df[forecast_df['Station'].isin(selected_stations)]
                    if forecast_start:
                        forecast_data = filtered_df[filtered_df['Date'] >= forecast_start]
                    else:
                        forecast_data = filtered_df
                    
                    if not forecast_data.empty:
                        metric_col = available_metrics['Tmax']['median']
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Average", f"{forecast_data[metric_col].mean():.2f} °C")
                        with col2:
                            st.metric("Max", f"{forecast_data[metric_col].max():.2f} °C")
                        with col3:
                            st.metric("Min", f"{forecast_data[metric_col].min():.2f} °C")
            
            with tab_tmin:
                fig = create_forecast_plot(
                    forecast_df,
                    available_metrics['Tmin'],
                    'Temperature Min (°C)',
                    forecast_start if forecast_start else forecast_df['Date'].min(),
                    selected_stations,
                    show_confidence,
                    show_historical
                )
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.subheader("Summary Statistics")
                    filtered_df = forecast_df[forecast_df['Station'].isin(selected_stations)]
                    if forecast_start:
                        forecast_data = filtered_df[filtered_df['Date'] >= forecast_start]
                    else:
                        forecast_data = filtered_df
                    
                    if not forecast_data.empty:
                        metric_col = available_metrics['Tmin']['median']
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Average", f"{forecast_data[metric_col].mean():.2f} °C")
                        with col2:
                            st.metric("Max", f"{forecast_data[metric_col].max():.2f} °C")
                        with col3:
                            st.metric("Min", f"{forecast_data[metric_col].min():.2f} °C")
            
            with tab_data:
                st.subheader("Raw Data Preview")
                display_df = forecast_df[forecast_df['Station'].isin(selected_stations)].copy()
                st.dataframe(display_df, height=400, use_container_width=True)
                
                csv = display_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Filtered Data as CSV",
                    data=csv,
                    file_name="forecast_data_filtered.csv",
                    mime="text/csv"
                )
        
        elif 'Generic' in available_metrics:
            # Generic format with Median, UL, LL
            tab_plot, tab_data = st.tabs(["📈 Forecast Plot", "📋 Data Table"])
            
            with tab_plot:
                fig = create_forecast_plot(
                    forecast_df,
                    available_metrics['Generic'],
                    'Forecast Value',
                    forecast_start if forecast_start else forecast_df['Date'].min(),
                    selected_stations,
                    show_confidence,
                    show_historical
                )
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.subheader("Summary Statistics")
                    filtered_df = forecast_df[forecast_df['Station'].isin(selected_stations)]
                    if forecast_start:
                        forecast_data = filtered_df[filtered_df['Date'] >= forecast_start]
                    else:
                        forecast_data = filtered_df
                    
                    if not forecast_data.empty:
                        metric_col = available_metrics['Generic']['median']
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Average", f"{forecast_data[metric_col].mean():.2f}")
                        with col2:
                            st.metric("Max", f"{forecast_data[metric_col].max():.2f}")
                        with col3:
                            st.metric("Min", f"{forecast_data[metric_col].min():.2f}")
                else:
                    st.warning("No data to display for selected stations.")
            
            with tab_data:
                st.subheader("Raw Data Preview")
                display_df = forecast_df[forecast_df['Station'].isin(selected_stations)].copy()
                st.dataframe(display_df, height=400, use_container_width=True)
                
                csv = display_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Filtered Data as CSV",
                    data=csv,
                    file_name="forecast_data_filtered.csv",
                    mime="text/csv"
                )

# ------------ QA/QC DATA DASHBOARD ------------
if qa_file is not None:
    st.header("🔍 QA/QC Data Dashboard")
    
    qa_df, basin_to_stations = load_qa_data(qa_file, sheet_name_qa)
    
    if qa_df is None:
        st.error("Failed to load QA/QC data. Please check your file format.")
    else:
        st.sidebar.success(f"✅ Loaded {len(qa_df):,} rows")
        st.sidebar.info(f"📊 {len(basin_to_stations)} basins found")
        st.sidebar.info(f"📍 {qa_df['Station_name'].nunique()} unique stations")
        
        all_basins = sorted(basin_to_stations.keys())
        metric_options = ["Raw_median", "Step_2_median", "Final_median"]
        available_metrics = [m for m in metric_options if m in qa_df.columns]
        
        if not available_metrics:
            st.error("No valid metric columns found in the data.")
        else:
            col1, col2, col3 = st.columns([1, 1.5, 1])
            
            with col1:
                selected_basin = st.selectbox("Basin", options=all_basins, index=0 if all_basins else None)
            
            with col2:
                available_stations = sorted(basin_to_stations.get(selected_basin, []))
                selected_qa_stations = st.multiselect("Stations", options=available_stations, default=available_stations)
            
            with col3:
                selected_metrics = st.multiselect("Metric(s)", options=available_metrics, default=[available_metrics[0]] if available_metrics else [])
            
            if selected_basin and selected_qa_stations:
                sub = qa_df[(qa_df["River_basin_name"] == selected_basin) & (qa_df["Station_name"].isin(selected_qa_stations))].copy()
            else:
                sub = pd.DataFrame()
            
            tab1, tab2, tab3, tab4 = st.tabs(["📈 Time-series", "📊 Pairwise Differences", "🔄 BC vs Observation", "📋 Per-Station Summary"])
            
            with tab1:
                if sub.empty:
                    st.warning("Select at least one station to view data.")
                elif not selected_metrics:
                    st.warning("Select at least one metric.")
                else:
                    ycols = [c for c in selected_metrics if c in sub.columns]
                    if ycols:
                        plot_df = sub.melt(id_vars=["Date", "Station_name"], value_vars=ycols, var_name="Metric", value_name="Flow")
                        fig = px.line(plot_df, x="Date", y="Flow", color="Station_name", line_dash="Metric", markers=True, title=f"{selected_basin} – Time Series")
                        fig.update_layout(legend_title_text="Station • Metric", yaxis_title="Flow (CMS)", height=600)
                        st.plotly_chart(fig, use_container_width=True)
            
            with tab2:
                if not sub.empty:
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        diff_metric = st.selectbox("Difference metric", options=available_metrics, index=0)
                    with col_b:
                        up_station = st.selectbox("Upstream station", options=[None] + available_stations, format_func=lambda x: "(Optional)" if x is None else x)
                    with col_c:
                        down_station = st.selectbox("Downstream station", options=[None] + available_stations, format_func=lambda x: "(Optional)" if x is None else x)
                    
                    st.markdown("---")
                    
                    if up_station and down_station and up_station != down_station:
                        up = qa_df[(qa_df["River_basin_name"] == selected_basin) & (qa_df["Station_name"] == up_station)][["Date", diff_metric]]
                        down = qa_df[(qa_df["River_basin_name"] == selected_basin) & (qa_df["Station_name"] == down_station)][["Date", diff_metric]]
                        m = pd.merge(up, down, on="Date", suffixes=("_up", "_down"))
                        m["Diff"] = m[f"{diff_metric}_up"] - m[f"{diff_metric}_down"]
                        fig = px.line(m, x="Date", y="Diff", title=f"{selected_basin} – Difference ({diff_metric}): {up_station} - {down_station}", markers=True)
                        fig.update_layout(yaxis_title="Difference (CMS)", height=600)
                        st.plotly_chart(fig, use_container_width=True)
                    elif len(selected_qa_stations) >= 2:
                        stations_in_basin = basin_to_stations.get(selected_basin, [])
                        order = [s for s in stations_in_basin if s in selected_qa_stations]
                        wide = qa_df[(qa_df["River_basin_name"] == selected_basin) & (qa_df["Station_name"].isin(order))].pivot_table(index="Date", columns="Station_name", values=diff_metric, aggfunc="first").reindex(columns=order).sort_index()
                        rows = []
                        for i in range(len(order) - 1):
                            a, b = order[i], order[i + 1]
                            dname = f"D{i+1}: {a} - {b}"
                            series = wide[a] - wide[b]
                            rows.append(series.rename(dname))
                        if rows:
                            diff_df = pd.concat(rows, axis=1).reset_index()
                            long_df = diff_df.melt("Date", var_name="Pair", value_name="Diff")
                            fig = px.line(long_df, x="Date", y="Diff", color="Pair", title=f"{selected_basin} – Consecutive Pairwise Differences ({diff_metric})", markers=True)
                            fig.update_layout(yaxis_title="Difference (CMS)", height=600)
                            st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("Select at least two stations.")
                else:
                    st.warning("Select at least one station to view differences.")
            
            with tab3:
                if sub.empty:
                    st.warning("Select at least one station to view data.")
                elif "OBS" not in sub.columns or "BC_Factor" not in sub.columns:
                    st.warning("OBS / BC_Factor columns not found in the data.")
                else:
                    fig = px.scatter(sub, x="OBS", y="BC_Factor", color="Station_name", trendline="ols", trendline_scope="overall", title=f"{selected_basin} – BC Factor vs OBS")
                    fig.update_layout(xaxis_title="OBS", yaxis_title="BC_Factor", height=600)
                    st.plotly_chart(fig, use_container_width=True)
            
            with tab4:
                if sub.empty:
                    st.warning("Select at least one station to view summary.")
                else:
                    summary_metrics = [m for m in ["Raw_median", "Step_2_median", "Final_median"] if m in sub.columns]
                    if summary_metrics:
                        sums = sub.groupby("Station_name")[summary_metrics].sum(min_count=1).reset_index()
                        avgs = sub.groupby("Station_name")[summary_metrics].mean().reset_index()
                        sums["Type"] = "Sum"
                        avgs["Type"] = "Average"
                        summary = pd.concat([sums, avgs], ignore_index=True)
                        summary = summary.melt(id_vars=["Station_name", "Type"], value_vars=summary_metrics, var_name="Metric", value_name="Value")
                        fig = px.bar(summary, x="Station_name", y="Value", color="Metric", facet_col="Type", barmode="group", title=f"{selected_basin} – Per-Station Sums & Averages")
                        fig.update_layout(yaxis_title="Flow (CMS)", height=600)
                        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.caption("WRMM Forecast Explorer | Built with Streamlit | 🌊 Upload your data to get started")