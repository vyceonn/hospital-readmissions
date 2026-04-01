import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3

st.set_page_config(page_title="Hospital Readmissions Dashboard", layout="wide")
st.title("🏥 Hospital Readmissions Analysis")
st.markdown("Analyzing 70,000+ diabetic patient encounters to identify readmission risk factors.")

# Load data
@st.cache_data
def load_data():
    conn = sqlite3.connect('hospital.db')
    df = pd.read_sql_query("SELECT * FROM readmissions", conn)
    conn.close()
    return df

df = load_data()

# Sidebar filters
st.sidebar.header("Filters")
age_filter = st.sidebar.slider("Age Range", int(df['age'].min()), int(df['age'].max()), (20, 80))
gender_filter = st.sidebar.multiselect("Gender", df['gender'].unique(), default=df['gender'].unique())

# Apply filters
filtered = df[(df['age'].between(age_filter[0], age_filter[1])) & (df['gender'].isin(gender_filter))]

# KPI metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Patients", f"{len(filtered):,}")
col2.metric("Readmission Rate", f"{filtered['readmitted'].mean():.1%}")
col3.metric("Avg Days in Hospital", f"{filtered['time_in_hospital'].mean():.1f}")
col4.metric("Avg Medications", f"{filtered['num_medications'].mean():.1f}")

st.divider()

# Charts
col1, col2 = st.columns(2)

with col1:
    st.subheader("Readmission Rate by Age Group")
    age_bins = pd.cut(filtered['age'], bins=[0,40,60,100], labels=['Under 40','40-60','Over 60'])
    age_data = filtered.groupby(age_bins, observed=True)['readmitted'].mean().reset_index()
    age_data.columns = ['Age Group', 'Readmission Rate']
    fig = px.bar(age_data, x='Age Group', y='Readmission Rate', color='Age Group',
                 color_discrete_sequence=px.colors.qualitative.Set2)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Time in Hospital Distribution")
    fig2 = px.histogram(filtered, x='time_in_hospital', color='gender',
                        barmode='overlay', nbins=14,
                        color_discrete_sequence=px.colors.qualitative.Set2)
    st.plotly_chart(fig2, use_container_width=True)

col3, col4 = st.columns(2)

with col3:
    st.subheader("Readmission Rate by Race")
    race_data = filtered.groupby('race')['readmitted'].mean().reset_index()
    race_data.columns = ['Race', 'Readmission Rate']
    fig3 = px.bar(race_data, x='Race', y='Readmission Rate',
                  color_discrete_sequence=px.colors.qualitative.Set2)
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.subheader("Medications vs Hospital Stay")
    fig4 = px.scatter(filtered.sample(2000), x='num_medications', y='time_in_hospital',
                      color='readmitted', opacity=0.5,
                      color_discrete_sequence=px.colors.qualitative.Set2)
    st.plotly_chart(fig4, use_container_width=True)

st.caption("Data source: UCI Diabetes 130-US Hospitals Dataset (1999-2008)")