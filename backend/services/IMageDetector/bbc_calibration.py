"""
BBC AI Detection Dataset — Reference Statistics Module
=======================================================
Source: BBC AI Content Analysis Dataset (n=1,215 articles)
Repo:   https://github.com/isfakeai/bbc-ai-content-analysis

This module contains calibration constants derived from the BBC dataset analysis.
All DeepScan detection thresholds reference these empirical values.

Dataset Overview
----------------
- Total articles: 1,215
- Detector models in dataset: GLM (520), Human (575), GPT-3/4 (73), OPT (41), Flan-T5 (6)
- ai_prob range: 0.104 – 0.977
- ai_prob mean: 0.688

Calibration Thresholds (ai_prob percentiles)
--------------------------------------------
10th  pct: 0.433
25th  pct: 0.610  <- Authentic boundary (mapped to 39 on 0-100 scale)
50th  pct: 0.721  <- Dataset median
75th  pct: 0.809  <- Uncertain/Likely Fake boundary (mapped to 61)
90th  pct: 0.868  <- Likely Fake/Definitely Fake boundary (mapped to 81)
99th  pct: 0.949

Model Averages
--------------
GLM (AI-generated):   avg_ai_prob = 0.795  (72% of articles >= 0.75)
GPT-3/4 (AI):         avg_ai_prob = 0.819  (86% of articles >= 0.75)
Human-authored:       avg_ai_prob = 0.565  ( 7% of articles >= 0.75)

Word Count Correlation
-----------------------
Short articles (<400 words):  avg_ai_prob = 0.733  (38% higher than long-form)
Long articles (>1000 words):  avg_ai_prob = 0.531  (substantially lower AI probability)
Overall avg word count:       756 words per article

Key Findings Applied in DeepScan
---------------------------------
1. VERDICT THRESHOLDS calibrated from BBC population percentiles.
2. FUSION WEIGHTS: MAS raised to 42% (pixel forensics most discriminative).
3. SEMANTIC LAYER: Short captions (<80 words) receive elevated AI-risk score.
4. KEYWORD PATTERNS: GLM-style AI content clusters around financial briefs and policy news.
5. HUMAN AUTHORSHIP MARKERS: Hedging language, long philosophical prose correlate with Human-authored content.
"""

# Calibrated thresholds for verdict bucketing (0-100 deepfake certainty scale)
THRESHOLD_AUTHENTIC      = 39   # ai_prob < 0.610 (bottom 25th percentile)
THRESHOLD_UNCERTAIN      = 61   # ai_prob 0.610-0.809 (interquartile range)
THRESHOLD_LIKELY_FAKE    = 81   # ai_prob 0.809-0.868 (75th-90th percentile)
# Above 81 = Definitely Fake (top 10%, ai_prob > 0.868)

# Population statistics
DATASET_MEAN_AI_PROB     = 0.688
DATASET_MEDIAN_AI_PROB   = 0.721
DATASET_SIZE             = 1215

# Word count signal
SHORT_ARTICLE_THRESHOLD  = 400     # words; avg_ai_prob = 0.733
LONG_ARTICLE_THRESHOLD   = 1000    # words; avg_ai_prob = 0.531
SHORT_CONTENT_AI_RISK_BOOST = 0.38 # % factor: short content is 38% more AI-like

# Model-specific averages
MODEL_AVG_PROBS = {
    "GLM":      0.795,
    "GPT-3/4":  0.819,
    "Human":    0.565,
    "OPT":      0.796,
    "Flan-T5":  0.767,
}
