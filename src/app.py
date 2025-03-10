import streamlit as st
import pandas as pd
from database import engine

st.title("📊 IPTU Checker: Satellite-Based Land Analysis")

query = "SELECT * FROM land_records"
df = pd.read_sql(query, engine)

st.write("📍 **Analyzed Land Data**")
st.dataframe(df)
st.bar_chart(df[['real_area', 'registered_area']])
