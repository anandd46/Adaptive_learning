"""
Synthetic Dataset Generator for the Adaptive Learning Platform.
Generates realistic student interaction data for development and demonstration.

IMPORTANT: This data is SYNTHETIC/DEMO only.
It MUST NOT be used as evidence for research hypotheses.
All generated data is clearly labeled as SYNTHETIC.
"""
import random
import numpy as np
import json
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional

# ─── Reproducible Seed ───────────────────────────────────────────────────────
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# ─── Demo Course Content ─────────────────────────────────────────────────────
DEMO_COURSES = [
    {
        "title": "Introduction to Python Programming",
        "subject_area": "Computer Science",
        "topics": [
            {"title": "Variables & Data Types", "difficulty": "beginner", "order": 1},
            {"title": "Control Flow", "difficulty": "beginner", "order": 2},
            {"title": "Functions", "difficulty": "beginner", "order": 3},
            {"title": "Lists & Dictionaries", "difficulty": "intermediate", "order": 4},
            {"title": "Recursion", "difficulty": "intermediate", "order": 5},
            {"title": "File I/O", "difficulty": "intermediate", "order": 6},
            {"title": "Object-Oriented Programming", "difficulty": "advanced", "order": 7},
            {"title": "Error Handling", "difficulty": "intermediate", "order": 8},
            {"title": "Modules & Packages", "difficulty": "intermediate", "order": 9},
            {"title": "Data Structures", "difficulty": "advanced", "order": 10},
        ],
        "prerequisites": {
            "Functions": ["Variables & Data Types", "Control Flow"],
            "Recursion": ["Functions"],
            "Object-Oriented Programming": ["Functions", "Lists & Dictionaries"],
            "Data Structures": ["Lists & Dictionaries", "Object-Oriented Programming"],
            "File I/O": ["Functions"],
            "Error Handling": ["Functions"],
            "Modules & Packages": ["Functions"],
        }
    }
]

# ─── Learner Archetypes ───────────────────────────────────────────────────────
LEARNER_ARCHETYPES = {
    "fast_learner": {
        "base_mastery": 0.85,
        "learning_rate": 0.08,
        "consistency": 0.9,
        "engagement": 0.85,
        "weight": 0.15,
    },
    "steady_learner": {
        "base_mastery": 0.65,
        "learning_rate": 0.05,
        "consistency": 0.8,
        "engagement": 0.7,
        "weight": 0.35,
    },
    "struggling_learner": {
        "base_mastery": 0.35,
        "learning_rate": 0.03,
        "consistency": 0.6,
        "engagement": 0.55,
        "weight": 0.25,
    },
    "inconsistent_learner": {
        "base_mastery": 0.55,
        "learning_rate": 0.04,
        "consistency": 0.4,
        "engagement": 0.6,
        "weight": 0.15,
    },
    "at_risk_learner": {
        "base_mastery": 0.20,
        "learning_rate": 0.02,
        "consistency": 0.3,
        "engagement": 0.35,
        "weight": 0.10,
    },
}

STUDENT_NAMES = [
    "Alice Chen", "Bob Kumar", "Carol Davis", "Dan Wilson", "Eve Martinez",
    "Frank Lee", "Grace Patel", "Henry Brown", "Iris Johnson", "Jack Smith",
    "Kira Anderson", "Leo Garcia", "Mia Thompson", "Noah White", "Olivia Harris",
    "Paul Clark", "Quinn Rodriguez", "Rose Lewis", "Sam Walker", "Tara Hall",
    "Uma Allen", "Victor Young", "Wendy King", "Xander Wright", "Yara Scott",
    "Zoe Green", "Alex Turner", "Blake Nelson", "Chris Baker", "Dana Carter",
    "Ethan Mitchell", "Fiona Perez", "George Roberts", "Hannah Jackson", "Ivan Flores",
    "Julia Hill", "Kyle Adams", "Laura Campbell", "Mike Parker", "Nancy Evans",
    "Oscar Collins", "Penny Edwards", "Quinn Stewart", "Rachel Morris", "Sam Rogers",
    "Tina Cook", "Uma Morgan", "Victor Reed", "Wendy Bell", "Xavier Murphy",
]


@dataclass
class SyntheticStudent:
    """Represents a synthetic student with archetype-based behavior."""
    id: str
    name: str
    email: str
    archetype: str
    base_mastery: float
    learning_rate: float
    consistency: float
    engagement: float
    topic_mastery: dict = field(default_factory=dict)
    quiz_history: list = field(default_factory=list)
    events: list = field(default_factory=list)


def select_archetype() -> str:
    """Select learner archetype based on weights."""
    archetypes = list(LEARNER_ARCHETYPES.keys())
    weights = [LEARNER_ARCHETYPES[a]["weight"] for a in archetypes]
    return random.choices(archetypes, weights=weights, k=1)[0]


def generate_topic_mastery(student: SyntheticStudent, topics: list[dict]) -> dict:
    """
    Generate realistic topic mastery for a student.
    
    Mastery varies by:
    - Student's base mastery level
    - Topic difficulty
    - Random variation
    - Archetype-specific patterns
    """
    mastery = {}
    base = student.base_mastery

    for topic in topics:
        # Adjust by difficulty
        difficulty_penalty = {"beginner": 0.0, "intermediate": -0.10, "advanced": -0.20}
        adjusted = base + difficulty_penalty.get(topic["difficulty"], 0.0)

        # Add realistic noise
        noise = np.random.normal(0, 0.15)
        score = max(0.05, min(0.99, adjusted + noise))

        # Struggling learners have specific weak spots
        if student.archetype in ("struggling_learner", "at_risk_learner"):
            # Extra weakness on harder topics
            if topic["difficulty"] in ("intermediate", "advanced"):
                score *= 0.7

        # Inconsistent learners: some topics excellent, some poor
        if student.archetype == "inconsistent_learner":
            if random.random() < 0.3:
                score = max(0.8, score)  # Randomly excelling
            elif random.random() < 0.3:
                score = min(0.3, score)  # Randomly failing

        mastery[topic["title"]] = round(score, 3)

    return mastery


def generate_quiz_attempts(
    student: SyntheticStudent,
    topic: str,
    mastery: float,
    n_attempts: int = None,
) -> list[dict]:
    """Generate realistic quiz attempt records for a topic."""
    if n_attempts is None:
        # More attempts if student is struggling
        if mastery < 0.4:
            n_attempts = random.randint(3, 7)
        elif mastery < 0.7:
            n_attempts = random.randint(2, 4)
        else:
            n_attempts = random.randint(1, 3)

    attempts = []
    current_mastery = max(0.1, mastery - student.learning_rate * n_attempts)

    for attempt_num in range(1, n_attempts + 1):
        # Mastery improves over attempts (with noise)
        attempt_score = max(0.0, min(1.0, current_mastery + np.random.normal(0, 0.12)))
        n_questions = random.choice([5, 8, 10])
        correct = round(attempt_score * n_questions)

        # Time spent: struggling students spend more time
        base_time = n_questions * 90  # seconds
        if mastery < 0.4:
            time_factor = random.uniform(1.3, 2.0)
        else:
            time_factor = random.uniform(0.8, 1.2)
        time_spent = int(base_time * time_factor)

        # Generate individual answers
        answers = []
        for q_idx in range(n_questions):
            is_correct = random.random() < attempt_score
            q_time = random.randint(20, 180)
            hint_used = (not is_correct) and (random.random() < 0.4)
            answers.append({
                "question_idx": q_idx,
                "is_correct": is_correct,
                "time_seconds": q_time,
                "hint_used": hint_used,
                "attempt_number": attempt_num,
            })

        attempts.append({
            "attempt_number": attempt_num,
            "score": round(attempt_score, 3),
            "n_questions": n_questions,
            "correct_count": correct,
            "time_spent_seconds": time_spent,
            "topic": topic,
            "answers": answers,
            "days_ago": (n_attempts - attempt_num) * random.randint(1, 3),
        })

        # Mastery improves with each attempt
        current_mastery = min(0.99, current_mastery + student.learning_rate * random.uniform(0.5, 1.5))

    return attempts


def generate_student_events(student: SyntheticStudent, topics: list[dict]) -> list[dict]:
    """Generate resource view and session events."""
    events = []
    base_date = datetime.now() - timedelta(days=30)

    for day_offset in range(30):
        # Active days based on consistency
        if random.random() > student.consistency:
            continue

        date = base_date + timedelta(days=day_offset)
        session_topics = random.sample(topics, k=min(3, len(topics)))

        for topic in session_topics:
            mastery = student.topic_mastery.get(topic["title"], 0.5)

            # Resource views
            n_views = random.randint(1, 4)
            for _ in range(n_views):
                events.append({
                    "event_type": "resource_view",
                    "topic": topic["title"],
                    "duration_seconds": random.randint(120, 900),
                    "occurred_at": date.isoformat(),
                    "day_offset": day_offset,
                })

            # Video events (30% chance)
            if random.random() < 0.3:
                completion = min(1.0, mastery + random.uniform(0, 0.3))
                events.append({
                    "event_type": "video_started",
                    "topic": topic["title"],
                    "occurred_at": date.isoformat(),
                    "day_offset": day_offset,
                })
                if random.random() < completion:
                    events.append({
                        "event_type": "video_completed",
                        "topic": topic["title"],
                        "completion_rate": round(completion, 2),
                        "occurred_at": date.isoformat(),
                        "day_offset": day_offset,
                    })

    return events


def generate_synthetic_dataset(n_students: int = 50) -> dict:
    """
    Generate a complete synthetic dataset.
    
    Args:
        n_students: Number of synthetic students to generate
        
    Returns:
        Dictionary with students, courses, quiz attempts, and events
    """
    print(f"[SYNTHETIC DATA] Generating {n_students} synthetic students...")
    print("[SYNTHETIC DATA] ⚠️  This data is for DEMO/DEVELOPMENT only.")
    print("[SYNTHETIC DATA] Do NOT use for research conclusions.\n")

    course = DEMO_COURSES[0]
    topics = course["topics"]

    students = []
    all_quiz_attempts = []
    all_events = []

    for i in range(n_students):
        name = STUDENT_NAMES[i % len(STUDENT_NAMES)]
        archetype = select_archetype()
        arch = LEARNER_ARCHETYPES[archetype]

        student = SyntheticStudent(
            id=str(uuid.uuid4()),
            name=name,
            email=f"student_{i+1}@demo.edu",
            archetype=archetype,
            base_mastery=arch["base_mastery"] + np.random.normal(0, 0.08),
            learning_rate=arch["learning_rate"],
            consistency=arch["consistency"],
            engagement=arch["engagement"],
        )
        student.base_mastery = max(0.1, min(0.95, student.base_mastery))

        # Generate topic mastery
        student.topic_mastery = generate_topic_mastery(student, topics)

        # Generate quiz attempts per topic
        for topic in topics:
            mastery = student.topic_mastery[topic["title"]]
            attempts = generate_quiz_attempts(student, topic["title"], mastery)
            student.quiz_history.extend(attempts)
            for att in attempts:
                att["student_id"] = student.id
                att["student_name"] = student.name
                att["archetype"] = archetype
            all_quiz_attempts.extend(attempts)

        # Generate events
        student.events = generate_student_events(student, topics)
        for evt in student.events:
            evt["student_id"] = student.id
        all_events.extend(student.events)

        students.append(student)

    # Derived feature dataset for ML
    feature_records = []
    for student in students:
        for topic in topics:
            topic_name = topic["title"]
            mastery = student.topic_mastery[topic_name]
            topic_attempts = [a for a in student.quiz_history if a["topic"] == topic_name]

            if not topic_attempts:
                continue

            scores = [a["score"] for a in topic_attempts]
            recent_scores = scores[-3:] if len(scores) >= 3 else scores
            time_spent = [a["time_spent_seconds"] for a in topic_attempts]

            # Compute answers stats
            all_answers = []
            for att in topic_attempts:
                all_answers.extend(att.get("answers", []))

            correct_answers = [a for a in all_answers if a["is_correct"]]
            wrong_answers = [a for a in all_answers if not a["is_correct"]]
            hint_uses = [a for a in all_answers if a.get("hint_used")]

            record = {
                "student_id": student.id,
                "student_name": student.name,
                "archetype": student.archetype,
                "topic": topic_name,
                "difficulty": topic["difficulty"],

                # Target variable
                "mastery_score": mastery,
                "is_gap": 1 if mastery < 0.5 else 0,

                # Performance features
                "recent_accuracy": np.mean(recent_scores) if recent_scores else 0,
                "avg_accuracy": np.mean(scores) if scores else 0,
                "accuracy_trend": (recent_scores[-1] - recent_scores[0]) if len(recent_scores) > 1 else 0,
                "total_attempts": len(topic_attempts),

                # Time features
                "avg_time_per_attempt": np.mean(time_spent) if time_spent else 0,

                # Behavior features
                "hint_usage_rate": len(hint_uses) / max(len(all_answers), 1),
                "skip_rate": 0,  # simplified for synthetic data

                # Engagement
                "engagement_score": student.engagement,
                "consistency_score": student.consistency,
            }
            feature_records.append(record)

    dataset = {
        "metadata": {
            "type": "SYNTHETIC",
            "label": "DEMO — NOT FOR RESEARCH CONCLUSIONS",
            "generated_at": datetime.now().isoformat(),
            "seed": RANDOM_SEED,
            "n_students": n_students,
            "n_topics": len(topics),
            "n_quiz_attempts": len(all_quiz_attempts),
            "n_events": len(all_events),
        },
        "course": course,
        "students": [
            {
                "id": s.id,
                "name": s.name,
                "email": s.email,
                "archetype": s.archetype,
                "topic_mastery": s.topic_mastery,
            }
            for s in students
        ],
        "quiz_attempts": all_quiz_attempts,
        "events": all_events,
        "feature_records": feature_records,
    }

    return dataset


def save_dataset(dataset: dict, output_dir: str = "data/synthetic") -> None:
    """Save dataset to JSON files."""
    import os
    os.makedirs(output_dir, exist_ok=True)

    # Save full dataset
    with open(f"{output_dir}/dataset.json", "w") as f:
        json.dump(dataset, f, indent=2, default=str)

    # Save feature records as CSV-ready JSON
    with open(f"{output_dir}/features.json", "w") as f:
        json.dump(dataset["feature_records"], f, indent=2, default=str)

    print(f"[SYNTHETIC DATA] Dataset saved to {output_dir}/")
    print(f"[SYNTHETIC DATA] Students: {dataset['metadata']['n_students']}")
    print(f"[SYNTHETIC DATA] Quiz attempts: {dataset['metadata']['n_quiz_attempts']}")
    print(f"[SYNTHETIC DATA] Events: {dataset['metadata']['n_events']}")
    print(f"[SYNTHETIC DATA] Feature records: {len(dataset['feature_records'])}")


if __name__ == "__main__":
    dataset = generate_synthetic_dataset(n_students=50)
    save_dataset(dataset)
