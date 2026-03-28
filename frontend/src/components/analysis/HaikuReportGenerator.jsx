import React, { useState, useEffect } from 'react';
import BrutalCard from '../ui/BrutalCard';
import { Loader2, Sparkles } from 'lucide-react';

export default function HaikuReportGenerator({ imageFile, sysScore }) {
  const [reportText, setReportText] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!imageFile) return;

    const generateReport = async () => {
      setLoading(true);
      try {
        const toBase64 = (f) => new Promise((res, rej) => {
          const reader = new FileReader();
          reader.readAsDataURL(f);
          reader.onload = () => res(reader.result.split(',')[1]);
          reader.onerror = rej;
        });

        const base64 = await toBase64(imageFile);

        const prompt = `You are an expert deepfake forensic analyst. Based strictly on the visual evidence in the image provided and the overall backend system score of ${sysScore}%, write a highly detailed diagnostic report matching THIS EXACT template structure. Do not output markdown code blocks, just raw formatted text.

Detection Report
Image Type: [Determine if it is an Art/Creative Image, Photograph, or Digital Composite]

Overall Forgery Score: ${sysScore}%

Analysis Summary
[Write a comprehensive 3-4 sentence paragraph evaluating the image authenticity. Reference specific visual artifacts such as lighting, skin texture, symmetry, or blending.]

Detailed Breakdown
[Feature Name 1] | [Assign 0-100%] [(Include WARNING here if score > 50%)]
[Provide 1 sentence of concrete visual observation explaining this specific score.]

[Feature Name 2] | [Assign 0-100%] [(Include WARNING here if score > 50%)]
[Provide 1 sentence of concrete visual observation explaining this specific score.]

[Feature Name 3] | [Assign 0-100%] [(Include WARNING here if score > 50%)]
[Provide 1 sentence of concrete visual observation explaining this specific score.]

[Feature Name 4] | [Assign 0-100%] [(Include WARNING here if score > 50%)]
[Provide 1 sentence of concrete visual observation explaining this specific score.]

[Feature Name 5] | [Assign 0-100%] [(Include WARNING here if score > 50%)]
[Provide 1 sentence of concrete visual observation explaining this specific score.]`;

        let tries = 0;
        while (!window.puter?.ai?.chat && tries < 20) {
            await new Promise(r => setTimeout(r, 200));
            tries++;
        }

        if (!window.puter?.ai?.chat) {
            setReportText("Failed to initialize Puter.js AI. Ensure you are connected to the network.");
            setLoading(false);
            return;
        }

        let res;
        try {
            res = await window.puter.ai.chat(
                [{
                    role: 'user', content: [
                        { type: 'image_url', image_url: { url: `data:${imageFile.type || 'image/jpeg'};base64,${base64}` } },
                        { type: 'text', text: prompt }
                    ]
                }],
                { model: 'claude-3-haiku' }
            );
        } catch (initialErr) {
            console.warn("Puter rejected claude-3-haiku, falling back to Sonnet/Gemini implicitly:", initialErr);
            // Fallback for Puter wrapper limitations on model names
            res = await window.puter.ai.chat(
                [{
                    role: 'user', content: [
                        { type: 'image_url', image_url: { url: `data:${imageFile.type || 'image/jpeg'};base64,${base64}` } },
                        { type: 'text', text: prompt }
                    ]
                }],
                { model: 'claude-sonnet-4-5' }
            );
        }

        let text = res?.message?.content || res || 'Analysis Failed to generate.';
        setReportText(text.trim());

      } catch (e) {
        console.error("Haiku generation failed", e);
        setReportText(`Haiku Agent encountered an error processing the image.\nError details: ${e?.message || e}`);
      } finally {
        setLoading(false);
      }
    };

    generateReport();
  }, [imageFile, sysScore]);

  if (!imageFile) return null;

  return (
    <BrutalCard className="!p-3 sm:!p-6 bg-ds-silver/5 border-l-4 sm:border-l-8 border-l-[#ffbbee]">
      <h3 className="font-grotesk font-black text-ds-silver text-base sm:text-xl uppercase tracking-wider sm:tracking-widest mb-3 sm:mb-4 flex items-center gap-2">
        <Sparkles className="text-[#ffbbee] w-5 h-5" /> 
        <span className="text-[#ffbbee]">Real-Time Haiku Analysis</span>
      </h3>
      {loading ? (
        <div className="flex items-center gap-3 text-ds-silver/50 font-mono text-sm py-4">
          <Loader2 className="animate-spin w-4 h-4" />
          <span>Claude-3-Haiku is scanning the pixel data...</span>
        </div>
      ) : (
        <div className="font-mono text-sm text-ds-silver/80 leading-relaxed whitespace-pre-wrap">
          {reportText}
        </div>
      )}
    </BrutalCard>
  );
}
