import streamlit as st
import pandas as pd
import plotly.express as px

from src.agents.workflow import app as workflow_app
from src.schemas.perspective import Answer
from src.services.perspective_service import start_interview, finish_interview

USER_ID = "demo-user"

SCORE_FIELDS = [
    "hook", "clarity", "engagement", "authenticity",
    "professionalism", "structure", "faithfulness",
]

st.set_page_config(page_title="LinkedInForge", page_icon="🚀", layout="wide")


def reset():
    for key in ("phase", "topic", "questions", "brief", "result"):
        st.session_state.pop(key, None)


def scores_frame(evaluation) -> pd.DataFrame:
    s = evaluation.scores
    return pd.DataFrame(
        [{"metric": f.title(), "score": getattr(s, f)} for f in SCORE_FIELDS]
    )


st.session_state.setdefault("phase", "topic")
st.title("🚀 LinkedInForge")


# ---------------------------------------------------------------- PHASE 1
if st.session_state.phase == "topic":
    st.caption("Step 1 of 3 — what are you writing about?")

    topic = st.text_input(
        "Topic",
        placeholder="Agentic engineering",
        help="Just the subject. You'll be asked for the details next.",
    )

    if st.button("Start interview", type="primary", use_container_width=True):
        if not topic.strip():
            st.warning("Please enter a topic.")
            st.stop()

        with st.spinner("Working out what to ask you..."):
            st.session_state.questions = start_interview(USER_ID, topic.strip())

        st.session_state.topic = topic.strip()
        st.session_state.phase = "answers"
        st.rerun()


# ---------------------------------------------------------------- PHASE 2
elif st.session_state.phase == "answers":
    st.caption("Step 2 of 3 — your actual views")
    st.subheader(st.session_state.topic)
    st.info("Short answers are fine. Specifics matter more than polish.")

    answers = []
    for q in st.session_state.questions.questions:
        st.markdown(f"**{q.text}**")
        st.caption(q.why)
        text = st.text_area(
            q.text,
            key=f"ans_{q.id}",
            placeholder=q.placeholder,
            label_visibility="collapsed",
            height=90,
        )
        answers.append(
            Answer(question_id=q.id, question_text=q.text, answer=text)
        )

    filled = sum(1 for a in answers if a.answer.strip())
    st.progress(filled / len(answers), text=f"{filled} of {len(answers)} answered")

    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("Start over", use_container_width=True):
            reset()
            st.rerun()

    with col2:
        if st.button("Build brief & write post", type="primary",
                     disabled=filled == 0, use_container_width=True):

            with st.spinner("Understanding your angle..."):
                brief = finish_interview(USER_ID, st.session_state.topic, answers)
            st.session_state.brief = brief

            with st.spinner("Generating and refining (this takes a minute)..."):
                st.session_state.result = workflow_app.invoke({
                    "topic": st.session_state.topic,
                    "brief": brief.model_dump(),
                    "post": "",
                    "evaluation": None,
                    "reflection": None,
                    "iteration": 0,
                    "done": False,
                    "previous_hook": 0,
                    "previous_engagement": 0,
                })

            st.session_state.phase = "result"
            st.rerun()


# ---------------------------------------------------------------- PHASE 3
else:
    result = st.session_state.result
    brief = st.session_state.brief
    evaluation = result["evaluation"]

    col1, col2 = st.columns([3, 1])
    with col1:
        st.success("Done")
    with col2:
        if st.button("Write another", use_container_width=True):
            reset()
            st.rerun()

    m1, m2 = st.columns(2)
    m1.metric("Iterations used", result["iteration"])
    m2.metric("Faithfulness", f"{evaluation.scores.faithfulness}/10")

    if brief.is_thin():
        st.warning("The brief was thin — the post likely leans on generic material.")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["📝 Final Post", "🎯 Your Brief", "📊 Evaluation", "📈 Scores"]
    )

    with tab1:
        st.text_area("Final post", value=result["post"], height=400,
                     label_visibility="collapsed")

    with tab2:
        st.caption("This is what the generator was given. Check it matches what you meant.")
        st.text(brief.to_prompt_block())

    with tab3:
        st.json(evaluation.model_dump())

    with tab4:
        df = scores_frame(evaluation)
        fig = px.bar(df, x="score", y="metric", orientation="h", text="score",
                     range_x=[0, 10])
        fig.update_layout(yaxis_title="", xaxis_title="Score", height=400)
        st.plotly_chart(fig, use_container_width=True)
        

# import streamlit as st
# import pandas as pd
# import plotly.express as px
# from src.api.service import run_pipeline

# st.set_page_config(
#     page_title="LinkedIn AI Optimizer",
#     page_icon="🚀",
#     layout="wide"
# )

# st.title("🚀 LinkedInForge")

# st.markdown(
#     """
# ### Multi-Agent LinkedIn Content Refinement System

# Transform ideas into polished LinkedIn posts using an AI workflow designed for professional storytelling.

# #### ⚙️ How it works

# 1. ✍️ **Generate** an initial draft from your prompt
# 2. 📊 **Evaluate** quality across multiple dimensions
# 3. 🧠 **Reflect** on strengths and weaknesses
# 4. 🔄 **Refine** the content through iterative improvements
# 5. ✅ Deliver a high-quality LinkedIn-ready post

# #### 📌 Evaluation Dimensions

# - Hook
# - Clarity
# - Engagement
# - Authenticity
# - Professionalism
# - Structure
# - Faithfulness

# """
# )

# topic = st.text_area(
#     "Topic / Prompt",
#     height=200,
#     placeholder="""
# Example:

# I got promoted to Engineering Manager after 5 years as a software engineer.
# Write a LinkedIn post about this achievement.
# """
# )


# generate = st.button(
#     "🚀 Generate & Optimize",
#     use_container_width=True
# )

# if generate:

#     if not topic.strip():
#         st.warning("Please enter a topic.")
#         st.stop()

#     with st.spinner("Optimizing your LinkedIn post..."):

#         result = run_pipeline(topic)

#     st.success("Optimization completed!")

#     post = result["post"]
#     evaluation = result["evaluation"]
#     reflection = result["reflection"]
#     iteration = result["iteration"]

#     scores_df = pd.DataFrame(result["scores"])

#     st.metric(
#         label="Iterations Used",
#         value=iteration
#     )

#     tab1, tab2, tab3, tab4 = st.tabs(
#         [
#             "📝 Final Post",
#             "📊 Evaluation",
#             "🧠 Reflection",
#             "📈 Scores"
#         ]
#     )

#     with tab1:

#         st.subheader("Final LinkedIn Post")

#         st.text_area("",value=post,height=350)

#     with tab2:

#         st.subheader("Evaluation Report")

#         st.json(evaluation)

#     with tab3:

#         st.subheader("Reflection Plan")

#         st.json(reflection)

#     with tab4:

#         st.subheader("Quality Scores")

#         fig = px.bar(
#             scores_df,
#             x="score",
#             y="metric",
#             orientation="h",
#             text="score",
#             title="Evaluation Scores"
#         )

#         fig.update_layout(yaxis_title="",xaxis_title="Score",height=400)

#         st.plotly_chart(fig,use_container_width=True)

#         st.dataframe(scores_df,use_container_width=True)


