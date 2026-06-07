import streamlit as st
import pandas as pd
import plotly.express as px
from src.api.service import run_pipeline

st.set_page_config(
    page_title="LinkedIn AI Optimizer",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 LinkedInForge")

st.markdown(
    """
### Multi-Agent LinkedIn Content Refinement System

Transform ideas into polished LinkedIn posts using an AI workflow designed for professional storytelling.

#### ⚙️ How it works

1. ✍️ **Generate** an initial draft from your prompt
2. 📊 **Evaluate** quality across multiple dimensions
3. 🧠 **Reflect** on strengths and weaknesses
4. 🔄 **Refine** the content through iterative improvements
5. ✅ Deliver a high-quality LinkedIn-ready post

#### 📌 Evaluation Dimensions

- Hook
- Clarity
- Engagement
- Authenticity
- Professionalism
- Structure
- Faithfulness

"""
)

topic = st.text_area(
    "Topic / Prompt",
    height=200,
    placeholder="""
Example:

I got promoted to Engineering Manager after 5 years as a software engineer.
Write a LinkedIn post about this achievement.
"""
)


generate = st.button(
    "🚀 Generate & Optimize",
    use_container_width=True
)

if generate:

    if not topic.strip():
        st.warning("Please enter a topic.")
        st.stop()

    with st.spinner("Optimizing your LinkedIn post..."):

        result = run_pipeline(topic)

    st.success("Optimization completed!")

    post = result["post"]
    evaluation = result["evaluation"]
    reflection = result["reflection"]
    iteration = result["iteration"]

    scores_df = pd.DataFrame(result["scores"])

    st.metric(
        label="Iterations Used",
        value=iteration
    )

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "📝 Final Post",
            "📊 Evaluation",
            "🧠 Reflection",
            "📈 Scores"
        ]
    )

    with tab1:

        st.subheader("Final LinkedIn Post")

        st.text_area("",value=post,height=350)

    with tab2:

        st.subheader("Evaluation Report")

        st.json(evaluation)

    with tab3:

        st.subheader("Reflection Plan")

        st.json(reflection)

    with tab4:

        st.subheader("Quality Scores")

        fig = px.bar(
            scores_df,
            x="score",
            y="metric",
            orientation="h",
            text="score",
            title="Evaluation Scores"
        )

        fig.update_layout(yaxis_title="",xaxis_title="Score",height=400)

        st.plotly_chart(fig,use_container_width=True)

        st.dataframe(scores_df,use_container_width=True)