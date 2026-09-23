"""
Phase 2 EDA Notebook — Learning Analytics Exploratory Data Analysis.
This is a plain Python script that can be run as a Jupyter notebook via:
    jupytext --to notebook notebooks/phase2_learning_analytics_eda.py

Or convert to .ipynb with:
    py -3.12 -c "import json; ... "

IMPORTANT: All data used here is SYNTHETIC/DEMO.
           Do NOT draw research conclusions from this analysis.
"""

# %% [markdown]
# # Phase 2 — Learning Analytics: Exploratory Data Analysis
#
# **⚠️ IMPORTANT: All data is SYNTHETIC/DEMO. Not for research conclusions.**
#
# This notebook explores the synthetic student interaction dataset generated
# by `scripts/generate_synthetic_data.py`. It covers:
# 1. Dataset overview and basic statistics
# 2. Mastery score distributions by learner archetype
# 3. Performance feature correlations
# 4. Engagement patterns over time
# 5. At-risk student identification heuristics
#
# **No ML model is trained in this notebook.** This is pure exploratory analysis
# of descriptive statistics to validate the synthetic data structure.

# %%
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Optional visualisation (gracefully skip if not installed)
try:
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mtick
    HAS_MATPLOTLIB = True
    plt.style.use("seaborn-v0_8-darkgrid")
    FIGSIZE = (12, 5)
except ImportError:
    HAS_MATPLOTLIB = False
    print("matplotlib not installed — skipping plots. Run: pip install matplotlib")

# ── Load synthetic dataset ────────────────────────────────────────────────────
DATA_DIR = Path("../data/synthetic")
assert DATA_DIR.exists(), (
    f"Synthetic data not found at {DATA_DIR}. "
    "Run: py -3.12 scripts/generate_synthetic_data.py"
)

with open(DATA_DIR / "dataset.json", encoding="utf-8") as f:
    dataset = json.load(f)

# SYNTHETIC DATA DISCLAIMER
meta = dataset["metadata"]
print("=" * 60)
print(f"DATA TYPE : {meta['type']}")
print(f"LABEL     : {meta['label']}")
print(f"GENERATED : {meta['generated_at']}")
print(f"SEED      : {meta['seed']}")
print("=" * 60)

# %% [markdown]
# ## 1. Dataset Overview

# %%
print(f"\nSynthetic Dataset Summary")
print(f"  Students       : {meta['n_students']}")
print(f"  Topics         : {meta['n_topics']}")
print(f"  Quiz Attempts  : {meta['n_quiz_attempts']}")
print(f"  Events         : {meta['n_events']}")
print(f"  Feature Records: {meta['n_feature_records']}")

# Load into DataFrames
students_df = pd.DataFrame(dataset["students"])
features_df = pd.DataFrame(dataset["feature_records"])
attempts_df = pd.DataFrame(dataset["quiz_attempts"])
events_df   = pd.DataFrame(dataset["events"])

print(f"\nArchetype distribution:")
print(students_df["archetype"].value_counts().to_string())

# %% [markdown]
# ## 2. Mastery Score Distribution by Archetype

# %%
print("\nMastery Score by Archetype (SYNTHETIC DATA):")
archetype_mastery = features_df.groupby("archetype")["mastery_score"].agg(
    ["mean", "std", "min", "max"]
).round(3)
print(archetype_mastery.to_string())

if HAS_MATPLOTLIB:
    fig, axes = plt.subplots(1, 2, figsize=FIGSIZE)

    # Box plot
    archetypes = features_df["archetype"].unique()
    data_by_arch = [
        features_df[features_df["archetype"] == a]["mastery_score"].values
        for a in archetypes
    ]
    axes[0].boxplot(data_by_arch, labels=[a.replace("_learner", "") for a in archetypes], vert=True)
    axes[0].set_title("Mastery Score by Archetype\n[SYNTHETIC DATA — NOT FOR RESEARCH]")
    axes[0].set_ylabel("Mastery Score (0–1)")
    axes[0].set_ylim(0, 1.05)
    axes[0].tick_params(axis="x", rotation=30)

    # Overall distribution
    axes[1].hist(features_df["mastery_score"], bins=20, edgecolor="black", color="steelblue")
    axes[1].axvline(0.35, color="red", linestyle="--", label="Beginner threshold (0.35)")
    axes[1].axvline(0.65, color="orange", linestyle="--", label="Intermediate threshold (0.65)")
    axes[1].axvline(0.85, color="green", linestyle="--", label="Mastered threshold (0.85)")
    axes[1].set_title("Overall Mastery Distribution\n[SYNTHETIC DATA]")
    axes[1].set_xlabel("Mastery Score")
    axes[1].set_ylabel("Count")
    axes[1].legend(fontsize=8)

    plt.tight_layout()
    plt.savefig(DATA_DIR / "mastery_distribution.png", dpi=100, bbox_inches="tight")
    print("Plot saved: data/synthetic/mastery_distribution.png")
    plt.show()

# %% [markdown]
# ## 3. Performance Feature Correlations

# %%
print("\nPerformance Feature Correlations with Mastery Score (SYNTHETIC DATA):")
numeric_cols = [
    "mastery_score", "recent_accuracy", "avg_accuracy",
    "accuracy_trend", "total_attempts", "hint_usage_rate",
    "avg_time_per_attempt", "engagement_score", "consistency_score",
]
corr = features_df[numeric_cols].corr()["mastery_score"].drop("mastery_score").round(3)
print(corr.sort_values(ascending=False).to_string())

print("\nNote: Correlations are expected here because the synthetic data generator")
print("uses mastery score to simulate quiz performance. This does NOT validate")
print("any research hypothesis about real student learning.")

# %% [markdown]
# ## 4. At-Risk Student Analysis (HEURISTIC — NOT RESEARCH VALIDATED)

# %%
print("\nAt-Risk Student Analysis (SYNTHETIC DATA — HEURISTIC ONLY):")

# At-risk: mastery < 0.35 AND engagement < 0.50
student_agg = features_df.groupby("student_id").agg(
    overall_mastery=("mastery_score", "mean"),
    avg_engagement=("engagement_score", "mean"),
    topics_below_threshold=("is_gap", "sum"),
).reset_index()

at_risk = student_agg[
    (student_agg["overall_mastery"] < 0.35) |
    (student_agg["avg_engagement"] < 0.50)
]
print(f"  Total students        : {len(student_agg)}")
print(f"  At-risk (heuristic)   : {len(at_risk)}")
print(f"  At-risk %             : {100*len(at_risk)/len(student_agg):.1f}%")

# Archetype of at-risk students
at_risk_with_arch = at_risk.merge(
    students_df[["id", "archetype"]], left_on="student_id", right_on="id"
)
if not at_risk_with_arch.empty:
    print("\nAt-risk breakdown by archetype:")
    print(at_risk_with_arch["archetype"].value_counts().to_string())

# %% [markdown]
# ## 5. Topic Difficulty Analysis

# %%
print("\nAverage Mastery by Topic and Difficulty (SYNTHETIC DATA):")
topic_analysis = features_df.groupby(["topic", "difficulty"]).agg(
    mean_mastery=("mastery_score", "mean"),
    mean_accuracy=("avg_accuracy", "mean"),
    total_attempts=("total_attempts", "sum"),
    gap_count=("is_gap", "sum"),
).round(3).sort_values("mean_mastery")

print(topic_analysis.to_string())

# %% [markdown]
# ## 6. Event Activity Summary

# %%
print("\nEvent Type Distribution (SYNTHETIC DATA):")
print(events_df["event_type"].value_counts().to_string())

print("\nEvents per student (top 5 / bottom 5):")
events_per_student = events_df.groupby("student_id").size().reset_index(name="event_count")
events_per_student = events_per_student.sort_values("event_count", ascending=False)
print("  High activity:", events_per_student.head()["event_count"].values)
print("  Low activity: ", events_per_student.tail()["event_count"].values)

# %% [markdown]
# ## Summary
#
# This EDA confirms that the synthetic data generator produces:
# - Realistic mastery distributions differentiated by archetype
# - Correlated performance features (as designed by the generator)
# - Identifiable at-risk students based on engagement and mastery heuristics
#
# **The next step (Phase 3)** is to:
# - Train adaptive recommendation models on real (non-synthetic) interaction data
# - Validate knowledge gap detection against teacher-labeled records
# - Integrate the LLM tutor with personalized context from the learner profile

print("\n[EDA COMPLETE]")
print(f"All results are based on SYNTHETIC data: {meta['label']}")
print("Do not cite or use these statistics in research publications.")
