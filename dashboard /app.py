
import streamlit as st
import pandas as pd
import numpy as np
import json
import re
from pathlib import Path

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Scientific Discovery Supervisor",
    page_icon="🔬",
    layout="wide"
)

st.title("🔬 Autonomous Scientific Discovery")
st.caption("Supervisor Console | AI Research Monitoring Dashboard")

# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def normalize_paper(paper):
    return {
        "title": paper.get("title", "Untitled"),
        "authors": paper.get("authors", []),
        "year": str(paper.get("year", "N/A")),
        "journal": paper.get("journal", "N/A"),
        "abstract": paper.get("abstract", "No abstract available"),
        "doi": paper.get("doi", ""),
        "url": paper.get("url", ""),
        "keywords": paper.get("keywords", [])
    }


def create_apa_citation(paper):
    authors = paper["authors"]

    if isinstance(authors, list):
        author_text = ", ".join(authors)
    else:
        author_text = str(authors)

    return (
        f"{author_text} ({paper['year']}). "
        f"{paper['title']}. {paper['journal']}."
    )


def escape_bibtex(value):
    replacements = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_"
    }

    for char, replacement in replacements.items():
        value = str(value).replace(char, replacement)

    return value


def create_bibtex(paper, index):
    authors = paper["authors"]

    if isinstance(authors, list):
        authors = " and ".join(authors)

    return f"""@article{{ref_{index},
    author = {{{escape_bibtex(authors)}}},
    title = {{{escape_bibtex(paper['title'])}}},
    journal = {{{escape_bibtex(paper['journal'])}}},
    year = {{{paper['year']}}},
    url = {{{paper['url']}}}
}}"""


def extract_papers(uploaded_file):
    try:
        data = json.load(uploaded_file)
        papers = data.get("papers", [])

        return [normalize_paper(p) for p in papers]

    except Exception as error:
        st.error(f"Unable to read JSON file: {error}")
        return []


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "discovery_result" not in st.session_state:
    st.session_state.discovery_result = None

if "bench_result" not in st.session_state:
    st.session_state.bench_result = None

if "console_initialized" not in st.session_state:
    st.session_state.console_initialized = False

if "current_step" not in st.session_state:
    st.session_state.current_step = 0

if "state_history" not in st.session_state:
    st.session_state.state_history = []

if "papers" not in st.session_state:
    st.session_state.papers = []

if "sandbox_telemetry" not in st.session_state:
    st.session_state.sandbox_telemetry = {
        "status": "Completed",
        "execution_time": 2.48,
        "memory_usage": 128.6,
        "exit_code": 0,
        "stdout": "Model execution completed successfully.",
        "stderr": "No errors detected.",
        "code": """from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

model.fit(X_train, y_train)
predictions = model.predict(X_test)

print("Execution completed")""",
        "debug_trace": [
            "Code received by sandbox",
            "Environment initialized",
            "Model execution completed",
            "Output returned successfully"
        ]
    }

# Day 21: Statistical Critic sample results

if "critic_metrics" not in st.session_state:
    st.session_state.critic_metrics = {
        "baseline_mean": 70.0,
        "treatment_mean": 82.5,
        "p_value": 0.00003,
        "cohens_d": 0.95,
        "ci_lower": 7.4,
        "ci_upper": 17.6,
        "power": 0.92,
        "verdict": "CONFIRMED STATISTICALLY SIGNIFICANT",
        "sample_size": 100
    }


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

st.sidebar.title("⚙️ Research Configuration")

research_topic = st.sidebar.text_input(
    "Research Topic",
    "Autonomous Scientific Discovery"
)

max_papers = st.sidebar.slider(
    "Maximum Research Papers",
    2, 8, 4
)

docker_enabled = st.sidebar.checkbox(
    "Enable Docker Sandbox",
    value=True
)

debug_enabled = st.sidebar.checkbox(
    "Enable Self-Debugging",
    value=True
)

st.sidebar.divider()

st.sidebar.subheader("Agent Architecture")

agents = [
    "Literature Research Agent",
    "Multimodal Analysis Agent",
    "Code Executor Agent",
    "Statistical Critic Agent",
    "Synthesis Agent"
]

for agent in agents:
    st.sidebar.success(agent)


# --------------------------------------------------
# MAIN CONTROLS
# --------------------------------------------------

st.subheader("Research Supervisor Console")

if st.button("🚀 Initialize Supervisor Console"):

    st.session_state.console_initialized = True

    st.success("Supervisor Console Initialized Successfully!")

if st.session_state.console_initialized:

    st.info(f"Current Research Topic: {research_topic}")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Literature Ingestion", "Ready")

    with col2:
        st.metric("Sandbox Execution", "Ready")

    with col3:
        st.metric("Statistical Critic", "Ready")


# --------------------------------------------------
# WORKFLOW STATE MACHINE
# --------------------------------------------------

workflow_states = [
    "Literature Research",
    "Multimodal Analysis",
    "Code Execution",
    "Statistical Evaluation",
    "Paper Synthesis"
]

st.divider()

st.subheader("Research Workflow State Machine")

current_step = st.session_state.current_step

workflow_col1, workflow_col2 = st.columns([3, 1])

with workflow_col1:

    for index, stage in enumerate(workflow_states):

        if index < current_step:
            status = "🟢 Completed"

        elif index == current_step:
            status = "🔵 Active"

        else:
            status = "⚪ Pending"

        st.write(f"**{index + 1}. {stage}** — {status}")


with workflow_col2:

    if st.button("⬅ Previous Stage"):
        if current_step > 0:
            st.session_state.current_step -= 1
            st.rerun()

    if st.button("Next Stage ➡"):
        if current_step < len(workflow_states) - 1:
            st.session_state.current_step += 1
            st.session_state.state_history.append(
                workflow_states[current_step]
            )
            st.rerun()

    if st.button("🔄 Reset Workflow"):
        st.session_state.current_step = 0
        st.session_state.state_history = []
        st.rerun()


with st.expander("View Execution History"):

    if st.session_state.state_history:
        st.dataframe(
            pd.DataFrame({
                "Completed Stage": st.session_state.state_history
            }),
            use_container_width=True
        )
    else:
        st.write("No completed stages yet.")


# --------------------------------------------------
# DASHBOARD TABS
# --------------------------------------------------

tabs = st.tabs([
    "🌳 Logic Tree & Telemetry",
    "📚 Literature Explorer",
    "🖼️ Multimodal Vision",
    "💻 Sandbox & Debugging",
    "📊 Statistical Critic",
    "📄 Research Paper",
    "🏆 Benchmark Grade"
])


# ==================================================
# TAB 1: LOGIC TREE & TELEMETRY
# ==================================================

with tabs[0]:

    st.header("Logic Tree & Agent Telemetry")

    st.graphviz_chart("""
    digraph ResearchWorkflow {

        rankdir=TB;

        Literature -> Multimodal;
        Multimodal -> Execution;
        Execution -> Critic;
        Critic -> Synthesis;

        Literature [style=filled, fillcolor=lightgreen];
        Multimodal [style=filled, fillcolor=lightblue];
        Execution [style=filled, fillcolor=lightgray];
        Critic [style=filled, fillcolor=lightgray];
        Synthesis [style=filled, fillcolor=lightgray];
    }
    """)

    st.subheader("Agent Execution History")

    trace_data = pd.DataFrame({
        "Agent": agents,
        "Status": [
            "Completed",
            "Completed",
            "Running",
            "Pending",
            "Pending"
        ]
    })

    st.dataframe(trace_data, use_container_width=True)


# ==================================================
# TAB 2: LITERATURE EXPLORER
# ==================================================

with tabs[1]:

    st.header("Literature Knowledge Base")

    uploaded_json = st.file_uploader(
        "Upload Literature JSON",
        type=["json"]
    )

    if uploaded_json is not None:

        if st.button("Import Research Papers"):

            imported_papers = extract_papers(uploaded_json)

            if imported_papers:
                st.session_state.papers = imported_papers
                st.success(
                    f"{len(imported_papers)} papers imported successfully."
                )

    papers = st.session_state.papers

    if papers:

        search_text = st.text_input(
            "Search by title, author, abstract or keyword"
        )

        years = sorted(
            set(paper["year"] for paper in papers),
            reverse=True
        )

        selected_years = st.multiselect(
            "Filter by publication year",
            years,
            default=years
        )

        filtered_papers = []

        for paper in papers:

            searchable = (
                paper["title"]
                + str(paper["authors"])
                + paper["abstract"]
                + str(paper["keywords"])
            ).lower()

            if (
                search_text.lower() in searchable
                and paper["year"] in selected_years
            ):
                filtered_papers.append(paper)

        st.write(
            f"Showing {len(filtered_papers)} research papers"
        )

        paper_df = pd.DataFrame([
            {
                "Title": p["title"],
                "Authors": ", ".join(p["authors"])
                if isinstance(p["authors"], list)
                else p["authors"],
                "Year": p["year"],
                "Journal": p["journal"]
            }
            for p in filtered_papers
        ])

        st.dataframe(paper_df, use_container_width=True)

        if filtered_papers:

            selected_paper = st.selectbox(
                "Select a paper",
                filtered_papers,
                format_func=lambda p: p["title"]
            )

            st.subheader(selected_paper["title"])

            st.write("**Abstract**")
            st.write(selected_paper["abstract"])

            st.write("**Authors:**", selected_paper["authors"])
            st.write("**Journal:**", selected_paper["journal"])
            st.write("**Year:**", selected_paper["year"])

            if selected_paper["url"]:
                st.markdown(
                    f"[Open Research Paper]({selected_paper['url']})"
                )

            st.divider()

            st.subheader("Citation Generator")

            apa = create_apa_citation(selected_paper)

            bibtex = create_bibtex(
                selected_paper,
                1
            )

            st.text_area(
                "APA Citation",
                apa,
                height=100
            )

            st.download_button(
                "Download BibTeX",
                bibtex,
                file_name="references.bib"
            )

    else:
        st.info("Upload a JSON file to explore research papers.")


# ==================================================
# TAB 3: MULTIMODAL VISION
# ==================================================

with tabs[2]:

    st.header("Multimodal Vision Analysis")

    st.info(
        "This section is reserved for visual research analysis "
        "and figure interpretation from the multimodal agent."
    )

    uploaded_image = st.file_uploader(
        "Upload a research figure",
        type=["png", "jpg", "jpeg"],
        key="vision_image"
    )

    if uploaded_image:

        st.image(
            uploaded_image,
            caption="Uploaded Research Figure",
            use_container_width=True
        )

        st.write(
            "Figure uploaded successfully. "
            "Automated vision interpretation is not connected yet."
        )


# ==================================================
# TAB 4: SANDBOX & DEBUGGING
# ==================================================

with tabs[3]:

    st.header("Sandbox Execution & Self-Debugging")

    telemetry = st.session_state.sandbox_telemetry

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Execution Status",
            telemetry["status"]
        )

    with col2:
        st.metric(
            "Execution Time",
            f"{telemetry['execution_time']} sec"
        )

    with col3:
        st.metric(
            "Memory Usage",
            f"{telemetry['memory_usage']} MB"
        )

    st.write("**Exit Code:**", telemetry["exit_code"])

    st.divider()

    st.subheader("Code Inspector")

    st.code(
        telemetry["code"],
        language="python"
    )

    st.subheader("Execution Output")

    st.text_area(
        "Standard Output",
        telemetry["stdout"],
        height=100
    )

    st.text_area(
        "Standard Error",
        telemetry["stderr"],
        height=100
    )

    st.divider()

    st.subheader("Self-Debugging Trace")

    for index, trace in enumerate(telemetry["debug_trace"]):

        st.success(
            f"Step {index + 1}: {trace}"
        )

    st.caption(
        f"Docker Enabled: {docker_enabled} | "
        f"Self-Debugging Enabled: {debug_enabled}"
    )


# ==================================================
# TAB 5: STATISTICAL CRITIC - DAY 21
# ==================================================

with tabs[4]:

    st.header("Statistical Critic Dashboard")

    st.caption(
        "Statistical performance evaluation and empirical "
        "distribution comparison."
    )

    metrics = st.session_state.critic_metrics

    # ----------------------------------------------
    # SECTION 1: VERDICT
    # ----------------------------------------------

    st.subheader("Statistical Verdict")

    st.success(metrics["verdict"])

    # ----------------------------------------------
    # SECTION 2: CRITIC METRIC CARDS
    # ----------------------------------------------

    st.subheader("Critic Performance Metrics")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "P-Value",
            f"{metrics['p_value']:.5f}",
            help="Probability value from the statistical test."
        )

    with col2:
        st.metric(
            "Cohen's d",
            f"{metrics['cohens_d']:.2f}",
            help="Standardized treatment effect size."
        )

    with col3:
        st.metric(
            "Statistical Power",
            f"{metrics['power'] * 100:.1f}%",
            help="Estimated probability of detecting an effect."
        )

    col4, col5, col6 = st.columns(3)

    with col4:
        st.metric(
            "Baseline Mean",
            f"{metrics['baseline_mean']:.2f}"
        )

    with col5:
        st.metric(
            "Treatment Mean",
            f"{metrics['treatment_mean']:.2f}",
            delta=round(
                metrics["treatment_mean"]
                - metrics["baseline_mean"],
                2
            )
        )

    with col6:
        st.metric(
            "Sample Size",
            metrics["sample_size"]
        )

    st.divider()

    # ----------------------------------------------
    # SECTION 3: CONFIDENCE INTERVAL
    # ----------------------------------------------

    st.subheader("95% Confidence Interval")

    ci_col1, ci_col2 = st.columns(2)

    with ci_col1:
        st.metric(
            "Lower Bound",
            f"{metrics['ci_lower']:.2f}"
        )

    with ci_col2:
        st.metric(
            "Upper Bound",
            f"{metrics['ci_upper']:.2f}"
        )

    st.info(
        "The confidence interval represents the estimated range "
        "of the treatment improvement."
    )

    st.divider()

    # ----------------------------------------------
    # SECTION 4: EMPIRICAL DISTRIBUTION CHART
    # ----------------------------------------------

    st.subheader("Empirical Score Distributions")

    st.write(
        "Comparison of baseline and treatment score distributions."
    )

    # Reproducible illustrative sample data
    rng = np.random.default_rng(42)

    baseline_scores = rng.normal(
        loc=metrics["baseline_mean"],
        scale=6.5,
        size=metrics["sample_size"]
    )

    treatment_scores = rng.normal(
        loc=metrics["treatment_mean"],
        scale=5.2,
        size=metrics["sample_size"]
    )

    # Calculate common histogram bins
    all_scores = np.concatenate([
        baseline_scores,
        treatment_scores
    ])

    bins = np.linspace(
        all_scores.min(),
        all_scores.max(),
        25
    )

    baseline_density, bin_edges = np.histogram(
        baseline_scores,
        bins=bins,
        density=True
    )

    treatment_density, _ = np.histogram(
        treatment_scores,
        bins=bins,
        density=True
    )

    bin_centers = (
        bin_edges[:-1] + bin_edges[1:]
    ) / 2

    distribution_df = pd.DataFrame({
        "Score": bin_centers,
        "Baseline": baseline_density,
        "Treatment": treatment_density
    }).set_index("Score")

    st.line_chart(
        distribution_df,
        use_container_width=True
    )

    st.caption(
        "Note: These distributions are simulated for dashboard "
        "demonstration and are not actual experiment observations."
    )

    st.divider()

    # ----------------------------------------------
    # SECTION 5: DISTRIBUTION SUMMARY
    # ----------------------------------------------

    st.subheader("Distribution Summary")

    summary_df = pd.DataFrame({
        "Metric": [
            "Mean",
            "Standard Deviation",
            "Minimum",
            "Maximum"
        ],
        "Baseline": [
            np.mean(baseline_scores),
            np.std(baseline_scores, ddof=1),
            np.min(baseline_scores),
            np.max(baseline_scores)
        ],
        "Treatment": [
            np.mean(treatment_scores),
            np.std(treatment_scores, ddof=1),
            np.min(treatment_scores),
            np.max(treatment_scores)
        ]
    })

    st.dataframe(
        summary_df.round(2),
        use_container_width=True,
        hide_index=True
    )

    # ----------------------------------------------
    # SECTION 6: INTERPRETATION
    # ----------------------------------------------

    st.subheader("Critic Interpretation")

    if metrics["p_value"] < 0.05:

        st.success(
            "The result is statistically significant at the "
            "5% significance level."
        )

    else:

        st.warning(
            "The result is not statistically significant "
            "at the 5% significance level."
        )

    if metrics["cohens_d"] >= 0.8:
        st.write("**Effect Size:** Large")

    elif metrics["cohens_d"] >= 0.5:
        st.write("**Effect Size:** Medium")

    elif metrics["cohens_d"] >= 0.2:
        st.write("**Effect Size:** Small")

    else:
        st.write("**Effect Size:** Negligible")

    if metrics["power"] >= 0.80:
        st.write("**Power Assessment:** Above the 80% target")

    else:
        st.warning(
            "Estimated statistical power is below the 80% target."
        )

    st.caption(
        "The metrics and verdict are illustrative sample values. "
        "Connect this section to CriticAgent outputs for actual results."
    )


# ==================================================
# TAB 6: RESEARCH PAPER
# ==================================================

with tabs[5]:

    st.header("LaTeX Research Paper")

    st.info(
        "This section will display the generated academic "
        "research manuscript."
    )

    paper_title = st.text_input(
        "Research Paper Title",
        "Autonomous Multimodal Scientific Discovery"
    )

    abstract = st.text_area(
        "Abstract",
        "This research explores an autonomous scientific "
        "discovery workflow using multiple intelligent agents."
    )

    latex_content = f"""
\\documentclass{{article}}

\\title{{{paper_title}}}
\\author{{Autonomous Multimodal Scientific Discovery Agent}}

\\begin{{document}}

\\maketitle

\\begin{{abstract}}
{abstract}
\\end{{abstract}}

\\section{{Introduction}}

Introduction to the research problem.

\\section{{Methodology}}

Description of the proposed research methodology.

\\section{{Experimental Results}}

Statistical evaluation of experimental findings.

\\section{{Conclusion}}

Summary of research findings.

\\end{{document}}
"""

    st.download_button(
        "⬇ Download LaTeX Source",
        latex_content,
        file_name="research_paper.tex",
        mime="text/plain"
    )

    with st.expander("Preview LaTeX Source"):
        st.code(
            latex_content,
            language="latex"
        )


# ==================================================
# TAB 7: BENCHMARK GRADE
# ==================================================

with tabs[6]:

    st.header("Holdout Benchmark Evaluation")

    st.info(
        "This section displays the benchmark evaluation "
        "of the autonomous research workflow."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Overall Score", "85/100")

    with col2:
        st.metric("Performance Grade", "A")

    with col3:
        st.metric("Recommendation", "Approved")

    benchmark_data = pd.DataFrame({
        "Evaluation Dimension": [
            "Research Quality",
            "Code Execution",
            "Statistical Validation",
            "Paper Synthesis"
        ],
        "Score": [
            88,
            84,
            90,
            78
        ]
    })

    st.subheader("Benchmark Dimension Breakdown")

    st.bar_chart(
        benchmark_data.set_index("Evaluation Dimension")
    )

    st.dataframe(
        benchmark_data,
        use_container_width=True,
        hide_index=True
    )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "Autonomous Multimodal Scientific Discovery | "
    "Zaalima Development AI Research Division"
)
