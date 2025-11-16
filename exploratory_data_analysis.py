from custom_data_load import read_excel_file

file_path = "l_o_freq_request_data.xlsx"
df = read_excel_file(file_path, sheet_name="Emissions from P&T Proc by Chem")



#Rename columns:

df.rename(columns={
    'Fluorinated GHG Emissions (metric tons)': 'Emissions_metric_tons',
    'Fluorinated GHG Emissions\n(mt CO2e)': 'Emissions_mtCO2e'
}, inplace=True)




import matplotlib.pyplot as plt

df.plot("Emissions_metric_tons", "Emissions_mtCO2e", kind="scatter", figsize=(12,3), title="Emissions vs Consumption", ax=plt.subplot(133), color='#28b463')


print(df.head(20))