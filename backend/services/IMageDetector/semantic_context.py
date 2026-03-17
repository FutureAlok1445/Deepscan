from loguru import logger
import re
from PIL import Image

try:
    from transformers import pipeline
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    logger.warning("transformers not installed — Semantic Context will use heuristics")

# BBC Dataset-derived keyword analysis:
# High-scoring AI articles (ai_prob >= 0.9) frequently covered: financial/market news,
# govt/AI policy, short factual briefs. Low-scoring articles (human, ai_prob <= 0.2):
# long-form investigative, historical, philosophical, and sci-fi commentary.

# GLM-tagged (AI-written) articles avg 0.795 vs Human 0.565.
# Key distinguishing phrases from GLM-labeled BBC articles appear in certain topic clusters.
BBC_AI_CONTENT_PATTERNS = [
    # Financial / market brevity (high GLM correlation)
    r'\binvestment\b', r'\bshares\b', r'\bstock\b', r'\bmarket\b',
    # AI policy / government briefings (high GLM correlation)  
    r'\bai summit\b', r'\bregulat\w+\b', r'\borgani[sz]\b',
    # Promotional / scam patterns (universal)
    r'\burgent\b', r'\bsend money\b', r'\bgiveaway\b', r'\bclick here\b',
    r'\binvest now\b', r'\bcrypto\b', r'\bfree\b', r'\bbreaking\b',
    # Deepfake-specific language anomalies
    r'\bcompletely accurate\b', r'\baccording to sources\b', r'\bexperts say\b',
    r'\bas expected\b', r'\bit is worth noting that\b',
]

# Human-authored texts (bbc low-scoring): philosophical, metaphorical, sci-fi, long-form
HUMAN_AUTHORSHIP_PATTERNS = [
    r'\bin a way\b', r'\bone might argue\b', r'\bit is hard to say\b',
    r'\bcurious\b', r'\bfascinating\b', r'\bironically\b', r'\bparadox\b',
]

class SemanticContextAnalyzer:
    """
    Layer 7: Understands contextual consistency.
    Upgraded with BBC AI Detection Dataset (n=1,215) insights:
    
    BBC Key Findings Applied:
    1. Short content (<400 words) averages ai_prob=0.733 vs 0.531 for long (>1000 words).
       -> Short captions/descriptions carry higher AI-generation risk.
    2. GLM-type AI articles average 0.795 probability; human-tagged average 0.565.
    3. High-scoring AI content clusters around financial briefs, policy summaries.
    4. Human-authored content has distinctive hedging language and longer prose.
    
    Provides Intent & Reasoning Score (IRS).
    """
    def __init__(self):
        self.intent_analyzer = None
        self.clip_image_analyzer = None

    async def load_model(self):
        if not HAS_TRANSFORMERS:
            logger.warning("Transformers not installed! SemanticContext relying on regex heuristics.")
            return
        # Disk-space guard: skip model download if less than 500MB free
        try:
            import shutil
            free_mb = shutil.disk_usage("/").free / (1024 ** 2)
            if free_mb < 500:
                logger.warning(f"Only {free_mb:.0f} MB free disk — skipping HuggingFace model download. Using heuristics only.")
                return
        except Exception:
            pass
        try:
            # Replaced facebook/bart-large-mnli (1.6GB) with lightweight DistilBERT-MNLI (~260MB)
            self.intent_analyzer = pipeline(
                "zero-shot-classification",
                model="typeform/distilbert-base-uncased-mnli",
            )
            self.clip_image_analyzer = pipeline(
                "zero-shot-image-classification",
                model="openai/clip-vit-base-patch32"
            )
            logger.info("SemanticContext lightweight DistilBERT-MNLI + CLIP loaded.")
        except Exception as e:
            logger.error(f"Failed to load semantic models: {e}")

    def _apply_bbc_heuristics(self, caption: str) -> tuple[float, list]:
        """
        Apply BBC-dataset-derived heuristic scoring to the caption/context.
        Returns (irs_adjustment, detail_messages).
        """
        adjustment = 0.0
        details = []

        if not caption:
            return 0.0, []

        caption_lower = caption.lower()
        word_count = len(caption.split())

        # --- BBC Finding 1: Short captions carry higher AI-generation risk ---
        # Short (<400 words) BBC articles averaged 0.733 ai_prob vs 0.531 for long (>1000 words)
        if word_count < 30:
            adjustment -= 8.0
            details.append(f"Very short caption ({word_count} words). BBC data: short content has 38% higher AI probability than long-form content.")
        elif word_count < 80:
            adjustment -= 4.0
            details.append(f"Short caption ({word_count} words). Slightly elevated AI-generation risk per BBC dataset correlation.")

        # --- BBC Finding 2: Check for AI-content language patterns ---
        ai_keyword_hits = sum(1 for pat in BBC_AI_CONTENT_PATTERNS
                              if re.search(pat, caption_lower))
        if ai_keyword_hits >= 3:
            adjustment -= 15.0
            details.append(f"Caption matches {ai_keyword_hits} AI-content keyword patterns from BBC analysis.")
        elif ai_keyword_hits >= 1:
            adjustment -= 6.0
            details.append(f"Caption contains {ai_keyword_hits} AI-associated language pattern(s).")

        # --- BBC Finding 3: Human authorship markers reduce risk ---
        human_hits = sum(1 for pat in HUMAN_AUTHORSHIP_PATTERNS
                         if re.search(pat, caption_lower))
        if human_hits >= 2:
            adjustment += 10.0
            details.append(f"Caption shows {human_hits} human-authorship markers (hedging language, philosophical tone).")

        # --- Original: Scam/urgency keywords ---
        scam_patterns = [r'\bsend money\b', r'\bgiveaway\b', r'\bclick here\b',
                         r'\binvest now\b', r'\bcrypto wallet\b']
        scam_hits = sum(1 for p in scam_patterns if re.search(p, caption_lower))
        if scam_hits > 0:
            adjustment -= min(40.0, scam_hits * 20.0)
            details.append(f"Scam/promotional urgency keywords detected ({scam_hits} match(es)).")

        return adjustment, details

    def analyze(self, image_path: str, caption: str) -> dict:
        result = {
            "score_irs": 100.0,
            "details": []
        }

        # Apply BBC-derived heuristics
        heuristic_adj, heuristic_details = self._apply_bbc_heuristics(caption)
        result["score_irs"] += heuristic_adj
        result["details"].extend(heuristic_details)

        if not HAS_TRANSFORMERS or not self.intent_analyzer or not self.clip_image_analyzer:
            result["details"].append("NLP/Vision semantic models unavailable. Using BBC-calibrated heuristic approach.")
            result["score_irs"] = max(0.0, min(100.0, result["score_irs"]))
            return result

        try:
            image = Image.open(image_path).convert('RGB')

            if caption and caption.strip():
                # Analyze caption intent using NLP (zero-shot)
                intent_labels = [
                    "scam or promotion",
                    "political propaganda",
                    "tragedy or negative event",
                    "celebration or positive news",
                    "factual news report"      # <-- added per BBC findings
                ]
                intent_res = self.intent_analyzer(caption, candidate_labels=intent_labels)
                top_intent = intent_res['labels'][0]
                top_score = intent_res['scores'][0]

                if top_intent in ["scam or promotion", "political propaganda"] and top_score > 0.5:
                    result["score_irs"] -= 30.0
                    result["details"].append(f"Caption classified as high-risk narrative ({top_intent}, confidence={top_score:.0%}).")

                # CLIP: verify image visually matches the caption's vibe
                clip_labels = ["smiling person", "crying person", "crowd event", "scary scene", "peaceful scene"]
                clip_res = self.clip_image_analyzer(image, candidate_labels=clip_labels)
                top_clip_label = clip_res[0]['label']

                # Context contradiction rule
                if top_intent == "tragedy or negative event" and top_clip_label == "smiling person":
                    result["score_irs"] -= 40.0
                    result["details"].append("Severe Context Contradiction: Negative caption but image depicts smiling/celebration.")

                # Factual news pattern (BBC finding: very short factual briefs are GLM-like)
                if top_intent == "factual news report" and top_score > 0.7:
                    result["details"].append("Caption classified as factual news report — consistent with BBC AI-generated content patterns.")

            else:
                # No caption: use CLIP to check if image itself looks synthetic
                clip_labels = ["ai generated image", "real photograph", "painting", "heavily edited photo"]
                clip_res = self.clip_image_analyzer(image, candidate_labels=clip_labels)
                for res in clip_res:
                    if res['label'] == "ai generated image" and res['score'] > 0.5:
                        result["score_irs"] -= 20.0
                        result["details"].append(f"CLIP zero-shot classified scene as synthetic/AI-generated ({res['score']:.0%} confidence).")
                        break

        except Exception as e:
            logger.error(f"Error in semantic analysis: {e}")
            result["score_irs"] = 90.0

        result["score_irs"] = max(0.0, min(100.0, result["score_irs"]))
        return result


semantic_analyzer = SemanticContextAnalyzer()
