"""
SQLAlchemy ORM models for the Adaptive Learning Platform.
All models use UUID primary keys and include created_at / updated_at timestamps.
"""
import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Float, ForeignKey,
    Integer, String, Text, JSON, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


# ─── Mixins ──────────────────────────────────────────────────────────────────

class UUIDMixin:
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ─── Users & Roles ────────────────────────────────────────────────────────────

class User(Base, UUIDMixin, TimestampMixin):
    """Core user account. Role determines student/teacher access."""
    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # student | teacher | admin
    is_active = Column(Boolean, default=True, nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    student_profile = relationship("Student", back_populates="user", uselist=False)
    teacher_profile = relationship("Teacher", back_populates="user", uselist=False)


class Student(Base, UUIDMixin, TimestampMixin):
    """Student profile — linked 1:1 to User."""
    __tablename__ = "students"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    grade_level = Column(String(50), nullable=True)
    learning_preferences = Column(JSON, default=dict)  # e.g. {"style": "visual"}
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="student_profile")
    mastery_records = relationship("StudentTopicMastery", back_populates="student")
    learner_profile = relationship("LearnerProfile", back_populates="student", uselist=False)
    quiz_attempts = relationship("QuizAttempt", back_populates="student")
    learning_sessions = relationship("LearningSession", back_populates="student")
    events = relationship("StudentEvent", back_populates="student")
    knowledge_gaps = relationship("KnowledgeGap", back_populates="student")
    recommendations = relationship("Recommendation", back_populates="student")
    study_plans = relationship("StudyPlan", back_populates="student")
    llm_conversations = relationship("LLMConversation", back_populates="student")
    experiment_participations = relationship("ExperimentParticipant", back_populates="student")
    model_predictions = relationship("ModelPrediction", back_populates="student")
    feedback_given = relationship("Feedback", back_populates="student")


class Teacher(Base, UUIDMixin, TimestampMixin):
    """Teacher profile — linked 1:1 to User."""
    __tablename__ = "teachers"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    department = Column(String(100), nullable=True)

    # Relationships
    user = relationship("User", back_populates="teacher_profile")
    courses = relationship("Course", back_populates="teacher")


# ─── Courses & Content ───────────────────────────────────────────────────────

class Course(Base, UUIDMixin, TimestampMixin):
    """A course containing multiple topics."""
    __tablename__ = "courses"

    teacher_id = Column(UUID(as_uuid=True), ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    subject_area = Column(String(100), nullable=False)
    difficulty_level = Column(String(20), default="intermediate")  # beginner|intermediate|advanced
    is_active = Column(Boolean, default=True)
    thumbnail_url = Column(String(500), nullable=True)

    # Relationships
    teacher = relationship("Teacher", back_populates="courses")
    topics = relationship("Topic", back_populates="course", order_by="Topic.order_index")
    quizzes = relationship("Quiz", back_populates="course")
    rag_documents = relationship("RAGDocument", back_populates="course")


class Topic(Base, UUIDMixin, TimestampMixin):
    """A topic within a course."""
    __tablename__ = "topics"

    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, default=0)
    difficulty_level = Column(String(20), default="beginner")
    learning_objectives = Column(JSON, default=list)  # list of objective strings
    estimated_minutes = Column(Integer, default=30)
    is_active = Column(Boolean, default=True)

    # Relationships
    course = relationship("Course", back_populates="topics")
    subtopics = relationship("Subtopic", back_populates="topic")
    resources = relationship("LearningResource", back_populates="topic")
    questions = relationship("Question", back_populates="topic")
    mastery_records = relationship("StudentTopicMastery", back_populates="topic")
    knowledge_gaps = relationship("KnowledgeGap", back_populates="topic")
    prerequisites_as_topic = relationship(
        "Prerequisite",
        foreign_keys="Prerequisite.topic_id",
        back_populates="topic",
    )
    prerequisites_as_prereq = relationship(
        "Prerequisite",
        foreign_keys="Prerequisite.prerequisite_topic_id",
        back_populates="prerequisite_topic",
    )
    knowledge_graph_nodes = relationship("KnowledgeGraphNode", back_populates="topic")


class Subtopic(Base, UUIDMixin, TimestampMixin):
    """A subtopic within a topic (e.g., Base Cases within Recursion)."""
    __tablename__ = "subtopics"

    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, default=0)

    topic = relationship("Topic", back_populates="subtopics")
    questions = relationship("Question", back_populates="subtopic")


class Prerequisite(Base, UUIDMixin):
    """Represents a prerequisite relationship between topics."""
    __tablename__ = "prerequisites"
    __table_args__ = (
        UniqueConstraint("topic_id", "prerequisite_topic_id", name="uq_topic_prereq"),
    )

    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    prerequisite_topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    relationship_type = Column(String(50), default="prerequisite_of")
    required_mastery = Column(Float, default=0.60)

    topic = relationship("Topic", foreign_keys=[topic_id], back_populates="prerequisites_as_topic")
    prerequisite_topic = relationship("Topic", foreign_keys=[prerequisite_topic_id], back_populates="prerequisites_as_prereq")


class LearningResource(Base, UUIDMixin, TimestampMixin):
    """A learning resource (video, article, exercise, etc.) for a topic."""
    __tablename__ = "learning_resources"

    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    resource_type = Column(String(50), nullable=False)  # video|article|exercise|quiz|interactive
    url = Column(String(1000), nullable=True)
    content = Column(Text, nullable=True)  # for inline content
    difficulty_level = Column(String(20), default="beginner")
    duration_minutes = Column(Integer, default=10)
    is_active = Column(Boolean, default=True)
    resource_metadata = Column(JSON, default=dict)  # renamed from 'metadata' (reserved)

    topic = relationship("Topic", back_populates="resources")


# ─── Assessment ──────────────────────────────────────────────────────────────

class Question(Base, UUIDMixin, TimestampMixin):
    """A quiz question, optionally AI-generated."""
    __tablename__ = "questions"

    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    subtopic_id = Column(UUID(as_uuid=True), ForeignKey("subtopics.id", ondelete="SET NULL"), nullable=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), default="multiple_choice")  # multiple_choice|short_answer|true_false
    difficulty_level = Column(String(20), default="beginner")
    correct_answer = Column(JSON, nullable=False)  # {"answer": "B"} or {"text": "..."}
    explanation = Column(Text, nullable=True)
    tags = Column(JSON, default=list)
    is_ai_generated = Column(Boolean, default=False)
    is_validated = Column(Boolean, default=True)

    topic = relationship("Topic", back_populates="questions")
    subtopic = relationship("Subtopic", back_populates="questions")
    options = relationship("QuestionOption", back_populates="question", cascade="all, delete-orphan")
    student_answers = relationship("StudentAnswer", back_populates="question")


class QuestionOption(Base, UUIDMixin):
    """An option for a multiple-choice question."""
    __tablename__ = "question_options"

    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    option_text = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False)
    order_index = Column(Integer, default=0)

    question = relationship("Question", back_populates="options")


class Quiz(Base, UUIDMixin, TimestampMixin):
    """A quiz associated with a course/topic."""
    __tablename__ = "quizzes"

    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    time_limit_minutes = Column(Integer, nullable=True)
    difficulty_level = Column(String(20), default="beginner")
    is_adaptive = Column(Boolean, default=False)
    is_ai_generated = Column(Boolean, default=False)

    course = relationship("Course", back_populates="quizzes")
    quiz_questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")
    attempts = relationship("QuizAttempt", back_populates="quiz")


class QuizQuestion(Base):
    """Junction table for Quiz ↔ Question."""
    __tablename__ = "quiz_questions"

    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="CASCADE"), primary_key=True)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True)
    order_index = Column(Integer, default=0)

    quiz = relationship("Quiz", back_populates="quiz_questions")
    question = relationship("Question")


class QuizAttempt(Base, UUIDMixin, TimestampMixin):
    """A student's attempt at a quiz."""
    __tablename__ = "quiz_attempts"

    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    score = Column(Float, nullable=True)  # 0.0-1.0, null if not yet scored
    total_questions = Column(Integer, nullable=False)
    correct_count = Column(Integer, default=0)
    time_spent_seconds = Column(Integer, default=0)
    status = Column(String(20), default="in_progress")  # in_progress|completed|abandoned
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    quiz = relationship("Quiz", back_populates="attempts")
    student = relationship("Student", back_populates="quiz_attempts")
    answers = relationship("StudentAnswer", back_populates="attempt", cascade="all, delete-orphan")


class StudentAnswer(Base, UUIDMixin):
    """A student's answer to a question within a quiz attempt."""
    __tablename__ = "student_answers"

    attempt_id = Column(UUID(as_uuid=True), ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    student_answer = Column(JSON, nullable=True)  # {"answer": "A"} or {"text": "..."}
    is_correct = Column(Boolean, nullable=True)
    time_spent_seconds = Column(Integer, default=0)
    hint_used = Column(Boolean, default=False)
    attempt_number = Column(Integer, default=1)
    answered_at = Column(DateTime(timezone=True), server_default=func.now())

    attempt = relationship("QuizAttempt", back_populates="answers")
    question = relationship("Question", back_populates="student_answers")


# ─── Learning Analytics ───────────────────────────────────────────────────────

class LearningSession(Base, UUIDMixin, TimestampMixin):
    """A student's learning session on the platform."""
    __tablename__ = "learning_sessions"

    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="SET NULL"), nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, default=0)
    session_type = Column(String(50), default="study")  # study|quiz|tutor|review

    student = relationship("Student", back_populates="learning_sessions")
    events = relationship("StudentEvent", back_populates="session")


class StudentEvent(Base, UUIDMixin):
    """A granular tracking event (resource view, quiz start, etc.)."""
    __tablename__ = "student_events"

    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("learning_sessions.id", ondelete="SET NULL"), nullable=True)
    event_type = Column(String(100), nullable=False, index=True)
    # event_type examples: resource_view, video_started, video_completed, quiz_started,
    #   quiz_completed, hint_requested, tutor_message, topic_revisit
    resource_id = Column(UUID(as_uuid=True), ForeignKey("learning_resources.id", ondelete="SET NULL"), nullable=True)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="SET NULL"), nullable=True, index=True)
    event_data = Column(JSON, default=dict)  # flexible extra data
    occurred_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    student = relationship("Student", back_populates="events")
    session = relationship("LearningSession", back_populates="events")


class StudentTopicMastery(Base, UUIDMixin, TimestampMixin):
    """Computed mastery score for a student-topic pair. Updated after each quiz."""
    __tablename__ = "student_topic_mastery"
    __table_args__ = (
        UniqueConstraint("student_id", "topic_id", name="uq_student_topic_mastery"),
    )

    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)
    mastery_score = Column(Float, default=0.0)        # 0.0–1.0
    confidence = Column(Float, default=0.0)            # confidence in mastery estimate
    attempts = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    recent_accuracy = Column(Float, default=0.0)      # accuracy in last 3 attempts
    average_accuracy = Column(Float, default=0.0)
    mastery_level = Column(String(20), default="not_started")  # not_started|beginner|intermediate|advanced|mastered
    last_assessed_at = Column(DateTime(timezone=True), nullable=True)

    student = relationship("Student", back_populates="mastery_records")
    topic = relationship("Topic", back_populates="mastery_records")


class LearnerProfile(Base, UUIDMixin, TimestampMixin):
    """Aggregated learner model — updated after each analytics run."""
    __tablename__ = "learner_profiles"

    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), unique=True, nullable=False)
    performance_summary = Column(JSON, default=dict)     # {topic_id: accuracy, ...}
    engagement_metrics = Column(JSON, default=dict)      # {sessions_per_week, avg_session_min, ...}
    learning_preferences = Column(JSON, default=dict)
    weak_topics = Column(JSON, default=list)             # [topic_id, ...]
    strong_topics = Column(JSON, default=list)
    current_learning_path = Column(JSON, default=list)   # ordered list of topic_ids
    recommendation_history = Column(JSON, default=list)
    intervention_history = Column(JSON, default=list)
    overall_mastery = Column(Float, default=0.0)
    engagement_score = Column(Float, default=0.0)
    current_streak_days = Column(Integer, default=0)

    student = relationship("Student", back_populates="learner_profile")


# ─── Knowledge Gap & Recommendations ─────────────────────────────────────────

class KnowledgeGap(Base, UUIDMixin, TimestampMixin):
    """A detected knowledge gap for a student in a specific topic."""
    __tablename__ = "knowledge_gaps"

    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)
    gap_score = Column(Float, nullable=False)         # 0.0–1.0 (higher = bigger gap)
    severity = Column(String(20), nullable=False)     # low|medium|high|critical
    priority = Column(Integer, default=5)             # 1 = highest priority
    evidence = Column(JSON, default=dict)             # signals that contributed to gap
    confidence = Column(Float, default=0.5)           # confidence in gap detection
    affected_concepts = Column(JSON, default=list)
    prerequisite_info = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    student = relationship("Student", back_populates="knowledge_gaps")
    topic = relationship("Topic", back_populates="knowledge_gaps")


class Recommendation(Base, UUIDMixin, TimestampMixin):
    """A personalized recommendation for a student."""
    __tablename__ = "recommendations"

    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    resource_id = Column(UUID(as_uuid=True), ForeignKey("learning_resources.id", ondelete="SET NULL"), nullable=True)
    recommendation_type = Column(String(50), nullable=False)  # topic|resource|quiz|review
    score = Column(Float, nullable=False)                     # recommendation score
    confidence = Column(Float, nullable=False)                # confidence estimate
    priority = Column(Integer, default=5)
    status = Column(String(20), default="pending")            # pending|accepted|rejected|expired
    context_snapshot = Column(JSON, default=dict)             # learner context at time of rec
    acted_on_at = Column(DateTime(timezone=True), nullable=True)

    student = relationship("Student", back_populates="recommendations")
    evidence = relationship("RecommendationEvidence", back_populates="recommendation", cascade="all, delete-orphan")


class RecommendationEvidence(Base, UUIDMixin):
    """Supporting evidence for a recommendation (for XAI display)."""
    __tablename__ = "recommendation_evidence"

    recommendation_id = Column(UUID(as_uuid=True), ForeignKey("recommendations.id", ondelete="CASCADE"), nullable=False, index=True)
    factor_name = Column(String(100), nullable=False)
    factor_value = Column(Float, nullable=True)
    factor_weight = Column(Float, nullable=True)
    shap_value = Column(Float, nullable=True)
    human_explanation = Column(Text, nullable=True)
    display_order = Column(Integer, default=0)

    recommendation = relationship("Recommendation", back_populates="evidence")


# ─── Study Plans ─────────────────────────────────────────────────────────────

class StudyPlan(Base, UUIDMixin, TimestampMixin):
    """A daily or weekly study plan for a student."""
    __tablename__ = "study_plans"

    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_date = Column(Date, nullable=False)
    plan_type = Column(String(20), default="daily")  # daily|weekly
    total_minutes = Column(Integer, default=30)
    status = Column(String(20), default="active")  # active|completed|expired

    student = relationship("Student", back_populates="study_plans")
    items = relationship("StudyPlanItem", back_populates="plan", order_by="StudyPlanItem.order_index", cascade="all, delete-orphan")


class StudyPlanItem(Base, UUIDMixin):
    """A single activity in a study plan."""
    __tablename__ = "study_plan_items"

    plan_id = Column(UUID(as_uuid=True), ForeignKey("study_plans.id", ondelete="CASCADE"), nullable=False)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    resource_id = Column(UUID(as_uuid=True), ForeignKey("learning_resources.id", ondelete="SET NULL"), nullable=True)
    activity_type = Column(String(50), nullable=False)  # concept|practice|quiz|review|tutor
    duration_minutes = Column(Integer, nullable=False)
    reason = Column(Text, nullable=True)
    order_index = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    plan = relationship("StudyPlan", back_populates="items")


# ─── LLM Conversations ────────────────────────────────────────────────────────

class LLMConversation(Base, UUIDMixin, TimestampMixin):
    """An AI tutor conversation session."""
    __tablename__ = "llm_conversations"

    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    conversation_type = Column(String(50), default="tutor")  # tutor|explain|quiz|hint|summarize
    context_snapshot = Column(JSON, default=dict)  # learner context at start
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)

    student = relationship("Student", back_populates="llm_conversations")
    messages = relationship("LLMMessage", back_populates="conversation", order_by="LLMMessage.created_at", cascade="all, delete-orphan")


class LLMMessage(Base, UUIDMixin):
    """A single message in an LLM conversation."""
    __tablename__ = "llm_messages"

    conversation_id = Column(UUID(as_uuid=True), ForeignKey("llm_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user|assistant|system
    content = Column(Text, nullable=False)
    provider = Column(String(50), nullable=True)   # google|openai|local
    model = Column(String(100), nullable=True)
    tokens_used = Column(Integer, nullable=True)
    latency_ms = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversation = relationship("LLMConversation", back_populates="messages")


# ─── RAG ──────────────────────────────────────────────────────────────────────

class RAGDocument(Base, UUIDMixin, TimestampMixin):
    """An educational document ingested into the RAG pipeline."""
    __tablename__ = "rag_documents"

    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False)  # pdf|text|markdown|url
    file_path = Column(String(1000), nullable=True)
    doc_metadata = Column(JSON, default=dict)  # renamed from 'metadata' (reserved)
    is_indexed = Column(Boolean, default=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    indexed_at = Column(DateTime(timezone=True), nullable=True)

    course = relationship("Course", back_populates="rag_documents")
    chunks = relationship("RAGChunk", back_populates="document", cascade="all, delete-orphan")


class RAGChunk(Base, UUIDMixin, TimestampMixin):
    """A text chunk from a RAG document with its vector store ID."""
    __tablename__ = "rag_chunks"

    document_id = Column(UUID(as_uuid=True), ForeignKey("rag_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_metadata = Column(JSON, default=dict)  # {page, section, topic, difficulty} — renamed from 'metadata'
    vector_id = Column(String(255), nullable=True)  # ID in ChromaDB

    document = relationship("RAGDocument", back_populates="chunks")


# ─── Knowledge Graph ──────────────────────────────────────────────────────────

class KnowledgeGraphNode(Base, UUIDMixin, TimestampMixin):
    """A node in the educational knowledge graph."""
    __tablename__ = "knowledge_graph_nodes"

    node_type = Column(String(50), nullable=False)  # DOMAIN|TOPIC|SUBTOPIC|CONCEPT|SKILL
    label = Column(String(255), nullable=False)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    attributes = Column(JSON, default=dict)

    topic = relationship("Topic", back_populates="knowledge_graph_nodes")
    outgoing_edges = relationship("KnowledgeGraphEdge", foreign_keys="KnowledgeGraphEdge.source_node_id", back_populates="source_node")
    incoming_edges = relationship("KnowledgeGraphEdge", foreign_keys="KnowledgeGraphEdge.target_node_id", back_populates="target_node")


class KnowledgeGraphEdge(Base, UUIDMixin, TimestampMixin):
    """A directed edge in the knowledge graph."""
    __tablename__ = "knowledge_graph_edges"
    __table_args__ = (
        UniqueConstraint("source_node_id", "target_node_id", "relationship_type", name="uq_kg_edge"),
    )

    source_node_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_graph_nodes.id", ondelete="CASCADE"), nullable=False)
    target_node_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_graph_nodes.id", ondelete="CASCADE"), nullable=False)
    relationship_type = Column(String(50), nullable=False)  # prerequisite_of|part_of|related_to|follows
    weight = Column(Float, default=1.0)
    attributes = Column(JSON, default=dict)

    source_node = relationship("KnowledgeGraphNode", foreign_keys=[source_node_id], back_populates="outgoing_edges")
    target_node = relationship("KnowledgeGraphNode", foreign_keys=[target_node_id], back_populates="incoming_edges")


# ─── ML & Explainability ─────────────────────────────────────────────────────

class ModelPrediction(Base, UUIDMixin, TimestampMixin):
    """A logged ML model prediction for audit and evaluation."""
    __tablename__ = "model_predictions"

    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=False)
    prediction_type = Column(String(50), nullable=False)  # mastery|gap|performance
    predicted_value = Column(Float, nullable=False)
    actual_value = Column(Float, nullable=True)  # filled in retrospectively
    feature_values = Column(JSON, default=dict)
    predicted_at = Column(DateTime(timezone=True), server_default=func.now())

    student = relationship("Student", back_populates="model_predictions")
    explanation = relationship("ModelExplanation", back_populates="prediction", uselist=False, cascade="all, delete-orphan")


class ModelExplanation(Base, UUIDMixin, TimestampMixin):
    """SHAP/LIME explanation for a model prediction."""
    __tablename__ = "model_explanations"

    prediction_id = Column(UUID(as_uuid=True), ForeignKey("model_predictions.id", ondelete="CASCADE"), unique=True, nullable=False)
    shap_values = Column(JSON, nullable=True)
    lime_values = Column(JSON, nullable=True)
    feature_importance = Column(JSON, nullable=True)
    human_explanation = Column(Text, nullable=True)

    prediction = relationship("ModelPrediction", back_populates="explanation")


# ─── Research Experiments ─────────────────────────────────────────────────────

class Experiment(Base, UUIDMixin, TimestampMixin):
    """A research experiment definition."""
    __tablename__ = "experiments"

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    hypothesis = Column(Text, nullable=True)
    control_conditions = Column(JSON, default=dict)
    treatment_conditions = Column(JSON, default=dict)
    status = Column(String(20), default="draft")  # draft|active|completed|archived
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)

    participants = relationship("ExperimentParticipant", back_populates="experiment")
    results = relationship("ExperimentResult", back_populates="experiment")


class ExperimentParticipant(Base, UUIDMixin, TimestampMixin):
    """A student enrolled in an experiment group."""
    __tablename__ = "experiment_participants"
    __table_args__ = (
        UniqueConstraint("experiment_id", "student_id", name="uq_exp_participant"),
    )

    experiment_id = Column(UUID(as_uuid=True), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    group_name = Column(String(50), nullable=False)  # control|treatment_adaptive|treatment_xai
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())

    experiment = relationship("Experiment", back_populates="participants")
    student = relationship("Student", back_populates="experiment_participations")
    results = relationship("ExperimentResult", back_populates="participant")


class ExperimentResult(Base, UUIDMixin, TimestampMixin):
    """A metric measurement for an experiment participant."""
    __tablename__ = "experiment_results"

    experiment_id = Column(UUID(as_uuid=True), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, index=True)
    participant_id = Column(UUID(as_uuid=True), ForeignKey("experiment_participants.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_name = Column(String(100), nullable=False)  # pre_test|post_test|engagement_score|trust_rating
    metric_value = Column(Float, nullable=False)
    phase = Column(String(50), nullable=False)  # pre_test|intervention|post_test|retention|survey
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())

    experiment = relationship("Experiment", back_populates="results")
    participant = relationship("ExperimentParticipant", back_populates="results")


# ─── Feedback ─────────────────────────────────────────────────────────────────

class Feedback(Base, UUIDMixin, TimestampMixin):
    """Student feedback on recommendations, tutor responses, or the platform."""
    __tablename__ = "feedback"

    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    feedback_type = Column(String(50), nullable=False)  # recommendation|tutor|platform|explanation
    reference_id = Column(UUID(as_uuid=True), nullable=True)  # ID of referenced object
    rating = Column(Integer, nullable=True)  # 1-5
    comment = Column(Text, nullable=True)

    student = relationship("Student", back_populates="feedback_given")
