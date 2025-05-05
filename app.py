import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(layout="wide")
st.title("📈 Trading Growth Tracker")

# ==== Sidebar Inputs ====
st.sidebar.header("💼 Input Parameters")
starting_capital = st.sidebar.number_input("Starting Capital ($)", value=40000)
daily_rate = st.sidebar.number_input("Daily Earning Rate (%)", value=10.0) / 100
takeout_percent = st.sidebar.slider("Weekly Takeout (%)", 0, 100, 0)
daily_takeout_percent = st.sidebar.slider("Daily Profit Takeout (% of Daily Gains)", 0, 100, 0)
months = st.sidebar.radio("Months", [0] + list(range(1, 13)), index=0)
weeks = st.sidebar.radio("Additional Weeks", list(range(0, 13)), index=1)
conversion_rate = st.sidebar.number_input("USD to INR Conversion Rate", value=64.0)

# ==== Constants ====
trading_days_per_month = 20
trading_days_per_week = 5

total_trading_days = (months * trading_days_per_month) + (weeks * trading_days_per_week)
start_date = datetime.today()

# ==== Generate Trading Dates (Weekdays Only) ====
dates = []
current = start_date
while len(dates) < total_trading_days:
    if current.weekday() < 5:
        dates.append(current)
    current += timedelta(days=1)

# ==== Simulation ====
capital = starting_capital
capital_history = []
daily_takeout_history = []
weekly_takeout_history = []
cumulative_takeout_history = []
cumulative_takeout = 0

for i, date in enumerate(dates):
    capital_before = capital
    profit = capital_before * daily_rate
    daily_takeout = profit * (daily_takeout_percent / 100)
    capital += (profit - daily_takeout)
    cumulative_takeout += daily_takeout

    weekly_takeout = 0
    if (i + 1) % trading_days_per_week == 0:
        weekly_takeout = capital * (takeout_percent / 100)
        capital -= weekly_takeout
        cumulative_takeout += weekly_takeout

    capital_history.append(capital)
    daily_takeout_history.append(daily_takeout)
    weekly_takeout_history.append(weekly_takeout)
    cumulative_takeout_history.append(cumulative_takeout)

# ==== Convert Data ====
df = pd.DataFrame({
    "Date": dates,
    "Capital": capital_history,
    "Daily Takeout": daily_takeout_history,
    "Weekly Takeout": weekly_takeout_history,
    "Cumulative Takeout": cumulative_takeout_history,
})
df["Day"] = df["Date"].dt.strftime("%a, %b %d")

# ==== Format Helpers ====
def format_yaxis(value):
    if value >= 1e9:
        return f"${value/1e9:.2f}B"
    elif value >= 1e6:
        return f"${value/1e6:.2f}M"
    elif value >= 1e3:
        return f"${value/1e3:.2f}K"
    else:
        return f"${value:.2f}"

def format_inr(value):
    s = str(int(round(value)))
    if len(s) <= 3:
        return f"₹{s}"
    else:
        last3 = s[-3:]
        rest = s[:-3]
        rest_with_commas = ""
        while len(rest) > 2:
            rest_with_commas = "," + rest[-2:] + rest_with_commas
            rest = rest[:-2]
        rest_with_commas = rest + rest_with_commas
        return f"₹{rest_with_commas},{last3}"

# ==== Summary ====
st.subheader("📌 Summary")
st.metric("Starting Capital (INR)", format_inr(starting_capital * conversion_rate))

col1, col2 = st.columns(2)
col1.metric("Final Capital in INR", format_inr(df["Capital"].iloc[-1] * conversion_rate))
col2.metric("Final Capital in MooMoo ($)", format_yaxis(df["Capital"].iloc[-1]))

col3, col4 = st.columns(2)
col3.metric("Total Taken Out (INR)", format_inr(df["Cumulative Takeout"].iloc[-1] * conversion_rate))
col4.metric("Total Taken Out ($)", format_yaxis(df["Cumulative Takeout"].iloc[-1]))

# ==== Weekend Highlights ====
weekend_shapes = []
for i in range(len(df) - 1):
    if df["Date"].iloc[i].weekday() == 4:  # Friday
        start_x = df["Date"].iloc[i] + timedelta(days=1)
        end_x = df["Date"].iloc[i] + timedelta(days=3)
        weekend_shapes.append(dict(
            type="rect",
            xref="x",
            yref="paper",
            x0=start_x,
            x1=end_x,
            y0=0,
            y1=1,
            fillcolor="lightgrey",
            opacity=0.3,
            layer="below",
            line_width=0,
        ))

# ==== Capital Chart ====
st.subheader("📈 Capital in MooMoo")
fig1 = go.Figure()
fig1.add_trace(go.Scatter(
    x=df["Date"], y=df["Capital"],
    mode='lines+markers',
    name='Capital',
    line=dict(color='green'),
    hovertext=df["Day"],
    hoverinfo="text+y"
))
fig1.update_layout(
    yaxis_title="Capital (auto-scaled)",
    xaxis_title="Date",
    height=400,
    margin=dict(l=20, r=20, t=30, b=20),
    shapes=weekend_shapes,
    yaxis_tickformat="d"
)
st.plotly_chart(fig1, use_container_width=True)

# ==== Cumulative Takeout Chart ====
st.subheader("💸 Cumulative Takeout (Daily + Weekly)")
fig2 = go.Figure()
fig2.add_trace(go.Bar(
    x=df["Date"],
    y=df["Cumulative Takeout"],
    marker_color='orange',
    hovertext=df["Day"],
    hoverinfo="text+y",
    name="Cumulative Takeout"
))
fig2.update_layout(
    yaxis_title="Takeout (auto-scaled)",
    xaxis_title="Date",
    height=400,
    margin=dict(l=20, r=20, t=30, b=20),
    yaxis_tickformat="d"
)
st.plotly_chart(fig2, use_container_width=True)

# ==== Daily vs Weekly Breakdown Chart ====
st.subheader("📅 Daily vs Weekly Takeout Breakdown")
fig3 = go.Figure()
fig3.add_trace(go.Bar(
    x=df["Date"],
    y=df["Daily Takeout"],
    name="Daily Takeout",
    marker_color='lightblue'
))
fig3.add_trace(go.Bar(
    x=df["Date"],
    y=df["Weekly Takeout"],
    name="Weekly Takeout",
    marker_color='salmon'
))
fig3.update_layout(
    barmode='stack',
    xaxis_title="Date",
    yaxis_title="Takeout (auto-scaled)",
    height=400,
    margin=dict(l=20, r=20, t=30, b=20),
    yaxis_tickformat="d"
)
st.plotly_chart(fig3, use_container_width=True)