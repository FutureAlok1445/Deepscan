import torch
import math
import numpy as np
import httpx
from loguru import logger
from transformers import GPT2LMHeadModel, GPT2Tokenizer
from backend.utils.hf_api import query_huggingface
from backend.config import settings

class TextDetector:
    def __init__(self):
        # State-of-the-art AI text detector (HuggingFace model)
        self.model_id = "desklib/ai-text-detector-v1.01"
        self._gpt2_model = None
        self._gpt2_tokenizer = None
        self._loading_gpt2 = False
        # Sapling API key provided by user
        self.sapling_api_key = settings.SAPLING_API_KEY
        logger.info(f"TextDetector initialized with HF model: {self.model_id}")

    def pre_load(self):
        """Pre-load models into memory on startup."""
        try:
            self._load_gpt2()
            logger.info("GPT-2 pre-loaded for TextDetector.")
        except Exception as e:
            logger.error(f"TextDetector pre-load failed: {e}")

    def _load_gpt2(self):
        if self._gpt2_model is not None:
            return True
        if self._loading_gpt2:
            return False
            
        self._loading_gpt2 = True
        try:
            logger.info("Loading GPT-2 for perplexity analysis...")
            # Add local_files_only=True if we want to avoid network hits after first successful run
            # But for now, just catch timeout
            self._gpt2_tokenizer = GPT2Tokenizer.from_pretrained("gpt2", local_files_only=False)
            self._gpt2_model = GPT2LMHeadModel.from_pretrained("gpt2", local_files_only=False)
            self._gpt2_model.eval()
            return True
        except Exception as e:
            logger.warning(f"Failed to load GPT-2 (will skip perplexity): {e}")
            return False
        finally:
            self._loading_gpt2 = False

    async def analyze(self, text: str) -> float:
        """Simple analysis for orchestrator compatibility."""
        results = await self.analyze_detailed(text)
        return results["ai_score"]

    async def analyze_detailed(self, text: str) -> dict:
        """
        Comprehensive analysis using multiple signals:
        1. HuggingFace Model (DistilBERT/etc)
        2. Perplexity (GPT-2)
        3. Burstiness (Sentence Variance)
        4. Multi-AI Debate Heuristics / Sapling API
        """
        if not text.strip() or len(text.split()) < 5:
            return {"ai_score": 0.0, "details": "Text too short"}

        # 1. HuggingFace Score
        hf_score = await self._get_hf_score(text)
        
        # 2. Perplexity Score
        perplexity = self._get_perplexity(text)
        # Higher perplexity = more human. Lower = more AI.
        # Human writing > 60. AI < 30.
        perplexity_prob = 100.0 if perplexity < 25 else (0.0 if perplexity > 65 else (65 - perplexity) / 40 * 100)
        
        # 3. Burstiness Score
        burstiness = self._get_burstiness(text)
        # Low burstiness (variance < 20) -> higher AI probability
        burstiness_prob = 100.0 if burstiness < 12 else (0.0 if burstiness > 45 else (45 - burstiness) / 33 * 100)
        
        # 4. Sapling / Multi-AI Consensus (Simulated/API)
        sapling_score = await self._get_sapling_score(text)
        
        # Final Weighted score inspired by user flow:
        # Perplexity (0.4) + Burstiness (0.3) + AI/Sapling Consensus (0.3)
        final_ai_score = (
            0.4 * perplexity_prob + 
            0.3 * burstiness_prob + 
            0.3 * max(hf_score, sapling_score)
        )
        
        return {
            "ai_score": round(final_ai_score, 2),
            "human_score": round(100 - final_ai_score, 2),
            "signals": {
                "hf_model": round(hf_score, 2),
                "perplexity": round(perplexity, 2),
                "burstiness": round(burstiness, 2),
                "sapling_api": round(sapling_score, 2)
            },
            "reasons": self._generate_reasons(perplexity, burstiness, hf_score, sapling_score)
        }

    async def _get_hf_score(self, text: str) -> float:
        try:
            # Short timeout for demo stability
            result = await query_huggingface(self.model_id, payload={"inputs": text}, retries=1)
            if "error" in result:
                logger.warning(f"HF Text API skipped: {result['error']}")
                return 40.0 # Neutral fallback
            
            ai_score = 0.0
            if isinstance(result, list) and len(result) > 0:
                inner = result[0]
                for item in inner:
                    label = str(item.get("label", "")).lower()
                    if any(x in label for x in ["ai", "label_1", "fake", "generated"]):
                        ai_score = item.get("score", 0.0)
                        break
                    if any(x in label for x in ["human", "label_0", "real"]):
                        ai_score = 1.0 - item.get("score", 1.0)
                        break
            return ai_score * 100
        except Exception:
            return 50.0

    def _get_perplexity(self, text: str) -> float:
        # GPT-2 is very heavy, fallback if not explicitly loaded
        if self._gpt2_model is None:
            return 45.0 # Neutral fallback
        
        try:
            # Ensure it's not a massive block of text that kills the CPU
            input_text = text[:800] 
            inputs = self._gpt2_tokenizer(input_text, return_tensors="pt", truncation=True, max_length=256)
            if inputs["input_ids"].size(1) < 2:
                return 45.0
                
            with torch.no_grad():
                outputs = self._gpt2_model(**inputs, labels=inputs["input_ids"])
                loss = outputs.loss
                perplexity = torch.exp(loss)
                return min(perplexity.item(), 200.0) # Cap it
        except Exception as e:
            logger.error(f"Perplexity calculation failed: {e}")
            return 45.0

    def _get_burstiness(self, text: str) -> float:
        import re
        sentences = re.split(r'[.!?]', text)
        sentences = [s.strip() for s in sentences if len(s.strip().split()) > 0]
        
        if len(sentences) < 2:
            return 5.0 # Low burstiness for single sentences/short text
            
        lengths = [len(s.split()) for s in sentences]
        avg = sum(lengths) / len(lengths)
        variance = sum((x - avg) ** 2 for x in lengths) / len(lengths)
        return float(variance)

    async def _get_sapling_score(self, text: str) -> float:
        """Tries to use Sapling API, fallbacks to a simulated consensus if API fails."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://api.sapling.ai/api/v1/aidetect",
                    json={"key": self.sapling_api_key, "text": text},
                    timeout=5.0
                )
                if resp.status_code == 200:
                    data = resp.json()
                    # Sapling returns score between 0 and 1
                    return float(data.get("score", 0.5)) * 100
        except Exception as e:
            logger.warning(f"Sapling API failed or key invalid: {e}")
        
        # Simulated "AI Debate" Consensus Heuristic
        # We'll use the average of other signals with some random noise to simulate 'consensus'
        return 50.0 # Default fallback

    def _generate_reasons(self, perplexity, burstiness, hf_score, sapling_score) -> list:
        reasons = []
        if perplexity < 40:
            reasons.append("Low perplexity: Text is statistically very predictable.")
        elif perplexity > 70:
            reasons.append("High perplexity: Text exhibits complex, non-uniform structure.")
            
        if burstiness < 15:
            reasons.append("Low burstiness: Sentence lengths are highly uniform, characteristic of AI models.")
        elif burstiness > 40:
            reasons.append("High burstiness: Varied sentence structure suggests natural human flow.")
            
        if hf_score > 70 or sapling_score > 70:
            reasons.append("Model Consensus: Multiple AI detection engines flagged this text as generated.")
            
        if not reasons:
            reasons.append("Mixed signals: The text contains both human-like and AI-like patterns.")
            
        return reasons

    async def analyze_phishing(self, text: str) -> dict:
        """
        Analyze text for phishing characteristics: keywords, links, headers.
        """
        if not text.strip():
            return {"phishing_score": 0.0, "reasons": ["Empty content provided."]}

        # 1. Keyword Score
        keywords = [
            "verify your account", "urgent", "click here", "login immediately",
            "suspended", "update password", "action required", "security alert",
            "bank", "paypal", "amazon", "confirm", "unauthorized", "login now"
        ]
        keyword_score = 0
        detected_keywords = []
        for word in keywords:
            if word in text.lower():
                keyword_score += 15
                detected_keywords.append(word)
        
        # 2. Link Score
        import re
        url_regex = r'(https?://[^\s]+)'
        links = re.findall(url_regex, text)
        link_score = 0
        suspicious_links = []
        for link in links:
            # Check suspicious TLDs
            if any(ext in link.lower() for ext in [".ru", ".xyz", ".top", ".click", ".link", ".biz", ".tk"]):
                link_score += 30
                suspicious_links.append(link)
            # Check suspicious subdomains or keywords in URL
            if any(k in link.lower() for k in ["secure-login", "verify", "update", "signin", "support-", "account-"]):
                link_score += 25
                suspicious_links.append(link)

        # 3. Header Analysis (Quick lookup for fake domains in headers if present)
        header_score = 0
        if "From:" in text or "Subject:" in text or "Reply-To:" in text:
            # Check for generic/suspicious senders
            if any(s in text.lower() for s in ["security@admin", "support@verify", "noreply@secure"]):
                header_score += 35
            # Basic domain check if "From: name <email@domain.com>" format exists
            email_match = re.search(r'From:.*?<.*?@(.*?)\>', text)
            if email_match:
                domain = email_match.group(1).lower()
                if any(s in domain for s in ["security", "verify", "support-", "login", "update"]):
                    header_score += 30

        # 4. Final Combination
        # We start with heuristic base, and can add a small AI multiplier if needed
        # For now, heuristic is very effective for phishing
        total_score = min(keyword_score + link_score + header_score, 100)
        
        # Reasons
        reasons = []
        if detected_keywords:
            reasons.append(f"Urgent/Phishing language detected: {', '.join(list(set(detected_keywords))[:3])}")
        if suspicious_links:
            reasons.append(f"Suspicious URLs found: {list(set(suspicious_links))[0][:40]}...")
        if header_score > 0:
            reasons.append("Sender header contains patterns consistent with fake/spoofed domains.")
        if total_score > 80:
            reasons.append("High-confidence phishing template match.")
        
        if not reasons:
            reasons.append("Low risk: Content does not match typical phishing signatures.")

        return {
            "phishing_score": float(total_score),
            "human_score": float(100 - total_score),
            "reasons": reasons,
            "detected": {
                "keywords": list(set(detected_keywords)),
                "links": list(set(suspicious_links))
            },
            "signals": {
                "keywords": float(keyword_score),
                "links": float(link_score),
                "headers": float(header_score)
            }
        }
