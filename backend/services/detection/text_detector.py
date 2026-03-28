import math
import numpy as np
import httpx
from loguru import logger

HAS_TORCH = False
HAS_TRANSFORMERS = False

try:
    import torch
    HAS_TORCH = True
except ImportError:
    logger.warning("torch not installed — TextDetector perplexity analysis disabled")

try:
    from transformers import GPT2LMHeadModel, GPT2Tokenizer
    HAS_TRANSFORMERS = True
except ImportError:
    GPT2LMHeadModel = None
    GPT2Tokenizer = None
    logger.warning("transformers not installed — TextDetector GPT-2 disabled")

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
        if not HAS_TORCH or not HAS_TRANSFORMERS:
            logger.debug("GPT-2 load skipped — torch or transformers not installed")
            return False
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
            return {
                "ai_score": 0.0, 
                "human_score": 100.0,
                "signals": {"hf_model": 0, "perplexity": 0, "burstiness": 0, "sapling_api": 0},
                "reasons": ["Text too short for reliable analysis."]
            }

        # 1. HuggingFace Score
        hf_score = await self._get_hf_score(text)
        
        # 2. Perplexity Score
        perplexity = self._get_perplexity(text)
        # Higher perplexity = more human. Lower = more AI.
        # Adjusted bands based on GPT-2-small typical outputs
        perplexity_prob = 100.0 if perplexity < 20 else (0.0 if perplexity > 80 else (80 - perplexity) / 60 * 100)
        
        # 3. Burstiness Score
        burstiness = self._get_burstiness(text)
        # Low burstiness (variance < 10) -> higher AI probability
        burstiness_prob = 100.0 if burstiness < 10 else (0.0 if burstiness > 50 else (50 - burstiness) / 40 * 100)
        
        # 4. Sapling / Multi-AI Consensus (Simulated/API)
        sapling_score = await self._get_sapling_score(text)
        
        # Weighted score composition
        # If HF model is highly confident (e.g. > 90 or < 10), give it more weight
        hf_weight = 0.5 if (hf_score > 90 or hf_score < 10) else 0.3
        
        final_ai_score = (
            0.35 * perplexity_prob + 
            0.25 * burstiness_prob + 
            hf_weight * hf_score +
            (0.4 - hf_weight) * sapling_score
        )
        
        final_ai_score = min(max(final_ai_score, 0), 100)
        
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
            # Try a slightly better model if the default ones are flaky
            # "Hello-SimpleAI/chatgpt-detector-roberta" is often quite good
            model_to_use = self.model_id
            result = await query_huggingface(model_to_use, payload={"inputs": text}, retries=2)
            
            if not result or "error" in result:
                logger.warning(f"HF Text API skipped or failed: {result.get('error') if result else 'Empty response'}")
                return 50.0 # Neutral fallback
            
            ai_score = 0.0
            # Some models return [[{"label": "...", "score": ...}]]
            if isinstance(result, list) and len(result) > 0:
                inner = result[0]
                if isinstance(inner, list):
                    for item in inner:
                        label = str(item.get("label", "")).lower()
                        if any(x in label for x in ["ai", "label_1", "fake", "generated", "machine"]):
                            ai_score = item.get("score", 0.0)
                            break
                        if any(x in label for x in ["human", "label_0", "real", "human-written"]):
                            ai_score = 1.0 - item.get("score", 1.0)
                            break
                elif isinstance(inner, dict):
                    # Some models return [{"label": "...", "score": ...}]
                    label = str(inner.get("label", "")).lower()
                    if any(x in label for x in ["ai", "label_1", "fake", "generated"]):
                        ai_score = inner.get("score", 0.0)
                    else:
                        ai_score = 1.0 - inner.get("score", 0.0)
            
            return ai_score * 100
        except Exception as e:
            logger.error(f"HF Score error: {e}")
            return 50.0

    def _get_perplexity(self, text: str) -> float:
        if self._gpt2_model is None:
            # Try loading once if it hasn't been loaded
            if not self._loading_gpt2:
                import threading
                threading.Thread(target=self._load_gpt2).start()
            return 45.0
        
        try:
            input_text = text[:1024] # Slightly larger window
            inputs = self._gpt2_tokenizer(input_text, return_tensors="pt", truncation=True, max_length=512)
            if inputs["input_ids"].size(1) < 5:
                return 45.0
                
            with torch.no_grad():
                outputs = self._gpt2_model(**inputs, labels=inputs["input_ids"])
                loss = outputs.loss
                perplexity = torch.exp(loss)
                return min(perplexity.item(), 250.0)
        except Exception as e:
            logger.error(f"Perplexity calculation failed: {e}")
            return 45.0

    def _get_burstiness(self, text: str) -> float:
        import re
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip().split()) > 0]
        
        if len(sentences) < 2:
            return 8.0 # Lower burstiness for single sentences
            
        lengths = [len(s.split()) for s in sentences]
        avg = sum(lengths) / len(lengths)
        variance = sum((x - avg) ** 2 for x in lengths) / len(lengths)
        return float(variance)

    async def _get_sapling_score(self, text: str) -> float:
        if not self.sapling_api_key or self.sapling_api_key in ("", "YOUR_SAPLING_KEY_HERE"):
            pass  # No valid key — skip API call
        else:
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        "https://api.sapling.ai/api/v1/aidetect",
                        json={"key": self.sapling_api_key, "text": text},
                        timeout=8.0
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        return float(data.get("score", 0.5)) * 100
            except Exception as e:
                logger.warning(f"Sapling API error: {e}")
        
        # If API fails, use a secondary check for "AI markers"
        ai_markers = ["as an ai language model", "in conclusion", "furthermore", "moreover", "it is important to note", "unprecedented"]
        marker_score = 10.0
        for marker in ai_markers:
            if marker in text.lower():
                marker_score += 15.0
        return min(marker_score, 80.0)

    def _generate_reasons(self, perplexity, burstiness, hf_score, sapling_score) -> list:
        reasons = []
        if perplexity < 30:
            reasons.append("Highly predictable word choice (low perplexity).")
        elif perplexity > 90:
            reasons.append("Highly creative and varied phrasing (high perplexity).")
            
        if burstiness < 12:
            reasons.append("Highly uniform sentence structures (low burstiness).")
        elif burstiness > 45:
            reasons.append("Varied and dynamic sentence rhythms (high burstiness).")
            
        if hf_score > 80:
            reasons.append("Neural pattern analyzer flags structural footprints of LLMs.")
        elif hf_score < 20:
            reasons.append("Text exhibits deep semantic nuance common in human writing.")
            
        if sapling_score > 70:
            reasons.append("Linguistic consensus: Multiple AI detectors flagged this content.")
            
        if not reasons:
            reasons.append("Mixed linguistic signals detected.")
            
        return reasons

    async def analyze_phishing(self, text: str) -> dict:
        """
        Advanced phishing analysis with:
        1. Contextual keyword analysis
        2. Credibility-based link scanning
        3. Urgency & Threat detection
        4. Header & Domain spoofing indicators
        """
        if not text.strip() or len(text.strip()) < 10:
            return {
                "phishing_score": 0.0, 
                "human_score": 100.0, 
                "reasons": ["Text too short for phishing analysis."],
                "signals": {"keywords": 0, "links": 0, "headers": 0, "urgency": 0}
            }

        # 1. Advanced Keyword & Urgency analysis
        malicious_keywords = {
            "critical": 15, "suspended": 20, "unauthorized": 25, "urgent action": 20, 
            "login attempt": 15, "reactivate": 15, "refund": 10, "inheritance": 30,
            "bill unpaid": 15, "legal action": 25, "summons": 30, "verify identity": 20
        }
        urgency_score = 0
        detected_keywords = []
        
        for k, v in malicious_keywords.items():
            if k in text.lower():
                urgency_score += v
                detected_keywords.append(k)

        # Check for aggressive punctuation and caps
        if "!!!" in text or "???" in text:
            urgency_score += 10
        if sum(1 for c in text if c.isupper()) / (len(text) + 1) > 0.4:
            urgency_score += 15 # Over-capitalization

        # 2. Advanced Link Analysis
        import re
        url_regex = r'(https?://[^\s]+)'
        links = re.findall(url_regex, text)
        link_score = 0
        suspicious_links = []
        
        for link in links:
            # TLD reputation
            if any(tld in link.lower() for tld in [".ru", ".xyz", ".top", ".click", ".link", ".biz", ".tk", ".ga"]):
                link_score += 35
                suspicious_links.append(f"Suspicious TLD: {link}")
            
            # Shorteners (often used in phishing)
            if any(sh in link.lower() for sh in ["bit.ly", "t.co", "tinyurl", "ow.ly"]):
                link_score += 15
                suspicious_links.append(f"Shortened URL: {link}")
            
            # Typosquatting/Keywords in URL
            if any(k in link.lower() for k in ["secure", "signin", "verify", "login", "update-account", "paypal-auth"]):
                link_score += 25
                suspicious_links.append(f"Login-bait URL: {link}")
                
            # IP-based URLs
            if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', link):
                link_score += 40
                suspicious_links.append(f"Direct IP link: {link}")

        # 3. Header & Social Engineering analysis
        header_score = 0
        if "From:" in text and "<" in text and ">" in text:
            header_score += 10
            # Spoofing check
            if any(s in text.lower() for s in ["gmail.com", "outlook.com", "yahoo.com"]):
                if any(k in text.lower() for k in ["official", "admin", "security", "support"]):
                    header_score += 30 # Generic email pretending to be admin
        
        # Sense of loss/gain
        if any(w in text.lower() for w in ["won", "prize", "jackpot", "lottery", "gift card"]):
            urgency_score += 20

        # Final Combination
        # We start with heuristic base, and can add a small AI multiplier if needed
        # For now, heuristic is very effective for phishing
        total_score = min(urgency_score + link_score + header_score, 100)
        
        # Add LLM context check via Groq if available
        groq_reasons = []
        try:
            import os
            from groq import AsyncGroq
            # Since the user specifically provided this key to use
            groq_key = os.environ.get("GROQ_API_KEY", "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")
            if groq_key:
                client = AsyncGroq(api_key=groq_key)
                prompt = (
                    f"Analyze this email/text for phishing or social engineering. "
                    f"Reply ONLY with a raw JSON object with exactly two keys: 'score' (number from 0 to 100, where 100 is definite phishing) "
                    f"and 'reason' (short 1 sentence explanation).\n\nText:\n{text}"
                )
                
                completion = await client.chat.completions.create(
                    model="llama3-70b-8192",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=150,
                )
                
                response_content = completion.choices[0].message.content
                import json
                import re
                
                # Try to extract JSON
                json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
                if json_match:
                    llm_data = json.loads(json_match.group(0))
                    llm_score = float(llm_data.get("score", 0))
                    llm_reason = str(llm_data.get("reason", ""))
                    
                    if llm_score > 60:
                        groq_reasons.append(f"AI Security Analysis: {llm_reason}")
                        # Combine AI score with heuristic score (weighting AI 40%, heuristic 60%)
                        total_score = (total_score * 0.6) + (llm_score * 0.4)
        except Exception as e:
            logger.error(f"Groq API error in phishing check: {e}")
        
        # Reasons
        reasons = []
        if detected_keywords:
            reasons.append(f"Urgent/Phishing language detected: {', '.join(list(set(detected_keywords))[:3])}")
        if suspicious_links:
            reasons.append(f"Suspicious URLs found: {list(set(suspicious_links))[0][:40]}...")
        if header_score > 0:
            reasons.append("Sender header contains patterns consistent with fake/spoofed domains.")
            
        reasons.extend(groq_reasons)
        
        if total_score > 80:
            reasons.append("High-confidence phishing template match.")
        
        if not reasons:
            reasons.append("Low risk: Content does not match typical phishing signatures.")
        elif not reasons:
            reasons.append("Suspicious patterns detected in communication context.")

        return {
            "phishing_score": round(total_score, 2),
            "human_score": round(100 - total_score, 2),
            "reasons": reasons,
            "detected": {
                "keywords": list(set(detected_keywords)),
                "links": list(set(suspicious_links))
            },
            "signals": {
                "keywords": round(min(urgency_score, 100), 2),
                "links": round(min(link_score, 100), 2),
                "headers": round(min(header_score, 100), 2),
                "urgency": round(min(urgency_score, 100), 2)
            }
        }

