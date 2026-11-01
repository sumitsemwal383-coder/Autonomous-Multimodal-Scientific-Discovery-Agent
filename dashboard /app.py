
import streamlit as st
import pandas as pd

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Scientific Discovery Supervisor",
    page_icon="🔬",
    layout="wide"
)

# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.title("🔬 Autonomous Scientific Discovery")
st.subheader("Supervisor Monitoring Console")

st.markdown(
    "Monitor the autonomous research workflow, agent progression, "
    "and execution states from a centralized dashboard."
)

# --------------------------------------------------
# SIDEBAR CONFIGURATION
# --------------------------------------------------

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

# --------------------------------------------------
# SESSION STATE INITIALIZATION
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

# --------------------------------------------------
# WORKFLOW STATE DEFINITIONS
# --------------------------------------------------

workflow_states = [
    {
        "name": "Literature Research",
        "agent": "Literature Researcher",
        "description": "Collects research papers and identifies relevant findings."
    },
    {
        "name": "Multimodal Analysis",
        "agent": "Multimodal Analyst",
        "description": "Analyzes research figures, diagrams, and visual information."
    },
    {
        "name": "Code Execution",
        "agent": "Code Executor",
        "description": "Executes experimental code in the research sandbox."
    },
    {
        "name": "Statistical Evaluation",
        "agent": "Statistical Critic",
        "description": "Evaluates experimental results using statistical tests."
    },
    {
        "name": "Paper Synthesis",
        "agent": "Paper Synthesizer",
        "description": "Organizes findings into a structured research manuscript."
    }
]

total_steps = len(workflow_states)

# --------------------------------------------------
# MAIN HEADER
# --------------------------------------------------

st.markdown("---")

st.info(
    f"**Research Topic:** {research_topic}  \n"
    f"**Maximum Papers:** {max_papers}  \n"
    f"**Docker Sandbox:** {'Enabled' if docker_enabled else 'Disabled'}  \n"
    f"**Self-Debugging:** {'Enabled' if debug_enabled else 'Disabled'}"
)

# --------------------------------------------------
# SUPERVISOR INITIALIZATION
# --------------------------------------------------

if st.button("🚀 Initialize Supervisor Console", use_container_width=True):
    st.session_state.console_initialized = True
    st.session_state.current_step = 0
    st.session_state.state_history = []
    st.success("Supervisor console initialized successfully.")

if st.session_state.console_initialized:

    st.success("Supervisor Console is Ready")

    # --------------------------------------------------
    # OVERVIEW
    # --------------------------------------------------

    st.subheader("System Overview")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Research Agents", "5")

    with col2:
        st.metric("Workflow Stages", total_steps)

    with col3:
        st.metric("Current Status", "Initialized")

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

    # --------------------------------------------------
    # TAB 1: INTERACTIVE LOGIC TREE
    # --------------------------------------------------

    with tabs[0]:

        st.subheader("🔀 Research Workflow State Machine")

        st.write(
            "The logic tree represents the sequence of autonomous "
            "research agents involved in the scientific discovery process."
        )

        current_step = st.session_state.current_step

        # Build Graphviz visualization
        graph = ["digraph ResearchWorkflow {"]
        graph.append('rankdir=TB;')
        graph.append('node [shape=box, style="rounded,filled", '
                     'fontname="Arial", fontsize=10, '
                     'margin="0.25,0.15"];')
        graph.append('edge [color="gray", penwidth=1.5];')

        for index, state in enumerate(workflow_states):

            node_id = f"stage{index}"

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
                f'{node_id} [label="{label}", fillcolor="{fill_color}"];'
            )

            if index > 0:
                graph.append(
                    f'stage{index - 1} -> {node_id};'
                )

        graph.append("}")

        st.graphviz_chart("\n".join(graph), use_container_width=True)

        # --------------------------------------------------
        # CURRENT WORKFLOW STATE
        # --------------------------------------------------

        st.divider()

        st.subheader("Current Agent Status")

        if current_step < total_steps:

            active_state = workflow_states[current_step]

            st.info(f"**Active Stage:** {active_state['name']}")

            col1, col2 = st.columns(2)

            with col1:
                st.write("**Assigned Agent**")
                st.write(active_state["agent"])

            with col2:
                st.write("**Stage Progress**")
                st.progress(
                    (current_step + 1) / total_steps
                )

            st.write("**Stage Description**")
            st.write(active_state["description"])

        else:
            st.success(
                "All workflow stages have been completed successfully."
            )

        # --------------------------------------------------
        # INTERACTIVE STATE CONTROLS
        # --------------------------------------------------

        st.divider()

        st.subheader("Interactive State Controls")

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

        # --------------------------------------------------
        # WORKFLOW EXECUTION HISTORY
        # --------------------------------------------------

        st.divider()

        st.subheader("Workflow Execution History")

        if st.session_state.state_history:

            history_df = pd.DataFrame(
                st.session_state.state_history
            )

            st.dataframe(
                history_df,
                use_container_width=True,
                hide_index=True
            )

        else:
            st.caption(
                "No workflow stages have been completed yet. "
                "Use Next Stage to simulate agent progression."
            )

    # --------------------------------------------------
    # REMAINING PLACEHOLDER TABS
    # --------------------------------------------------

    with tabs[1]:
        st.subheader("Literature & Vector Store")
        st.info("Literature exploration interface will be integrated in a future stage.")

    with tabs[2]:
        st.subheader("Multimodal Vision")
        st.info("Visual research analysis will be integrated in a future stage.")

    with tabs[3]:
        st.subheader("Sandbox & Self-Debugging")
        st.info("Sandbox execution monitoring will be integrated in a future stage.")

    with tabs[4]:
        st.subheader("Statistical Critic")
        st.info("Statistical evaluation metrics will be integrated in a future stage.")

    with tabs[5]:
        st.subheader("LaTeX Research Paper")
        st.info("Research manuscript preview will be integrated in a future stage.")

    with tabs[6]:
        st.subheader("Holdout Benchmark")
        st.info("Benchmark evaluation will be integrated in a future stage.")

else:

    # --------------------------------------------------
    # INITIAL DASHBOARD OVERVIEW
    # --------------------------------------------------

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

# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.markdown("---")

st.caption(
    "Autonomous Multimodal Scientific Discovery Agent | "
    "Supervisor Monitoring Dashboard"
)
