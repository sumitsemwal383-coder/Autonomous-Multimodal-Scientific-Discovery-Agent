
import streamlit as st
import pandas as pd
import json
import re

# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Scientific Discovery Supervisor",
    page_icon="🔬",
    layout="wide"
)

# ==================================================
# HELPER FUNCTIONS
# ==================================================

def normalize_paper(paper):
    """Standardize literature record fields."""

    if not isinstance(paper, dict):
        return None

    authors = paper.get("authors", [])

    if isinstance(authors, str):
        authors = [authors]

    keywords = paper.get("keywords", [])

    if isinstance(keywords, str):
        keywords = [keywords]

    return {
        "title": str(paper.get("title", "Untitled Paper")),
        "authors": authors,
        "year": str(paper.get("year", "N/A")),
        "journal": str(
            paper.get("journal", paper.get("publication", "N/A"))
        ),
        "abstract": str(
            paper.get("abstract", "No abstract available.")
        ),
        "doi": str(paper.get("doi", "N/A")),
        "url": str(paper.get("url", "")),
        "keywords": keywords
    }


def create_apa_citation(paper):
    """Generate a basic APA-style reference."""

    authors = paper["authors"]

    if not authors:
        author_text = "Unknown Author"

    elif len(authors) == 1:
        author_text = str(authors[0])

    elif len(authors) == 2:
        author_text = f"{authors[0]} & {authors[1]}"

    else:
        author_text = ", ".join(
            str(author) for author in authors[:-1]
        )
        author_text += f", & {authors[-1]}"

    citation = (
        f"{author_text} ({paper['year']}). "
        f"{paper['title']}. {paper['journal']}."
    )

    if paper["doi"] != "N/A":
        citation += f" https://doi.org/{paper['doi']}"

    return citation


def escape_bibtex(value):
    """Escape common BibTeX special characters."""

    replacements = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_"
    }

    for character, replacement in replacements.items():
        value = str(value).replace(character, replacement)

    return value


def create_bibtex(paper, index):
    """Generate a basic BibTeX article entry."""

    first_author = (
        str(paper["authors"][0])
        if paper["authors"]
        else "unknown"
    )

    author_key = re.sub(
        r"[^a-zA-Z0-9]",
        "",
        first_author.split()[-1]
    ).lower()

    year_key = re.sub(
        r"[^0-9]",
        "",
        paper["year"]
    )

    citation_key = f"{author_key}{year_key}_{index}"

    authors = " and ".join(
        str(author) for author in paper["authors"]
    ) or "Unknown Author"

    return (
        f"@article{{{citation_key},\n"
        f"  author = {{{escape_bibtex(authors)}}},\n"
        f"  title = {{{escape_bibtex(paper['title'])}}},\n"
        f"  journal = {{{escape_bibtex(paper['journal'])}}},\n"
        f"  year = {{{escape_bibtex(paper['year'])}}},\n"
        f"  doi = {{{escape_bibtex(paper['doi'])}}}\n"
        f"}}"
    )


def extract_papers(data):
    """Extract and normalize paper records from JSON."""

    if isinstance(data, dict):
        data = data.get("papers", [])

    if not isinstance(data, list):
        raise ValueError(
            "JSON must contain a list of papers or a 'papers' list."
        )

    return [
        normalized
        for paper in data
        if (normalized := normalize_paper(paper)) is not None
    ]


# ==================================================
# SESSION STATE INITIALIZATION
# ==================================================

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

if "literature_records" not in st.session_state:
    st.session_state.literature_records = []

if "literature_upload_name" not in st.session_state:
    st.session_state.literature_upload_name = None

# Day 20: Sandbox telemetry state

if "sandbox_telemetry" not in st.session_state:
    st.session_state.sandbox_telemetry = {
        "status": "Completed",
        "execution_time": 2.48,
        "memory_usage": 128.6,
        "exit_code": 0,

        "stdout": (
            "Initializing research experiment...\n"
            "Loading dataset...\n"
            "Running model evaluation...\n"
            "Experiment completed successfully."
        ),

        "stderr": "No errors reported.",

        "code": """import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# Load experimental dataset
data = pd.read_csv("research_dataset.csv")

X = data.drop("target", axis=1)
y = data["target"]

# Split dataset
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train model
model = RandomForestClassifier(random_state=42)
model.fit(X_train, y_train)

# Evaluate experiment
predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)

print("Model Accuracy:", accuracy)
""",

        "debug_trace": [
            {
                "step": 1,
                "event": "Environment initialized",
                "status": "Success"
            },
            {
                "step": 2,
                "event": "Dataset loading completed",
                "status": "Success"
            },
            {
                "step": 3,
                "event": "Model training completed",
                "status": "Success"
            },
            {
                "step": 4,
                "event": "Evaluation completed",
                "status": "Success"
            }
        ]
    }


# ==================================================
# HEADER
# ==================================================

st.title("🔬 Autonomous Scientific Discovery")

st.subheader("Supervisor Monitoring Console")

st.markdown(
    "Monitor the autonomous research workflow, agent progression, "
    "literature knowledge base, and experimental execution."
)

# ==================================================
# SIDEBAR CONFIGURATION
# ==================================================

with st.sidebar:

    st.title("🧠 Supervisor Controls")

    research_topic = st.text_input(
        "Research Topic",
        value="Machine Learning Research"
    )

    max_papers = st.slider(
        "Maximum Research Papers",
        min_value=2,
        max_value=8,
        value=4
    )

    docker_enabled = st.checkbox(
        "Enable Docker Sandbox",
        value=True
    )

    debug_enabled = st.checkbox(
        "Enable Self-Debugging",
        value=True
    )

    st.divider()

    st.subheader("Agent Architecture")

    agents = [
        "Literature Researcher",
        "Multimodal Analyst",
        "Code Executor",
        "Statistical Critic",
        "Paper Synthesizer"
    ]

    for agent in agents:
        st.markdown(f"• {agent}")


# ==================================================
# RESEARCH CONFIGURATION
# ==================================================

st.markdown("---")

st.info(
    f"**Research Topic:** {research_topic}  \n"
    f"**Maximum Papers:** {max_papers}  \n"
    f"**Docker Sandbox:** {'Enabled' if docker_enabled else 'Disabled'}  \n"
    f"**Self-Debugging:** {'Enabled' if debug_enabled else 'Disabled'}"
)


# ==================================================
# SUPERVISOR INITIALIZATION
# ==================================================

if st.button(
    "🚀 Initialize Supervisor Console",
    use_container_width=True
):

    st.session_state.console_initialized = True
    st.session_state.current_step = 0
    st.session_state.state_history = []

    st.success(
        "Supervisor console initialized successfully."
    )


# ==================================================
# WORKFLOW STATE DEFINITIONS
# ==================================================

workflow_states = [
    {
        "name": "Literature Research",
        "agent": "Literature Researcher",
        "description": (
            "Collects research papers and identifies relevant findings."
        )
    },
    {
        "name": "Multimodal Analysis",
        "agent": "Multimodal Analyst",
        "description": (
            "Analyzes research figures, diagrams, and visual information."
        )
    },
    {
        "name": "Code Execution",
        "agent": "Code Executor",
        "description": (
            "Executes experimental code in the research sandbox."
        )
    },
    {
        "name": "Statistical Evaluation",
        "agent": "Statistical Critic",
        "description": (
            "Evaluates experimental results using statistical tests."
        )
    },
    {
        "name": "Paper Synthesis",
        "agent": "Paper Synthesizer",
        "description": (
            "Organizes findings into a structured research manuscript."
        )
    }
]

total_steps = len(workflow_states)


# ==================================================
# MAIN DASHBOARD
# ==================================================

if st.session_state.console_initialized:

    st.success("Supervisor Console is Ready")

    # --------------------------------------------------
    # SYSTEM OVERVIEW
    # --------------------------------------------------

    st.subheader("System Overview")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Research Agents", "5")

    with col2:
        st.metric("Workflow Stages", total_steps)

    with col3:
        st.metric(
            "Literature Records",
            len(st.session_state.literature_records)
        )

    # --------------------------------------------------
    # DASHBOARD TABS
    # --------------------------------------------------

    tabs = st.tabs([
        "Logic Tree & State Machine",
        "Literature & Vector Store",
        "Multimodal Vision",
        "Sandbox & Self-Debugging",
        "Statistical Critic",
        "LaTeX Research Paper",
        "Holdout Benchmark"
    ])

    # ==================================================
    # TAB 1: LOGIC TREE AND STATE MACHINE
    # ==================================================

    with tabs[0]:

        st.subheader("🔀 Research Workflow State Machine")

        st.write(
            "Visual representation of the autonomous "
            "research agent execution sequence."
        )

        current_step = st.session_state.current_step

        graph = [
            "digraph ResearchWorkflow {",
            "rankdir=TB;",
            'node [shape=box, style="rounded,filled", '
            'fontname="Arial", fontsize=10];',
            'edge [color="gray", penwidth=1.5];'
        ]

        for index, state in enumerate(workflow_states):

            if index < current_step:
                fill_color = "palegreen"
                status = "Completed"

            elif index == current_step:
                fill_color = "lightskyblue"
                status = "Active"

            else:
                fill_color = "lightgray"
                status = "Pending"

            label = (
                f'{state["name"]}\\n'
                f'{state["agent"]}\\n'
                f'Status: {status}'
            )

            graph.append(
                f'stage{index} [label="{label}", '
                f'fillcolor="{fill_color}"];'
            )

            if index > 0:
                graph.append(
                    f'stage{index - 1} -> stage{index};'
                )

        graph.append("}")

        st.graphviz_chart(
            "\n".join(graph),
            use_container_width=True
        )

        st.divider()

        if current_step < total_steps:

            active_state = workflow_states[current_step]

            st.info(
                f"Active Stage: {active_state['name']}"
            )

            st.write(
                "**Assigned Agent:**",
                active_state["agent"]
            )

            st.write(
                "**Description:**",
                active_state["description"]
            )

            st.progress(
                (current_step + 1) / total_steps
            )

        else:

            st.success(
                "All workflow stages have been completed."
            )

        # State navigation

        col1, col2, col3 = st.columns(3)

        with col1:

            if st.button(
                "⬅ Previous Stage",
                disabled=(current_step == 0),
                use_container_width=True
            ):

                st.session_state.current_step -= 1
                st.rerun()

        with col2:

            if st.button(
                "Next Stage ➡",
                disabled=(current_step >= total_steps),
                use_container_width=True
            ):

                if current_step < total_steps:

                    completed_state = workflow_states[current_step]

                    st.session_state.state_history.append({
                        "Stage": completed_state["name"],
                        "Agent": completed_state["agent"],
                        "Status": "Completed"
                    })

                    st.session_state.current_step += 1

                st.rerun()

        with col3:

            if st.button(
                "🔄 Reset Workflow",
                use_container_width=True
            ):

                st.session_state.current_step = 0
                st.session_state.state_history = []
                st.rerun()

        if st.session_state.state_history:

            st.subheader("Workflow Execution History")

            st.dataframe(
                pd.DataFrame(st.session_state.state_history),
                use_container_width=True,
                hide_index=True
            )


    # ==================================================
    # TAB 2: LITERATURE KNOWLEDGE BASE EXPLORER
    # ==================================================

    with tabs[1]:

        st.subheader("📚 Literature Knowledge Base Explorer")

        st.write(
            "Explore research papers, inspect publication details, "
            "and generate formatted citations."
        )

        # Import literature records

        st.markdown("### Import Research Papers")

        uploaded_file = st.file_uploader(
            "Upload literature records in JSON format",
            type=["json"],
            help=(
                "Upload a JSON list of research papers or an object "
                "containing a 'papers' list."
            ),
            key="literature_json_upload"
        )

        if uploaded_file is not None:

            if (
                st.session_state.literature_upload_name
                != uploaded_file.name
            ):

                try:

                    imported_data = json.load(uploaded_file)

                    imported_papers = extract_papers(
                        imported_data
                    )

                    st.session_state.literature_records = imported_papers

                    st.session_state.literature_upload_name = (
                        uploaded_file.name
                    )

                    st.success(
                        f"Successfully imported {len(imported_papers)} "
                        "literature records."
                    )

                except (
                    json.JSONDecodeError,
                    ValueError
                ) as error:

                    st.error(
                        f"Unable to import JSON: {error}"
                    )

        papers = st.session_state.literature_records

        st.divider()

        # Knowledge base metrics

        metric1, metric2, metric3 = st.columns(3)

        with metric1:
            st.metric("Total Papers", len(papers))

        with metric2:

            authors = {
                author
                for paper in papers
                for author in paper["authors"]
            }

            st.metric("Unique Authors", len(authors))

        with metric3:

            years = {
                paper["year"]
                for paper in papers
                if paper["year"] != "N/A"
            }

            st.metric("Publication Years", len(years))

        # Search and filter

        st.markdown("### Search and Filter Literature")

        if papers:

            search_query = st.text_input(
                "Search by title, author, abstract, or keyword",
                placeholder="Enter a search term..."
            )

            available_years = sorted(
                {
                    paper["year"]
                    for paper in papers
                    if paper["year"] != "N/A"
                },
                reverse=True
            )

            year_options = ["All Years"] + available_years

            selected_year = st.selectbox(
                "Filter by Publication Year",
                year_options
            )

            filtered_papers = []

            for paper in papers:

                searchable_text = " ".join([
                    paper["title"],
                    paper["abstract"],
                    paper["journal"],
                    " ".join(
                        str(a) for a in paper["authors"]
                    ),
                    " ".join(
                        str(k) for k in paper["keywords"]
                    )
                ]).lower()

                matches_search = (
                    search_query.lower() in searchable_text
                )

                matches_year = (
                    selected_year == "All Years"
                    or paper["year"] == selected_year
                )

                if matches_search and matches_year:
                    filtered_papers.append(paper)

            st.write(
                f"**Showing {len(filtered_papers)} "
                f"of {len(papers)} papers**"
            )

            if filtered_papers:

                # Literature table

                literature_table = pd.DataFrame([
                    {
                        "Title": paper["title"],
                        "Authors": ", ".join(
                            str(a) for a in paper["authors"]
                        ),
                        "Year": paper["year"],
                        "Publication": paper["journal"]
                    }
                    for paper in filtered_papers
                ])

                st.dataframe(
                    literature_table,
                    use_container_width=True,
                    hide_index=True
                )

                st.divider()

                # Paper details viewer

                st.markdown("### Research Paper Details")

                selected_index = st.selectbox(
                    "Select a paper to inspect",
                    options=range(len(filtered_papers)),
                    format_func=lambda i: filtered_papers[i]["title"]
                )

                selected_paper = filtered_papers[selected_index]

                st.markdown(
                    f"#### {selected_paper['title']}"
                )

                st.write(
                    "**Authors:**",
                    ", ".join(
                        str(a) for a in selected_paper["authors"]
                    ) or "Unknown"
                )

                st.write(
                    "**Publication Year:**",
                    selected_paper["year"]
                )

                st.write(
                    "**Journal:**",
                    selected_paper["journal"]
                )

                st.write(
                    "**DOI:**",
                    selected_paper["doi"]
                )

                if selected_paper["url"]:

                    st.markdown(
                        f"[Open Research Paper]({selected_paper['url']})"
                    )

                st.markdown("**Abstract**")

                st.write(selected_paper["abstract"])

                st.write(
                    "**Keywords:**",
                    ", ".join(
                        str(k) for k in selected_paper["keywords"]
                    ) or "Not provided"
                )

                # Citation viewer

                st.divider()

                st.markdown("### Citation Viewer")

                apa_citation = create_apa_citation(
                    selected_paper
                )

                bibtex_citation = create_bibtex(
                    selected_paper,
                    selected_index + 1
                )

                citation_format = st.radio(
                    "Select Citation Format",
                    ["APA", "BibTeX"],
                    horizontal=True
                )

                if citation_format == "APA":

                    st.code(
                        apa_citation,
                        language="text"
                    )

                    st.download_button(
                        "Download APA Citation",
                        data=apa_citation,
                        file_name="citation.txt",
                        mime="text/plain"
                    )

                else:

                    st.code(
                        bibtex_citation,
                        language="bibtex"
                    )

                    st.download_button(
                        "Download BibTeX Citation",
                        data=bibtex_citation,
                        file_name="citation.bib",
                        mime="application/x-bibtex"
                    )

            else:

                st.warning(
                    "No papers match your search or selected filters."
                )

        else:

            st.info(
                "The literature knowledge base is currently empty. "
                "Upload a JSON file containing research-paper records "
                "to explore papers and generate citations."
            )


    # ==================================================
    # TAB 3: MULTIMODAL VISION
    # ==================================================

    with tabs[2]:

        st.subheader("Multimodal Vision")

        st.info(
            "Visual research analysis will be integrated "
            "in a future development stage."
        )


    # ==================================================
    # TAB 4: SANDBOX EXECUTION TELEMETRY & CODE INSPECTOR
    # ==================================================

    with tabs[3]:

        st.subheader("💻 Sandbox Execution Telemetry")

        st.write(
            "Monitor experimental code execution, resource usage, "
            "execution logs, and self-debugging activity."
        )

        telemetry = st.session_state.sandbox_telemetry

        # Execution status

        st.markdown("### Execution Status")

        if telemetry["status"] == "Completed":

            st.success(
                "Execution Completed Successfully"
            )

        elif telemetry["status"] == "Failed":

            st.error("Execution Failed")

        else:

            st.warning(
                "Execution Status: " + telemetry["status"]
            )

        # Resource utilization

        st.markdown("### Resource Utilization")

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Execution Time",
                f"{telemetry['execution_time']:.2f} sec"
            )

        with col2:

            st.metric(
                "Memory Usage",
                f"{telemetry['memory_usage']:.1f} MB"
            )

        with col3:

            st.metric(
                "Exit Code",
                telemetry["exit_code"]
            )

        st.divider()

        # Code inspector

        st.markdown("### 🔍 Experimental Code Inspector")

        code_type = st.selectbox(
            "Select Code Module",
            [
                "Model Training Script",
                "Dataset Processing",
                "Model Evaluation"
            ]
        )

        st.caption(
            f"Selected Module: {code_type}"
        )

        st.code(
            telemetry["code"],
            language="python",
            line_numbers=True
        )

        st.divider()

        # Execution logs

        st.markdown("### 📋 Execution Logs")

        log_col1, log_col2 = st.columns(2)

        with log_col1:

            st.markdown("**Standard Output (STDOUT)**")

            st.code(
                telemetry["stdout"],
                language="text"
            )

        with log_col2:

            st.markdown("**Standard Error (STDERR)**")

            if telemetry["stderr"] == "No errors reported.":

                st.success(telemetry["stderr"])

            else:

                st.error(telemetry["stderr"])

        st.divider()

        # Self-debugging trace

        st.markdown("### 🛠️ Self-Debugging Execution Trace")

        debug_df = pd.DataFrame(
            telemetry["debug_trace"]
        )

        st.dataframe(
            debug_df,
            use_container_width=True,
            hide_index=True
        )

        completed_steps = sum(
            1
            for step in telemetry["debug_trace"]
            if step["status"] == "Success"
        )

        total_debug_steps = len(
            telemetry["debug_trace"]
        )

        if total_debug_steps > 0:

            st.markdown("**Debugging Progress**")

            st.progress(
                completed_steps / total_debug_steps
            )

            st.caption(
                f"{completed_steps} of {total_debug_steps} "
                "execution steps completed successfully."
            )

        st.divider()

        # Sandbox configuration

        st.markdown("### Sandbox Configuration")

        config_col1, config_col2 = st.columns(2)

        with config_col1:

            st.write(
                "**Docker Sandbox:**",
                "Enabled" if docker_enabled else "Disabled"
            )

        with config_col2:

            st.write(
                "**Self-Debugging:**",
                "Enabled" if debug_enabled else "Disabled"
            )

        st.caption(
            "Execution metrics and logs shown here are illustrative "
            "sample telemetry. Live sandbox integration will be "
            "connected in a later development stage."
        )


    # ==================================================
    # TAB 5: STATISTICAL CRITIC
    # ==================================================

    with tabs[4]:

        st.subheader("Statistical Critic")

        st.info(
            "Statistical evaluation metrics will be integrated "
            "in a future development stage."
        )


    # ==================================================
    # TAB 6: LATEX RESEARCH PAPER
    # ==================================================

    with tabs[5]:

        st.subheader("LaTeX Research Paper")

        st.info(
            "Research manuscript preview will be integrated "
            "in a future development stage."
        )


    # ==================================================
    # TAB 7: HOLDOUT BENCHMARK
    # ==================================================

    with tabs[6]:

        st.subheader("Holdout Benchmark")

        st.info(
            "Benchmark evaluation will be integrated "
            "in a future development stage."
        )


# ==================================================
# INITIAL DASHBOARD OVERVIEW
# ==================================================

else:

    st.subheader("Supervisor Console Overview")

    col1, col2, col3 = st.columns(3)

    with col1:

        st.markdown("### 📚 Literature Research")

        st.write(
            "Collects relevant academic papers and "
            "identifies research gaps."
        )

    with col2:

        st.markdown("### 💻 Experimental Execution")

        st.write(
            "Executes experimental code inside "
            "a controlled sandbox environment."
        )

    with col3:

        st.markdown("### 📊 Statistical Critique")

        st.write(
            "Evaluates experimental findings using "
            "statistical significance and effect size."
        )

    st.warning(
        "Initialize the Supervisor Console to access "
        "the workflow state machine and monitoring tabs."
    )


# ==================================================
# FOOTER
# ==================================================

st.markdown("---")

st.caption(
    "Autonomous Multimodal Scientific Discovery Agent | "
    "Supervisor Monitoring Dashboard"
)
