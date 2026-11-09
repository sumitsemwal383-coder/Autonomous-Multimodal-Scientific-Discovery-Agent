
# ==================================================
# TAB 8: TOKEN TRACKING & COST ANALYTICS - DAY 23
# ==================================================

with tabs[7]:

    st.header("💰 Token Tracking & Cost Analytics")

    st.write(
        "Monitor token consumption, estimate API expenses, "
        "and analyze usage across research tasks."
    )

    st.divider()

    # ----------------------------------------------
    # SECTION 1: API PRICING CONFIGURATION
    # ----------------------------------------------

    st.subheader("API Pricing Configuration")

    price_col1, price_col2 = st.columns(2)

    with price_col1:
        input_rate = st.number_input(
            "Input Cost per 1 Million Tokens ($)",
            min_value=0.0,
            value=2.00,
            step=0.10
        )

    with price_col2:
        output_rate = st.number_input(
            "Output Cost per 1 Million Tokens ($)",
            min_value=0.0,
            value=8.00,
            step=0.10
        )

    st.caption(
        "These are configurable example rates. "
        "Replace them with the pricing of your actual model provider."
    )

    st.divider()

    # ----------------------------------------------
    # SECTION 2: RECORD TOKEN USAGE
    # ----------------------------------------------

    st.subheader("Record Research Task Usage")

    with st.form("token_usage_form"):

        task_name = st.text_input(
            "Research Task",
            placeholder="e.g. Literature Analysis"
        )

        input_tokens = st.number_input(
            "Input Tokens",
            min_value=0,
            value=1000,
            step=100
        )

        output_tokens = st.number_input(
            "Output Tokens",
            min_value=0,
            value=500,
            step=100
        )

        record_usage = st.form_submit_button(
            "➕ Record Token Usage",
            use_container_width=True
        )

    if record_usage:

        if not task_name.strip():

            st.error("Please enter a research task name.")

        else:

            total_tokens = input_tokens + output_tokens

            estimated_cost = (
                (input_tokens / 1_000_000) * input_rate
                +
                (output_tokens / 1_000_000) * output_rate
            )

            usage_record = {
                "Task": task_name.strip(),
                "Input Tokens": int(input_tokens),
                "Output Tokens": int(output_tokens),
                "Total Tokens": int(total_tokens),
                "Estimated Cost ($)": estimated_cost,
                "Timestamp": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            }

            st.session_state.token_history.append(
                usage_record
            )

            st.success("Token usage recorded successfully!")

            st.rerun()

    st.divider()

    # ----------------------------------------------
    # SECTION 3: USAGE SUMMARY
    # ----------------------------------------------

    st.subheader("Token Usage Overview")

    history = st.session_state.token_history

    total_input = sum(
        item["Input Tokens"] for item in history
    )

    total_output = sum(
        item["Output Tokens"] for item in history
    )

    total_tokens = total_input + total_output

    total_cost = sum(
        item["Estimated Cost ($)"] for item in history
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Input Tokens",
        f"{total_input:,}"
    )

    col2.metric(
        "Output Tokens",
        f"{total_output:,}"
    )

    col3.metric(
        "Total Tokens",
        f"{total_tokens:,}"
    )

    col4.metric(
        "Estimated Total Cost",
        f"${total_cost:.6f}"
    )

    st.divider()

    # ----------------------------------------------
    # SECTION 4: TOKEN USAGE CHART
    # ----------------------------------------------

    st.subheader("Token Consumption Analysis")

    if history:

        usage_df = pd.DataFrame(history)

        chart_df = usage_df[
            ["Task", "Input Tokens", "Output Tokens"]
        ].set_index("Task")

        st.bar_chart(
            chart_df,
            use_container_width=True
        )

        st.caption(
            "Comparison of input and output token consumption "
            "across recorded research tasks."
        )

    else:

        st.info(
            "No token usage recorded yet. "
            "Add a research task above to generate analytics."
        )

    st.divider()

    # ----------------------------------------------
    # SECTION 5: COST ANALYTICS
    # ----------------------------------------------

    st.subheader("API Cost Analysis")

    if history:

        cost_df = pd.DataFrame(history)

        cost_chart = cost_df[
            ["Task", "Estimated Cost ($)"]
        ].set_index("Task")

        st.bar_chart(
            cost_chart,
            use_container_width=True
        )

        st.metric(
            "Average Cost per Task",
            f"${total_cost / len(history):.6f}"
        )

    else:

        st.info("Cost analytics will appear after recording usage.")

    st.divider()

    # ----------------------------------------------
    # SECTION 6: USAGE HISTORY
    # ----------------------------------------------

    st.subheader("Token Usage History")

    if history:

        history_df = pd.DataFrame(history)

        st.dataframe(
            history_df,
            use_container_width=True,
            hide_index=True
        )

        csv_data = history_df.to_csv(index=False)

        st.download_button(
            "⬇ Download Usage Report (CSV)",
            data=csv_data,
            file_name="token_usage_report.csv",
            mime="text/csv"
        )

        if st.button("🗑️ Clear Usage History"):

            st.session_state.token_history = []

            st.success("Usage history cleared.")

            st.rerun()

    else:

        st.info("No usage history available.")

    st.divider()

    st.subheader("Usage Insights")

    if total_tokens > 0:

        input_percentage = (
            total_input / total_tokens
        ) * 100

        output_percentage = (
            total_output / total_tokens
        ) * 100

        st.write(
            f"**Input Token Share:** {input_percentage:.2f}%"
        )

        st.write(
            f"**Output Token Share:** {output_percentage:.2f}%"
        )

        st.progress(input_percentage / 100)

        st.write(
            f"**Recorded Research Tasks:** {len(history)}"
        )

    else:

        st.write(
            "Record token usage to generate insights."
        )

    st.caption(
        "Usage data is maintained in Streamlit session state. "
        "It is not persistent across separate sessions."
    )
