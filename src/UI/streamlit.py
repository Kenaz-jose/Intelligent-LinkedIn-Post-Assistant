import streamlit as st
import pandas as pd
import plotly.express as px
import uuid

from src.agents.curator import get_curated_topics
from src.agents.workflow import app as workflow_app
from src.schemas.perspective import Answer
from src.services.perspective_service import (
    start_interview,
    probe_interview,
    finish_interview,
)
from src.store.run_store import save_brief, save_run
from src.services.search_service import fetch_live_context

USER_ID = "demo-user"

CRAFT_FIELDS = [
    "hook", "clarity", "engagement", "authenticity",
    "professionalism", "structure",
]

st.set_page_config(page_title="Spotlight", page_icon="💫", layout="wide")

# ---------------------------------------------------------
# SESSION STATE & LANGGRAPH CONFIG
# ---------------------------------------------------------
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

config = {"configurable": {"thread_id": st.session_state.thread_id}}

st.session_state.setdefault("phase", "topic")


def reset():
    for key in ("phase", "topic", "tone", "questions", "answers", "probe_questions",
                "brief", "brief_id", "result", "raw_search_results", "selected_references"):
        st.session_state.pop(key, None)
    for key in [k for k in st.session_state if k.startswith("ans_")]:
        st.session_state.pop(key, None)
    # Generate a new thread ID for a fresh LangGraph memory state
    st.session_state.thread_id = str(uuid.uuid4())


def collect_answers(questions, is_probe: bool = False) -> list[Answer]:
    answers = []
    for q in questions:
        st.markdown(f"**{q.text}**")
        
        if is_probe:
            st.info(f"💡 **Tip:** {q.why}")
        else:
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
    return answers


def render_brief(brief) -> None:
    st.markdown(f"#### {brief.thesis or '_No clear position captured_'}")
    st.caption("This is the position the post will argue.")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Written for**")
        st.write(brief.audience or "Professionals on LinkedIn")

    with col2:
        st.markdown("**They should leave thinking**")
        st.write(brief.takeaway or "_Nothing specific captured_")

    st.divider()

    st.markdown("**Drawing on your experience**")
    if brief.evidence:
        for item in brief.evidence:
            st.markdown(f"- {item}")
    else:
        st.markdown(
            "_Nothing captured. The post will have no first-hand material "
            "to draw on._"
        )

    if brief.details:
        st.markdown("**And these specifics**")
        for item in brief.details:
            st.markdown(f"- {item}")


def scores_frame(evaluation) -> pd.DataFrame:
    s = evaluation.scores
    return pd.DataFrame([
        {
            "metric": f.title(),
            "score": getattr(s, f).score,
            "observation": getattr(s, f).observation,
        }
        for f in CRAFT_FIELDS
    ])


def initial_state(topic: str, brief, external_references: list = None) -> dict:
    return {
        "topic": topic,
        "brief": brief.model_dump(),
        "external_references": external_references or [],
        "post": "",
        "tone": st.session_state.get("tone", "Direct, punchy, and technical (like a senior engineer)"),
        "evaluation": None,
        "reflection": None,
        "verdict": None,
        "decision": None,
        "iteration": 0,
        "repairs_used": 0,
        "current_craft": 0.0,
        "previous_craft": -1.0,
        "alternative_hooks": [],
        "best_alternative_hooks": [],
        "best_post": "",
        "best_verdict": None,
        "best_evaluation": None,
        "best_iteration": 0,
    }


def build_brief(answers: list[Answer], was_probed: bool = False) -> None:
    with st.spinner("Understanding your angle..."):
        st.session_state.brief = finish_interview(
            USER_ID, st.session_state.topic, answers, st.session_state.tone
        )

    st.session_state.brief_id = save_brief(
        USER_ID, st.session_state.brief, answers, was_probed
    )

    st.session_state.phase = "brief"
    st.rerun()


# ==============================================================================
# UI MAIN LOOP
# ==============================================================================

st.title("🚀 LinkedInForge")

# ---------------------------------------------------------------- TOPIC
if st.session_state.phase == "topic":
    st.caption("Step 1 — what are you writing about?")

    st.markdown("### 💡 Need inspiration?")
    categories = [
        "AI & Deep Learning", 
        "Quantum Mechanics", 
        "Evolutionary Biology", 
        "Productivity & Deep Work", 
        "World Affairs"
    ]
    
    selected_category = st.pills("Select a domain to see trending news:", categories)
    
    selected_tone = st.selectbox(
        "Select Post Tone & Vibe:",
        [
            "Direct, punchy, and technical (like a senior engineer)",
            "Conversational, casual, and highly relatable (story-driven)",
            "Sharp, contrarian, and bold (challenging conventional wisdom)",
            "Witty, sarcastic, and funny (uses dry humor and developer self-deprecation without losing technical accuracy)",
            "Academic, measured, and deeply analytical"
        ]
    )

    if selected_category:
        with st.spinner(f"Curating trending topics in {selected_category}..."):
            try:
                curated_data = get_curated_topics(selected_category)
                if curated_data and curated_data.articles:
                    st.markdown(f"**Trending in {selected_category}:**")
                    
                    for idx, article in enumerate(curated_data.articles):
                        with st.container(border=True):
                            st.subheader(article.headline)
                            st.write(article.summary)
                            
                            unique_key = f"{article.url}_{idx}"
                            if st.button("Write about this", key=unique_key, type="secondary"):
                                st.session_state.topic = f"{article.headline}: {article.summary}"
                                st.session_state.tone = selected_tone
                                
                                with st.spinner("Working out what to ask you..."):
                                    st.session_state.questions = start_interview(
                                        USER_ID, st.session_state.topic, selected_tone
                                    )
                                st.session_state.phase = "answers"
                                st.rerun()
                else:
                    st.warning("No articles were found for this category right now. Please try another category or enter your topic manually below.")
                    
            except Exception as e:
                st.error("Could not fetch trending news right now. Try another category or enter manually.")
                st.exception(e)

    st.divider()

    st.markdown("### ✍️ Or enter your own topic")
    topic = st.text_input(
        "Topic",
        placeholder="Agentic engineering",
        help="Just the subject. You'll be asked for the details next.",
    )

    if st.button("Start interview", type="primary", use_container_width=True):
        if not topic.strip():
            st.warning("Please enter a topic or select a news article above.")
            st.stop()
        
        st.session_state.topic = topic.strip()
        st.session_state.tone = selected_tone

        with st.spinner("Working out what to ask you..."):
            st.session_state.questions = start_interview(USER_ID, topic.strip(), selected_tone)

        st.session_state.phase = "answers"
        st.rerun()

# ---------------------------------------------------------------- ANSWERS
elif st.session_state.phase == "answers":
    st.caption("Step 2 — your actual views")
    st.subheader(st.session_state.topic)
    st.info(
        "Short answers are fine. Specifics matter more than polish — numbers, "
        "names, and what actually happened are what stop the post sounding "
        "generic."
    )

    answers = collect_answers(st.session_state.questions.questions)
    filled = sum(1 for a in answers if a.answer.strip())
    total_questions = len(answers) if len(answers) > 0 else 1
    st.progress(filled / total_questions, text=f"{filled} of {len(answers)} answered")

    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("Skip to brief", use_container_width=True):
            build_brief(answers)          

    with col2:
        if st.button("Continue", type="primary", use_container_width=True):
            st.session_state.answers = answers  
            
            with st.spinner("Analyzing answers for follow-ups..."):
                st.session_state.probe_questions = probe_interview(
                    USER_ID, st.session_state.topic, answers, st.session_state.tone
                )

            if st.session_state.probe_questions.questions:
                st.session_state.phase = "probe"
                st.rerun()
            else:
                build_brief(answers)

# ---------------------------------------------------------------- PROBE
elif st.session_state.phase == "probe":
    st.caption("One more thing")
    st.subheader("A couple of follow-ups")
    st.info(
        "Some answers were a little general. These are the specifics that "
        "will keep the post from sounding like everyone else's. Skip any "
        "you'd rather not answer."
    )

    probe_answers = collect_answers(st.session_state.probe_questions.questions, is_probe=True)

    st.divider()
    col1, col2 = st.columns([1, 2])

    with col1:
        if st.button("Skip these", use_container_width=True):
            build_brief(st.session_state.answers)

    with col2:
        if st.button("Continue", type="primary", use_container_width=True):
            build_brief(st.session_state.answers + probe_answers, was_probed=True)

# ---------------------------------------------------------------- BRIEF
elif st.session_state.phase == "brief":
    brief = st.session_state.brief
    st.caption("Step 3 — check this before we write")
    st.subheader("The angle")
    st.markdown(
        "Everything below comes from your answers. Nothing else can appear "
        "in the post — if the angle is wrong, fix it here rather than "
        "rewriting the post later."
    )

    render_brief(brief)
    gaps = brief.thin_fields()

    if not brief.evidence:
        st.error(
            "**This brief has no first-hand experience in it.**\n\n"
            "The writer would have nothing to draw on and would invent "
            "specifics, which the faithfulness check then rejects. That "
            "cycle costs several minutes and produces a post you cannot "
            "publish.\n\n"
            "Go back and answer at least one question with something that "
            "actually happened — a project, a decision, a thing that broke."
        )

        if st.button("Back to answers", type="primary", use_container_width=True):
            st.session_state.phase = "answers"
            st.rerun()
        st.stop()

    if gaps:
        lines = "\n".join(f"- {g}" for g in gaps)
        st.info(f"The brief is usable, but these would strengthen it:\n\n{lines}")

    st.divider()

    st.markdown("### 🌐 Add Live Context (Optional)")
    st.caption("Ground your post with real-time industry data, news, or benchmarks.")
    
    if "raw_search_results" not in st.session_state:
        st.session_state.raw_search_results = None
        st.session_state.selected_references = []
        
    fetch_context = st.checkbox("Search the web for current data supporting your thesis")
    
    if fetch_context:
        if st.session_state.raw_search_results is None:
            with st.spinner("Fetching live context..."):
                st.session_state.raw_search_results = fetch_live_context(
                    topic=st.session_state.topic, 
                    thesis=brief.thesis or ""
                )
        
        if st.session_state.raw_search_results:
            st.write("**Select the facts you want to explicitly include in your draft:**")
            current_selections = []
            for idx, result in enumerate(st.session_state.raw_search_results):
                with st.container(border=True):
                    if st.checkbox(f"**{result['title']}**", key=f"ref_{idx}"):
                        current_selections.append(result)
                    st.caption(f"{result['snippet']}")
                    st.markdown(f"[Source Link]({result['url']})")
                    
            st.session_state.selected_references = current_selections
        else:
            st.warning("No relevant live data found right now.")
    else:
        st.session_state.selected_references = []
        st.session_state.raw_search_results = None

    st.divider()

    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("Back to answers", use_container_width=True):
            st.session_state.phase = "answers"
            st.rerun()

    with col2:
        if st.button("Write the post", type="primary", use_container_width=True):
            try:
                with st.spinner("Agents are drafting, evaluating, and routing..."):
                    # Use STREAM instead of invoke so the graph hits the HITL breakpoint
                    for event in workflow_app.stream(
                        initial_state(
                            st.session_state.topic, 
                            brief, 
                            st.session_state.selected_references
                        ),
                        config=config
                    ):
                        node_name = list(event.keys())[0]
                        st.toast(f"Agent finished: {node_name}")
                        
            except Exception as e:
                st.error("Something went wrong while generating your post.")
                st.exception(e)
                st.stop()
                
            # Transition to the review station instead of the result page
            st.session_state.phase = "review"
            st.rerun()

# ---------------------------------------------------------------- REVIEW (HITL)
elif st.session_state.phase == "review":
    st.caption("Step 4 — Human Review")
    st.subheader("Approve or Revise")
    
    current_state = workflow_app.get_state(config)
    
    # Check if the graph successfully paused at the breakpoint
    if current_state.next and current_state.next[0] == "finalize":
        st.warning("⏸️ Autonomous routing paused. The draft is ready for your review.")
        
        state_values = current_state.values
        draft = state_values.get("best_post", state_values.get("post", ""))
        
        verdict = state_values.get("verdict")
        if verdict:
            st.caption(f"Craft Score: {verdict.craft_score}/10 | Faithfulness: {verdict.faithfulness}/10")

        # Text area allows manual tweaks before finalizing
        editable_draft = st.text_area("Best Draft So Far (Edit directly, or request AI revisions below):", 
                                      value=draft, height=350)
        
        with st.form("hitl_form"):
            feedback = st.text_input("Request AI revisions (e.g., 'Make it punchier', 'Fix the ending'):")
            
            col1, col2 = st.columns(2)
            approve_btn = col1.form_submit_button("✅ Approve & Publish", type="primary")
            revise_btn = col2.form_submit_button("🔄 Route to Repair Agents")
            
            if approve_btn:
                with st.spinner("Finalizing post..."):
                    # Inject manual edits into the state before finalizing
                    if editable_draft != draft:
                        workflow_app.update_state(config, {"post": editable_draft})
                    
                    final_result = workflow_app.invoke(None, config=config)
                    
                    st.session_state.result = final_result
                    save_run(st.session_state.get("brief_id"), final_result)
                    
                    st.session_state.phase = "result"
                    st.rerun()
                    
            elif revise_btn:
                if not feedback:
                    st.error("Please provide revision instructions if sending back to the repair agents.")
                else:
                    with st.spinner(f"Routing back for revisions..."):
                        # Inject human feedback into the state
                        workflow_app.update_state(
                            config,
                            {"evaluation": {"feedback": f"HUMAN OVERRIDE: {feedback}"}},
                            as_node="evaluate"
                        )
                        # Resume graph execution
                        for event in workflow_app.stream(None, config=config):
                            node_name = list(event.keys())[0]
                            st.toast(f"Agent finished: {node_name}")
                        
                        st.rerun()
    else:
        # Fallback if the graph hit MAX_ITERATIONS and didn't pause properly
        st.session_state.result = current_state.values
        save_run(st.session_state.get("brief_id"), st.session_state.result)
        st.session_state.phase = "result"
        st.rerun()

# ---------------------------------------------------------------- RESULT
elif st.session_state.phase == "result":
    result = st.session_state.result
    brief = st.session_state.brief
    evaluation = result.get("evaluation")
    verdict = result.get("verdict")
    decision = result.get("decision")

    if evaluation is None or verdict is None:
        st.error("Evaluation failed — showing the unevaluated draft.")
        if decision is not None:
            st.caption(decision.reason)
        st.text_area("Draft", value=result.get("post", ""), height=400)
        if st.button("Try again"):
            reset()
            st.rerun()
        st.stop()

    col1, col2 = st.columns([3, 1])

    with col1:
        if verdict.passes_faithfulness:
            st.success("Done")
        else:
            st.error(
                "No draft passed the faithfulness check. This post contains "
                "material not supported by your brief — review every specific "
                "claim before publishing."
            )

    with col2:
        if st.button("Write another", use_container_width=True):
            reset()
            st.rerun()

    m1, m2, m3 = st.columns(3)
    m1.metric("Craft score", f"{verdict.craft_score}/10")
    m2.metric(
        "Winning draft",
        f"#{result['best_iteration']}",
        help=f"Best of {result['iteration'] + 1} drafts generated",
    )
    m3.metric("Faithfulness", f"{verdict.faithfulness}/10")

    if decision is not None:
        if result["best_iteration"] < result["iteration"]:
            st.caption(
                f"Stopped after draft #{result['iteration']}: {decision.reason} "
                f"Returning draft #{result['best_iteration']}, which scored higher."
            )
        else:
            st.caption(f"Stopped because: {decision.reason}")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["📝 Final Post", "🎯 Your Brief", "📊 Evaluation", "📈 Scores"]
    )

    with tab1:
        st.subheader("📝 Final Post")
        
        winning_post = result.get("best_post", result.get("post", ""))
        
        paragraphs = winning_post.split("\n\n")
        original_hook = paragraphs[0] if paragraphs else ""
        post_body = "\n\n".join(paragraphs[1:]) if len(paragraphs) > 1 else ""

        alt_hooks = result.get("best_alternative_hooks", result.get("alternative_hooks", []))

        hook_options = {
            "Original (Keep as generated)": original_hook
        }
        
        for h in alt_hooks:
            snippet = h['text'][:60] + "..." if len(h['text']) > 60 else h['text']
            label = f"{h['angle']}: {snippet}"
            hook_options[label] = h['text']

        if alt_hooks:
            st.markdown("**Want a different opening? Swap the hook:**")
            selected_label = st.radio(
                "Alternative Hooks", 
                options=list(hook_options.keys()), 
                label_visibility="collapsed"
            )
            selected_hook_text = hook_options[selected_label]
            st.divider()
        else:
            selected_hook_text = original_hook
            st.caption("No alternative hooks passed the faithfulness check.")

        final_display_text = f"{selected_hook_text}\n\n{post_body}" if post_body else selected_hook_text

        st.text_area(
            "Final post", 
            value=final_display_text, 
            height=400,
            label_visibility="collapsed"
        )

    with tab2:
        st.caption("The angle the post was written from.")
        render_brief(brief)

        with st.expander("Raw brief (what the agents saw)"):
            st.code(brief.to_prompt_block())
            
    with tab3:
        claims = getattr(evaluation, "unsupported_claims", [])
        if claims:
            st.warning("Claims not supported by your brief:")
            for c in claims:
                st.markdown(f"- {c}")
            st.divider()
        st.json(evaluation.model_dump())

    with tab4:
        gate = "PASS" if verdict.passes_faithfulness else "FAIL"
        st.metric("Faithfulness gate", f"{verdict.faithfulness}/10 — {gate}")
        st.caption(evaluation.scores.faithfulness.observation)
        st.divider()

        st.metric("Weighted craft score", f"{verdict.craft_score}/10")

        df = scores_frame(evaluation)
        fig = px.bar(
            df, x="score", y="metric", orientation="h", text="score",
            range_x=[0, 10], hover_data=["observation"],
        )
        fig.update_layout(yaxis_title="", xaxis_title="Score", height=400)
        st.plotly_chart(fig, use_container_width=True)