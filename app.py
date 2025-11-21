import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from custom_data_load import read_excel_file
from tqdm import tqdm

# ====== Config ======
CLIMATIQ_API_KEY = "ANKDEMM85D3PDCD4NMQ3FPJNS0"
API_URL = "https://api.climatiq.io/data/v1/estimate"

# ====== Function to estimate CO2e for a single chemical ======
def estimate_chemical_emission(activity_id, weight_kg, api_key=CLIMATIQ_API_KEY):
    """
    Estimate CO2e (kg) for a given chemical using Climatiq API.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "emission_factor": {
            "activity_id": activity_id,
            "data_version": "27.27"
        },
        "parameters": {
            "weight": weight_kg,
            "weight_unit": "kg"
        }
    }
    try:
        response = requests.post(API_URL, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        co2e = result.get("co2e", {}).get("value")
        if co2e is None:
            st.warning(f"No CO2e returned for {activity_id} ({weight_kg} kg).")
        return co2e
    except requests.exceptions.RequestException as e:
        st.warning(f"API request failed for {activity_id} ({weight_kg} kg): {e}")
        return None

# ====== Streamlit UI ======
st.title("Fluorinated GHG CO2e Estimator")
st.write("Upload an Excel file to estimate CO2e for fluorinated greenhouse gases.")

uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])

if uploaded_file:
    # Read Excel
    df = read_excel_file(uploaded_file, sheet_name="Emissions from P&T Proc by Chem")
    df.rename(columns={
        'Fluorinated GHG Emissions (metric tons)': 'Emissions_metric_tons',
        'Fluorinated GHG Emissions\n(mt CO2e)': 'Emissions_mtCO2e'
    }, inplace=True)

    # Activity mapping
    activity_mapping = {
        "HFC-227ea": "fugitive-hfc-227ea",
        "HFC-23": "fugitive-hfc-23",
        "HFC-236fa": "fugitive-hfc-236fa",
        "HFC-125": "fugitive-hfc-125",
        "HFC-143a": "fugitive-hfc-143a",
        "HFC-134a": "fugitive-hfc-134a",
        "HFC-32": "fugitive-hfc-32",
        "HFC-404A": "fugitive-hfc-404a",
        "HFC-407C": "fugitive-hfc-407c",
        "HFC-410A": "fugitive-hfc-410a",
        "R-22": "fugitive-hcfc-22"
    }

    df['activity_id'] = df['Fluorinated GHG Name'].map(activity_mapping)
    df_supported = df.dropna(subset=['activity_id']).copy()
    df_supported['weight_kg'] = df_supported['Emissions_metric_tons'] * 1000

    # Group by activity to reduce API calls
    grouped = df_supported.groupby('activity_id')['weight_kg'].sum().reset_index()

    # Progress bar in Streamlit
    st.info("Estimating CO2e for each chemical...")
    co2e_results = {}
    progress_bar = st.progress(0)
    for idx, (_, row) in enumerate(grouped.iterrows()):
        co2e_results[row['activity_id']] = estimate_chemical_emission(row['activity_id'], row['weight_kg'])
        progress_bar.progress((idx + 1) / len(grouped))

    # Map CO2e back to original DataFrame
    df_supported['CO2e_kg'] = df_supported['activity_id'].map(co2e_results)

    # Display results
    st.subheader("Results")
    st.dataframe(df_supported[['Fluorinated GHG Name', 'Emissions_metric_tons', 'CO2e_kg']])

    # Download button
    output = BytesIO()
    df_supported.to_excel(output, index=False)
    output.seek(0)
    st.download_button(
        "Download results as Excel",
        data=output,
        file_name="emissions_with_CO2e.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
