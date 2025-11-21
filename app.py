import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# ====== Config ======
CLIMATIQ_API_KEY = "ANKDEMM85D3PDCD4NMQ3FPJNS0"
API_URL = "https://api.climatiq.io/data/v1/estimate"

# ====== Function to estimate CO2e ======
def estimate_chemical_emission(activity_id, weight_kg, api_key=CLIMATIQ_API_KEY):
    """
    Call Climatiq API to estimate CO2e for a given fluorinated GHG.
    Returns CO2e in kg.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "emission_factor": {"activity_id": activity_id},
        "parameters": {"weight": weight_kg, "weight_unit": "kg"}
    }

    try:
        response = requests.post(API_URL, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        co2e = result.get("co2e", {}).get("value")
        if co2e is None:
            st.warning(f"No CO2e returned for {activity_id} with weight {weight_kg} kg.")
        return co2e
    except requests.exceptions.RequestException as e:
        st.warning(f"API request failed for {activity_id} with weight {weight_kg} kg: {e}")
        return None

# ====== Streamlit UI ======
st.title("Fluorinated GHG CO₂e Estimator")
st.write("Upload an Excel file with your fluorinated GHG emissions and get CO₂e estimates.")

uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])

if uploaded_file:
    # Read Excel sheet
    try:
        df = pd.read_excel(uploaded_file, sheet_name="Emissions from P&T Proc by Chem")
    except Exception as e:
        st.error(f"Failed to read Excel file: {e}")
        st.stop()

    # Rename columns for easier handling
    df.rename(columns={
        'Fluorinated GHG Emissions (metric tons)': 'Emissions_metric_tons',
        'Fluorinated GHG Emissions\n(mt CO2e)': 'Emissions_mtCO2e'
    }, inplace=True)

    # Map supported gases to Climatiq activity IDs
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

    # Map activity IDs and calculate weight in kg
    df['activity_id'] = df['Fluorinated GHG Name'].map(activity_mapping)
    df_supported = df.dropna(subset=['activity_id']).copy()
    df_supported['weight_kg'] = df_supported['Emissions_metric_tons'] * 1000

    # Estimate CO2e per row
    st.info("Estimating CO₂e for supported GHGs...")
    df_supported['CO2e_kg'] = df_supported.apply(
        lambda row: estimate_chemical_emission(row['activity_id'], row['weight_kg']),
        axis=1
    )

    # Display results
    st.subheader("Results")
    st.dataframe(df_supported[['Fluorinated GHG Name', 'Emissions_metric_tons', 'CO2e_kg']])

    # Provide download button
    output = BytesIO()
    df_supported.to_excel(output, index=False)
    output.seek(0)
    st.download_button(
        "Download results as Excel",
        data=output,
        file_name="emissions_with_CO2e.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
