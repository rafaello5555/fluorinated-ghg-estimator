import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from custom_data_load import read_excel_file  # your custom loader

# ====== Config ======
CLIMATIQ_API_KEY = "ANKDEMM85D3PDCD4NMQ3FPJNS0"
API_URL = "https://api.climatiq.io/data/v1/estimate"

# ====== Function to estimate CO2e ======
def estimate_chemical_emission(activity_id, weight_kg, api_key=CLIMATIQ_API_KEY):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "emission_factor": {
            "activity_id": activity_id
            # optionally, you can add "data_version": "27.27" if known to be valid
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
            st.warning(f"No CO2e returned for {activity_id} with weight {weight_kg}. Response: {result}")
        return co2e
    except requests.exceptions.RequestException as e:
        st.warning(f"API request failed for {activity_id} with weight {weight_kg}: {e}")
        return None

# ====== Streamlit UI ======
st.title("Fluorinated GHG CO2e Estimator")

uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])

if uploaded_file:
    df = read_excel_file(uploaded_file, sheet_name="Emissions from P&T Proc by Chem")

    # Rename columns
    df.rename(columns={
        'Fluorinated GHG Emissions (metric tons)': 'Emissions_metric_tons',
        'Fluorinated GHG Emissions\n(mt CO2e)': 'Emissions_mtCO2e'
    }, inplace=True)

    # Map supported gases
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

    # Estimate CO2e per activity
    co2e_results = {}
    for _, row in grouped.iterrows():
        co2e_results[row['activity_id']] = estimate_chemical_emission(row['activity_id'], row['weight_kg'])

    # Map CO2e back to original DataFrame proportionally
    df_supported['CO2e_kg'] = df_supported.apply(
        lambda row: co2e_results[row['activity_id']] * (row['weight_kg'] / grouped.loc[grouped['activity_id']==row['activity_id'], 'weight_kg'].values[0])
        if row['activity_id'] in co2e_results and co2e_results[row['activity_id']] is not None else None,
        axis=1
    )

    # Show results
    st.subheader("Results")
    st.dataframe(df_supported[['Fluorinated GHG Name', 'Emissions_metric_tons', 'CO2e_kg']])

    # Download button
    output = BytesIO()
    df_supported.to_excel(output, index=False)
    output.seek(0)
    st.download_button("Download results as Excel", data=output, file_name="emissions_with_CO2e.xlsx")
