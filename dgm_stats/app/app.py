import collections
import dataclasses
import os

import dotenv
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import dgm_stats as ds

dotenv.load_dotenv()

colors = px.colors.qualitative.Plotly


class CourseRating:
    def __init__(self, rating_value1, rating_result1, rating_value2, rating_result2):
        self._rating_value1 = float(rating_value1)
        self._rating_result1 = float(rating_result1)
        self._rating_value2 = float(rating_value2)
        self._rating_result2 = float(rating_result2)

    def get_rating(self, result):
        return (self._rating_value2 - self._rating_value1) * (result - self._rating_result1) / \
               (self._rating_result2 - self._rating_result1) + self._rating_value1


@dataclasses.dataclass
class Course:
    name: str
    full_name: str
    course_rating: CourseRating
    par: int

    @staticmethod
    def from_data(data) -> 'Course':
        course = data["course"]
        baskets = data["baskets"]
        par = sum(int(basket["Par"]) for basket in baskets)
        return Course(course["Name"],
                      course["Fullname"],
                      CourseRating(course["RatingValue1"],
                                   course["RatingResult1"],
                                   course["RatingValue2"],
                                   course["RatingResult2"]),
                      par)


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


api = ds.Api("https://discgolfmetrix.com/api.php", os.environ["DGM_CODE"])


@st.cache()
def fetch_competition(id: int):
    result = api.get_competition(id)
    return result


@st.cache()
def fetch_course(id: int):
    result = api.get_course(id)
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


# data = fetch(2064109)
data_all = fetch_competition(2064106)
course_data = fetch_course(data_all["Competition"]["CourseID"])
course = Course.from_data(course_data)

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

best_5 = something(df_all_summary)

with st.sidebar:
    st.title("Competition")
    st.text_input("Choose competition", placeholder="Buråsheia Ukesgolf 2022", disabled=True)
    st.title("Player breakdown")
    players = st.multiselect("Choose players", df_all.columns, default=list(best_5.iloc[:3].index))

st.write("# Welcome to Disc Golf Metrix Stats!")
st.write(f"## Here are the results for {data_all['Competition']['Name']}")

st.write("### Results, only counting the top 5 rounds")
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
st.plotly_chart(fig, use_container_width=True)

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
st.plotly_chart(fig, use_container_width=True)


def player_breakdown(df_all, df_all_summary, players):
    best_5 = {}
    for name, weeks in df_all_summary[players].T.iterrows():
        best = weeks.nsmallest(5)
        # best.insert(0, "Total", best.sum())
        best_5[name] = best
    best_5_df = pd.DataFrame(best_5).T
    best_5_df.insert(0, "Total", best_5_df.sum(axis=1))
    best_5_df.columns = ["Total"] + list(range(1, len(best_5_df.columns)))
    best_5 = best_5_df.sort_values("Total")
    best_5 = best_5.style.highlight_null(props="color: transparent;").format("{:.0f}")
    st.write("Top 5 rounds")
    best_5

    all_results = df_all_summary[players].T
    all_results.insert(0, "Total", all_results.sum(axis=1))
    all_results.columns = ["Total"] + list(range(1, len(all_results.columns)))
    all_results = all_results.sort_values("Total")
    styled_results = all_results.style.highlight_null(props="color: transparent;").format("{:.0f}")
    st.write("All rounds")
    st.write(styled_results)

    df = df_all.T.loc[players]
    st.write("Cumulative sum")
    st.line_chart(df.T.cumsum())

    st.write("### Course Rating")
    st.write("Quick rating is the mean of the last 8 rounds.")

    player_ratings = course.course_rating.get_rating(df_all_summary[players] + course.par)

    fig = go.Figure()
    for i, (player, ratings) in enumerate(player_ratings.T.iterrows()):
        rolling_mean = ratings.dropna().rolling(8).mean().reindex(ratings.index)
        fig.add_trace(go.Scatter(
            y=rolling_mean.values,
            x=rolling_mean.index,
            name=f"{player} quick rating",
            line_color=colors[i],
        ))
        fig.add_trace(go.Scatter(
            y=ratings.values,
            x=ratings.index,
            line_color=colors[i],
            name=f"{player} score",
            opacity=0.25
        ))
        #st.write(player, rolling_mean)

    #fig = px.line(player_ratings)
    # fig.add_trace(go.Scatter(y=))
    fig.update_layout(
        yaxis=dict(
            title="Rating"
        ),
        xaxis=dict(
            title="Week"
        ),
        legend=dict(
            title="Player"
        )
    )
    fig.update_xaxes(showgrid=False)
    st.plotly_chart(fig, use_container_width=True)

    st.write("### Count of each score across the competition")
    common_data = pd.DataFrame([series.value_counts() for _, series in df.iterrows()])
    fig = px.bar(common_data)
    fig.update_layout(
        xaxis=dict(
            title="Players",
        ),
        yaxis=dict(
            title="Count of each score"
        ),
        legend=dict(
            title="Score (relative)"
        )
    )
    st.plotly_chart(fig, use_container_width=True)

    st.write("### Score distributions per hole")
    st.write("The line is the average and the colored area is the scoring range, from minimum score to maximum score.")

    # Todo: make dynamic for number of holes
    number_of_holes = 18
    player_dfs = {}
    for player, series in df.iterrows():
        round_scores = collections.defaultdict(list)
        for i, score in enumerate(series):
            round_scores[i // 18].append(score)
        player_dfs[player] = pd.DataFrame(round_scores)

    fig = go.Figure()

    for i, (player, player_df) in enumerate(player_dfs.items()):
        pdf = player_df.T.dropna()
        x_axis = pdf.T.index + 1
        # confidence = 0.75
        high = pdf.max(axis=0)  # pdf.mean(axis=0)+pdf.std()*confidence
        low = pdf.min(axis=0)  # pdf.mean(axis=0)-pdf.std()*confidence
        fig.add_trace(go.Scatter(
            x=np.hstack((x_axis, x_axis[::-1])),
            y=np.hstack((high, low[::-1])),
            fillcolor=colors[i],
            line_color=colors[i],
            opacity=0.25,
            fill="toself",
            mode="lines",
            name=f"{player} - range"
        ))

        fig.add_trace(go.Scatter(
            x=x_axis,
            y=pdf.mean(axis=0),
            fillcolor=colors[i],
            line_color=colors[i],
            name=f"{player} - mean",
            mode="lines"
        ))

    st.plotly_chart(fig, use_container_width=True)

    # Todo: make dynamic for number of holes
    number_of_holes = 18
    data = {player: {i: collections.defaultdict(lambda: 0) for i in range(1, number_of_holes + 1)} for player in players}
    for player, series in df.iterrows():
        for i, value in enumerate(series.values):
            if pd.isna(value):
                continue
            data[player][i % number_of_holes + 1][value] += 1
    reform = {(outerKey, innerKey): values for outerKey, innerDict in data.items() for innerKey, values in innerDict.items()}
    common_data = pd.DataFrame(reform)

    for player in players:
        player_dt = common_data[player]
        player_dt.index = player_dt.index.astype(int)
        fig = px.bar(player_dt.sort_index().T)
        fig.update_layout(
            xaxis=dict(
                title="Players",
                tick0=1,
                dtick=1,
            ),
            yaxis=dict(
                title="Count"
            ),
            legend=dict(
                title="Score (relative)"
            ),
            title=f"{player}"
        )
        st.plotly_chart(fig, use_container_width=True)


st.write("## Player breakdown")

if players:
    player_breakdown(df_all, df_all_summary, players)

# cumsum
#
# df = to_df(data)
#
# st.write("Player results", df)
# st.area_chart(df.T)
#
# common_data = pd.DataFrame([series.value_counts() for _, series in df.T.iterrows()])
#
# common_data
#
# st.line_chart(common_data)
#
# fig = px.bar(common_data)
# fig.update_layout(
#     xaxis=dict(
#         title="Holes",
#         tick0=1,
#         dtick=1,
#     ),
#     yaxis=dict(
#         title="Count"
#     ),
#     legend=dict(
#         title="Score (relative)"
#     )
# )
# st.plotly_chart(fig, use_container_width=True)
