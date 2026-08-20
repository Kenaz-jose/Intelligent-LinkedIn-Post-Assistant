from pydantic import BaseModel, Field

"""
INTERVIEW LAYER
These models represent the temporary conversation between
the Perspective Layer and the user.

 Flow:

     Topic
       ↓
   Interview Agent
       ↓
   QuestionSet
       ↓
   User Answers
       ↓
     Answer

 The interview layer's job is to collect raw information
 from the user. It should NOT try to write the final
 LinkedIn post.
"""

class InterviewQuestion(BaseModel):
    """
    Represents one question asked during a perspective interview.

    Each question contains:
    - id          : Unique identifier used to connect an answer
                    back to this question.
    - text        : The actual question shown to the user.
    - why         : Explains why this question is being asked.
                    This can be displayed in the UI to encourage
                    more thoughtful answers.
    - placeholder : Example/guidance shown inside the answer box.
                    This helps the user understand the type of
                    answer the system is looking for.
    """

    id: str
    text: str
    why: str = ""  
    placeholder: str = ""     

class QuestionSet(BaseModel):
    """
    Represents the collection of questions generated for
    one perspective interview.

    The Interview Agent should return a QuestionSet instead
    of an unstructured list.

    Example:

        QuestionSet(
            questions=[
                InterviewQuestion(...),
                InterviewQuestion(...),
                InterviewQuestion(...)
            ]
        )

    Field(default_factory=list) creates a NEW empty list for
    every QuestionSet instance.

    This is safer than using [] directly as a default value.
    """

    questions: list[InterviewQuestion] = Field(default_factory=list)


class Answer(BaseModel):
    """
    Represents the user's answer to one interview question.

    question_id:
        Connects the answer to the original question.

    question_text:
        Stores the actual question along with the answer.
        This makes the Answer object self-contained and useful
        even if the original QuestionSet is no longer available.

    answer:
        The user's raw response.

    Example:

        Answer(
            question_id="q1",
            question_text="What do you think about AI agents?",
            answer="I think AI agents are..."
        )
    """

    question_id: str
    question_text: str = ""
    answer: str = ""

"""
 PERSPECTIVE LAYER
 PerspectiveBrief is the most important object in this file.

 The interview collects RAW INFORMATION.

 PerspectiveBrief converts that information into a structured
 representation of what the user actually thinks.

 It acts as the contract between:

       Interview Layer
              ↓
       PerspectiveBrief
              ↓
       Content Generation Layer

 The Content Generator should NOT have to discover the user's
 perspective itself. It should receive an already synthesized
 PerspectiveBrief.
"""

class PerspectiveBrief(BaseModel):
    """
    Structured representation of the user's perspective on
    one specific topic.

    The fields intentionally separate different kinds of
    information so downstream agents can use them correctly.

    topic:
        The subject being discussed.

    thesis:
        The user's central position or claim.

        This should ideally be something that can be agreed with
        or disagreed with.

        Weak:
            "AI is changing software development."

        Stronger:
            "AI coding agents will change software development
             more through workflow redesign than replacing
             developers."

    evidence:
        First-hand experiences provided by the user.

        This is one of the most important fields for preventing
        generic AI-generated content.

    details:
        Concrete supporting information such as:
        - numbers
        - tools
        - timeframes
        - projects
        - technologies
        - specific events

    audience:
        The intended audience for the eventual content.

    takeaway:
        The main lesson or action the reader should leave with.
    """
    topic: str = ""
    thesis: str = ""
    evidence: list[str] = Field(default_factory=list)
    details: list[str] = Field(default_factory=list)
    audience: str = ""
    takeaway: str = ""

    def to_prompt_block(self) -> str:
        """
        Converts the PerspectiveBrief into a standardized text
        block that can be inserted into an LLM prompt.

        Keeping this formatting inside the schema gives the
        PerspectiveBrief ONE canonical representation.

        This is useful because multiple agents may consume the
        same PerspectiveBrief:

            Generator
            Evaluator
            Refiner
            Critic
            etc.

        If every agent formats the object differently, their
        understanding of the user's perspective can drift.

        Therefore:

            PerspectiveBrief
                    ↓
             to_prompt_block()
                    ↓
              Same context
                    ↓
        Multiple downstream agents
        """

        def bullets(items: list[str]) -> str:
            """
            Converts a list into an indented bullet list.

            Example:

                ["Python", "LangGraph"]

            becomes:

                - Python
                - LangGraph
            """

            return (
                "\n".join(f"  - {i}" for i in items)
                if items
                else "  - (none given)"
            )

        return (
            f"TOPIC: {self.topic}\n"
            f"THE AUTHOR'S THESIS: {self.thesis}\n"
            f"THEIR FIRST-HAND EVIDENCE:\n{bullets(self.evidence)}\n"
            f"CONCRETE DETAILS:\n{bullets(self.details)}\n"
            f"AUDIENCE: {self.audience or 'Professionals on LinkedIn'}\n"
            f"READER TAKEAWAY: {self.takeaway}"
        )

    def is_thin(self) -> bool:
        """
        Performs a cheap deterministic check to determine
        whether the perspective contains enough information
        to produce personal content.

        A perspective is considered "thin" if:
        1. The thesis is extremely short, OR
        2. There is no first-hand evidence.

        This intentionally does NOT use an LLM.

        The purpose is to catch obvious weak inputs cheaply
        before spending another LLM call.

        Example of a thin perspective:

            thesis = "AI is changing everything"
            evidence = []

        Example of a stronger perspective:

            thesis = "AI coding agents shift developers
                      from implementation toward verification"

            evidence = [
                "I used an agent to build a feature",
                "Most of my time was spent reviewing its output"
            ]

        FUTURE:
        This can eventually evolve into a richer Perspective
        Quality Score containing things such as:

            - Specificity
            - Evidence strength
            - Distinctiveness
            - Reasoning depth
            - Actionability
            - Originality
        """

        return len(self.thesis.split()) < 5 or not self.evidence

"""
 LONG-TERM USER MEMORY
 UserMemory represents what LinkedInForge has learned about
 this specific person across multiple interviews.

 PerspectiveBrief is TOPIC-SPECIFIC.

 UserMemory is USER-SPECIFIC.

 Example:

   PerspectiveBrief
       "AI coding agents"
             ↓
       UserMemory
             ↓
   Known view:
       "AI agents are useful for repetitive implementation."

 Future interview:

   UserMemory
        ↓
   Interview Agent
        ↓
   More personalized questions
"""

class UserMemory(BaseModel):
    """
    Lightweight long-term memory for a LinkedInForge user.

    This is intentionally simple for the MVP.

    IMPORTANT:
    This should eventually evolve from simple lists into a
    structured/retrievable memory system.

    Possible future evolution:

        Lists
          ↓
        Structured memories
          ↓
        Semantic retrieval
          ↓
        Relationships between memories
          ↓
        Perspective Graph / Digital Twin
    """

    user_id: str
    known_views: list[str] = Field(default_factory=list)
    known_experiences: list[str] = Field(default_factory=list)
    past_topics: list[str] = Field(default_factory=list)
    audience: str = ""
    interviews_done: int = 0

    def to_prompt_block(self) -> str:
        """
        Converts the user's memory into a standardized prompt
        block for the Interview Agent or other agents.

        If this is the first interview, explicitly tell the LLM
        that nothing is known.

        An empty prompt can be ambiguous to an LLM.
        Explicitly saying "nothing known yet" makes the state
        clear.
        """

        if self.interviews_done == 0:
            return "(First interview with this person — nothing known yet)"

        def bullets(items: list[str]) -> str:
            return (
                "\n".join(f"  - {i}" for i in items)
                if items
                else "  - (none known)"
            )

        return (
            f"KNOWN VIEWS:\n{bullets(self.known_views)}\n"
            f"KNOWN EXPERIENCES:\n{bullets(self.known_experiences)}\n"
            f"PAST TOPICS:\n{bullets(self.past_topics)}\n"
            f"AUDIENCE: {self.audience or '(not known)'}\n"
            f"INTERVIEWS COMPLETED: {self.interviews_done}"
        )


    def absorb(self, brief: PerspectiveBrief) -> "UserMemory":
        """
        Adds information from a newly created PerspectiveBrief
        into the user's long-term memory.

        Flow:

            PerspectiveBrief
                    ↓
                 absorb()
                    ↓
              UserMemory
                    ↓
           Future interviews

        This method intentionally does NOT use an LLM.

        The PerspectiveBrief has already been synthesized.
        Memory updates should therefore be deterministic.

        Benefits:
        - cheaper
        - faster
        - predictable
        - no additional hallucination risk
        """

        def add(target: list[str],items: list[str],cap: int) -> list[str]:
            """
            Add new items to a memory list.

            Responsibilities:

            1. Avoid duplicates.
            2. Ignore empty strings.
            3. Keep the memory bounded.

            Deduplication is case-insensitive.

            Example:

                Existing:
                    "AI agents are useful"

                New:
                    "ai agents are useful"

                Result:
                    Only one copy is stored.
            """

            seen = {
                t.strip().lower()
                for t in target
            }

            for item in items:

                key = item.strip().lower()
                if key and key not in seen:

                    target.append(item.strip())
                    seen.add(key)
            return target[-cap:]


        if brief.thesis:
            self.known_views = add(self.known_views,[brief.thesis],20)

        self.known_experiences = add(self.known_experiences,brief.evidence,20)

        if brief.topic:
            self.past_topics = add(self.past_topics,[brief.topic],50)


        if brief.audience:
            self.audience = brief.audience


        self.interviews_done += 1

        return self