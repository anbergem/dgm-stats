import collections
import dataclasses

import pandas as pd
import plotly.express as px
import streamlit as st

import dgm_stats as ds


@dataclasses.dataclass
class UserResult:
    name: str
    class_name: str
    group: int
    results: pd.Series


def to_df(result):
    all_series = []
    for user in result["Competition"]["Results"]:
        series = pd.DataFrame(user["PlayerResults"])["Diff"]
        series.name = user["Name"]
        series.index = range(1, 19)
        # series["Total"] = series.sum()
        all_series.append(series)
        # UserResult(user["Name"], user["ClassName"], int(user["Group"]), series)
    return pd.DataFrame(all_series)


@st.cache()
def fetch(id: int):
    api = ds.Api("https://discgolfmetrix.com/api.php")
    result = api.get_competition(id)
    return result


@st.cache()
def fetch_all(data) -> pd.DataFrame:
    user_results = collections.defaultdict(dict)

    for w_i, weekly_competition in enumerate(data["Competition"]["SubCompetitions"]):
        for s_i, sub_competition in enumerate(weekly_competition["SubCompetitions"]):
            for u_i, user_result in enumerate(sub_competition["Results"]):
                for h_i, hole in enumerate(user_result["PlayerResults"]):
                    if not hole:
                        continue
                    # results[weekly_competition["Name"]][sub_competition["Name"]][user_result["Name"]][i] = hole["Diff"]
                    # results[weekly_competition["Name"]][user_result["Name"]][i] = hole["Diff"]
                    user_results[user_result["Name"]][f"{w_i:02}{h_i:02}"] = int(hole["Diff"])

    df = pd.DataFrame(user_results).dropna(axis=1, thresh=5 * 18)
    return df.sort_index()


@st.cache()
def fetch_all_summary(data) -> pd.DataFrame:
    user_results = collections.defaultdict(dict)

    number_of_holes = len(data["Competition"]["Tracks"])
    for w_i, weekly_competition in enumerate(data["Competition"]["SubCompetitions"]):
        for s_i, sub_competition in enumerate(weekly_competition["SubCompetitions"]):
            for u_i, user_result in enumerate(sub_competition["Results"]):
                if len(user_result["PlayerResults"]) != number_of_holes:
                    continue
                user_results[user_result["Name"]][f"{w_i:02}"] = user_result["Diff"]

    df = pd.DataFrame(user_results).dropna(axis=1, thresh=5)
    return df.sort_index()


data = fetch(2064109)
data_all = fetch(2064106)

st.write("# Welcome to Disc Golf Metrix Stats!")
st.write(f"## Here are the results for {data_all['Competition']['Name']}")

df_all = fetch_all(data_all)
df_all_summary = fetch_all_summary(data_all)


def something(df):
    best_5 = {}
    for name, weeks in df.T.iterrows():
        best = weeks.nsmallest(5)
        # best.insert(0, "Total", best.sum())
        best_5[name] = best
    best_5_df = pd.DataFrame(best_5).T
    best_5_df.insert(0, "Total", best_5_df.sum(axis=1))
    best_5_df.columns = ["Total"] + list(range(1, len(best_5_df.columns)))
    return best_5_df.sort_values("Total")


st.write("### Results, only counting the top 5 rounds")
best_5 = something(df_all_summary)
best_5 = best_5.style.highlight_null(props="color: transparent;").format("{:.0f}")
best_5

st.write("### Coming: Per class breakdown")

st.write("### All results")
all_results = df_all_summary.T
all_results.insert(0, "Total", all_results.sum(axis=1))
all_results.columns = ["Total"] + list(range(1, len(all_results.columns)))
all_results = all_results.sort_values("Total")
all_results = all_results.style.highlight_null(props="color: transparent;").format("{:.0f}")
all_results

fig = px.line(df_all_summary.cumsum())
fig.update_layout(
    title="Cumulative score per week",
    xaxis=dict(
        title="Weeks",
    ),
    yaxis=dict(
        title="Cumulative Score (relative)"
    ),
    legend=dict(
        title="Players (>= 5 weeks)"
    )
)
chart = st.plotly_chart(fig)

cumsum = df_all.cumsum()
fig = px.line(cumsum)
fig.update_layout(
    title="Cumulative score per hole",
    xaxis=dict(
        title="Weeks",
    ),
    yaxis=dict(
        title="Cumulative Score (relative)"
    ),
    legend=dict(
        title="Players (>= 5 weeks)"
    )
)
chart = st.plotly_chart(fig)
cumsum

df = to_df(data)

st.write("Player results", df)
st.area_chart(df.T)

common_data = pd.DataFrame([series.value_counts() for _, series in df.T.iterrows()])

common_data

st.line_chart(common_data)

fig = px.bar(common_data)
fig.update_layout(
    xaxis=dict(
        title="Holes",
        tick0=1,
        dtick=1,
    ),
    yaxis=dict(
        title="Count"
    ),
    legend=dict(
        title="Score (relative)"
    )
)
st.plotly_chart(fig)
