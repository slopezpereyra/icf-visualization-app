import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide")

data = pd.read_csv("formatted_data.csv")
data = data.drop(data[data["ISI"] == 0].index)
s_level = pd.read_csv("analysis_subject_level.csv")
g_level = pd.read_csv("analysis_group_level.csv")
participants_info = pd.read_csv("ParticipantsInfo.csv").rename(
    columns={"Unnamed: 4": "Comments"})


help_str = """How do you want to measure the relative amplitude of paired pulses with respect
to single test pulses? Standard way is MeanRA. The lower your dropdown choice, the more robust
the measure."""

##### LOGIC ########


def plot_subject_data(s):
    fig = go.Figure()

    grouped_s_isi = s_level.groupby(["Subject", "SessionType"])

    bl = grouped_s_isi.get_group((s, "BL"))
    swd = grouped_s_isi.get_group((s, "SWD"))
    fig.add_trace(go.Scatter(x=bl["ISI"], y=bl["RA"],
                             name=str(s) + " " + "Baseline"))
    fig.add_trace(go.Scatter(x=bl["ISI"], y=bl["ARA"], visible='legendonly',
                             name=str(s) + " " + "Baseline adjusted"))
    fig.add_trace(go.Scatter(x=swd["ISI"], y=swd["RA"],
                             name=str(s) + " " + "SWD"))
    fig.add_trace(go.Scatter(x=bl["ISI"], y=swd["ARA"],
                             name=str(s) + " " + "SWD adjusted", visible='legendonly'))

    fig.add_hline(y=1, line_dash="dot")
    fig.update_layout(title="Subject's " + str(s) + "Relative Amplitudes",
                      xaxis_title="ISI", yaxis_title="Relative amplitude")
    fig.update_layout(margin=dict(l=2, r=2, t=80, b=80))

    return fig


def plot_subject_variance(s):
    fig = go.Figure()
    box_df_bl = data.groupby(["Subject", "SessionType"]).get_group((s, "BL"))
    box_df_swd = data.groupby(["Subject", "SessionType"]).get_group((s, "SWD"))
    fig.add_trace(
        go.Box(x=box_df_bl["ISI"], y=box_df_bl["EMGPeakToPeak"], name="Baseline"))
    fig.add_trace(go.Box(
        x=box_df_swd["ISI"], y=box_df_swd["EMGPeakToPeak"], name="Slow-wave disruption"))

    fig.update_layout(margin=dict(l=2, r=2, t=80, b=80),
                      title="Subject's " + str(s) + " EMG box-plots",
                      xaxis_title="ISI", yaxis_title="EMG Peak to Peak")

    return fig


def plot_all_subject_data():
    fig = go.Figure()
    df = s_level.copy()
    df = df[df["Group"] == 1] if only_hc else df
    df = df[df["Group"] == 2] if only_mdd else df
    grouped = df.groupby(["Subject", "SessionType"])
    coef = "RA" if not checkbox_adj else "ARA"
    if checkbox_bl:
        for x in df["Subject"].unique():
            plot_data = grouped.get_group((x, "BL"))
            fig.add_trace(go.Scatter(x=plot_data["ISI"], y=plot_data[coef],
                                     name=str(x) + " " + "BL"))
    if checkbox_swd:
        for x in df["Subject"].unique():
            plot_data = grouped.get_group((x, "SWD"))
            fig.add_trace(go.Scatter(x=plot_data["ISI"], y=plot_data[coef],
                                     name=str(x) + " " + "SWD"))

    fig.add_hline(y=1, line_dash="dot")
    fig.update_layout(margin=dict(l=2, r=2, t=30, b=20),
                      xaxis_title="ISI", yaxis_title="Relative amplitude")

    return fig


def group(group, session_type):
    return g_level[(g_level["Group"] == group) & (g_level["SessionType"] == session_type)]


def set_data(coef):
    groups = [group(1, "BL")[["ISI", "MeanRA"]], group(
        1, "SWD")[["ISI", "MeanRA"]], group(2, "BL")[["ISI", "MeanRA"]], group(2, "SWD")[["ISI", "MeanRA"]]]
    ISI = g_level["ISI"]
    BL_A = group(1, "BL")[coef].tolist()
    BL_B = group(2, "BL")[coef].tolist()
    SWD_A = group(1, "SWD")[coef].tolist()
    SWD_B = group(2, "SWD")[coef].tolist()

    zipped = list(zip(ISI, BL_A, BL_B, SWD_A, SWD_B))

    return (pd.DataFrame(zipped, columns=["ISI", "BL 1",  "BL 2", "SWD 1", "SWD 2"]))


def plot_data(adj):

    coef = "WMedianRA" if adj else "MeanRA"
    df = set_data(coef)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["ISI"], y=df["BL 1"],
                             mode='markers+lines', name="HC: Baseline"))
    fig.add_trace(go.Scatter(x=df["ISI"], y=df["BL 2"],
                             mode='markers+lines', name="MDD: Baseline"))
    fig.add_trace(go.Scatter(x=df["ISI"], y=df["SWD 1"],
                             mode='markers+lines', name="HC: Slow-wave disruption"))
    fig.add_trace(go.Scatter(x=df["ISI"], y=df["SWD 2"],
                             mode='markers+lines', name="MDD: Slow-wave disruption"))
    fig.add_hline(y=1, line_dash="dot")
    fig.update_layout(margin=dict(l=2, r=2, t=30, b=0),
                      xaxis_title="ISI", yaxis_title="Relative Amplitude")

    return (fig)

####### APP ##########


with st.sidebar:
    st.write("Source code at ...")

st.title("Data visualization dashboard")
st.write("Welcome to our data's front-end little world.")


# ------ Participants info -----------

first_expander = st.expander(label="Participants information", expanded=False)
with first_expander:
    st.dataframe(participants_info, width=640)


# ------ General -----------

st.header("General statistics")

col1, col2 = st.columns(2)

cdf_ptop = px.ecdf(data, x="EMGPeakToPeak",
                   color="ISI", width=600, title="CDF: EMG peak to peak")
cdf_ra = px.ecdf(data, x="RA",
                 color="ISI", width=600, title="CDF: Relative Amplitude")
cdf_ptop.update_layout(margin=dict(l=2, r=2, t=30, b=0))
cdf_ra.update_layout(margin=dict(l=2, r=2, t=30, b=0))

col1.plotly_chart(cdf_ptop)
col2.plotly_chart(cdf_ra)


cdf_ptop_facetted = px.ecdf(data, x="EMGPeakToPeak",
                            color="ISI", width=700, facet_row="Label",
                            title="CDF: EMG peak to peak by group")
cdf_ra_facetted = px.ecdf(data, x="RA",
                          color="ISI", width=700, facet_row="Label",
                          title="CDF: Relative Amplitude by group")

cdf_ptop_facetted.update_layout(margin=dict(l=2, r=2, t=30, b=0))
cdf_ra_facetted.update_layout(margin=dict(l=2, r=2, t=30, b=0))
col1.plotly_chart(cdf_ptop_facetted)
col2.plotly_chart(cdf_ra_facetted)

t2 = px.parallel_coordinates(data, color="Subject",
                             dimensions=['ISI',
                                         'EMGPeakToPeak', 'RA'],
                             color_continuous_scale=px.colors.diverging.Tealrose,
                             width=1200,
                             title="Parallel Coordinates: ISI to EMG to Relative Amplitude")

st.plotly_chart(t2)

dens_heat_a = px.density_heatmap(
    data, x="EMGPeakToPeak", title="Density heatmap: EMG peak to peak")
dens_heat_b = px.density_heatmap(data, x="EMGPeakToPeak", facet_row="Label",
                                 title="Density heatmap: EMG peak to peak by group")
col1.plotly_chart(dens_heat_a)
col2.plotly_chart(dens_heat_b)

# ------ Subject data -----------

st.header("Curious about a particular subject...?")

s_query = st.text_input("Subject query",
                        help="Write a subject number to get that subject's data")

scol1, scol2 = st.columns(2)

if s_query != "":
    try:
        s_data = s_level[s_level["Subject"] == int(s_query)]
        if len(s_data != 0):
            scol1.plotly_chart(plot_subject_data(int(s_query)))
            scol2.plotly_chart(plot_subject_variance(int(s_query)))
        else:
            st.error("No data found for subject " + s_query)
    except:
        st.error("No data found for Subject ", s_query)


# ------ Subjects data -----------

st.header("Curious about all of them...?")

second_expander = st.expander(label="Plot controls", expanded=True)

with second_expander:
    checkbox_bl = st.checkbox("Baseline", True)
    checkbox_swd = st.checkbox("Slow-wave disruption", True)
    checkbox_adj = st.checkbox("Adjusted measures?", False)
    only_hc = st.checkbox("Hide MDD subjects", False)
    only_mdd = st.checkbox("Hide healthy control subjects", False)

fig3 = plot_all_subject_data()
st.plotly_chart(fig3)

# ------ Group data -----------


st.header("Measures of ICF relative amplitude")

coefficient = st.checkbox("Adjusted measures of relative amplitude?")


st.plotly_chart(plot_data(coefficient))
