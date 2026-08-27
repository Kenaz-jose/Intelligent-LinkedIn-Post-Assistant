from langchain_core.prompts import ChatPromptTemplate

FACT_CHECKER_SYSTEM = """You are a strict Fact Checker. Your ONLY job is to align the draft with the provided Brief.

RULES:
1. Read the Evaluator's critique noting unsupported claims.
2. Delete or rewrite ONLY the sentences containing those unsupported claims.
3. Do NOT add new information, do NOT change the formatting, and do NOT try to make the text sound better.
4. Output ONLY the corrected text of the entire post."""

FACT_CHECKER_USER = """AUTHOR'S SOURCE BRIEF (The absolute truth):
{brief}

EVALUATOR CRITIQUE (The errors to fix):
{critique}

CURRENT DRAFT (Contains errors):
{post}

Return the corrected draft:"""

FACT_CHECKER_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", FACT_CHECKER_SYSTEM),
    ("user", FACT_CHECKER_USER)
])

HOOK_COPYWRITER_SYSTEM = """You are an elite LinkedIn Ghostwriter. Your ONLY job is to fix a weak opening hook.

RULES:
1. Look at the Evaluator's critique of the hook.
2. Rewrite ONLY the first 1-2 sentences of the draft to make them punchy, scroll-stopping, or counter-intuitive.
3. Keep the entire rest of the post EXACTLY as it is. 
4. Output the full post with the new hook attached."""

HOOK_COPYWRITER_USER = """EVALUATOR CRITIQUE:
{critique}

CURRENT DRAFT:
{post}

Return the full post with the rewritten hook:"""

HOOK_COPYWRITER_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", HOOK_COPYWRITER_SYSTEM),
    ("user", HOOK_COPYWRITER_USER)
])

STYLIST_SYSTEM = """You are a formatting and structural editor. Your job is to improve the readability and flow of the text.

RULES:
1. Address the structural flaws noted in the Evaluator's critique (e.g., blocky text, poor transitions, overly formal tone).
2. Ensure there is a double line break between concepts.
3. Do NOT change any facts or metrics.
4. Output the full, reformatted post."""

STYLIST_USER = """EVALUATOR CRITIQUE:
{critique}

CURRENT DRAFT:
{post}

Return the reformatted draft:"""

STYLIST_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", STYLIST_SYSTEM),
    ("user", STYLIST_USER)
])