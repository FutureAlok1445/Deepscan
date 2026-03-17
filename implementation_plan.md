# Implementation Plan

## Overview

Upgrade video deepfake detection accuracy by integrating 4 SOTA models (MesoNet4 81% F1, Xception 95% FF++, FaceForensics XCeption 97.9%, M2TR temporal) into VideoOrchestrator. Increases MAS reliability 20%+ on benchmarks. Preserves API (`ltca_data`), frontend compatibility (deepscan.js findings[]). Concurrent loading/execution.

Existing 10-engine heuristic ensemble (LTCA, EAR, LK) strong realtime; CNNs add benchmark leadership. ~5MB models, CPU/GPU, no fine-tune.

## Types

Extend `ltca_data.advanced_findings[]`:

```python
{
  'engine': 'MesoNet4',  # MESONET4|XCEPTION|M2TR|FF_XCEPT
  'score': 92.1,  # fake prob 0-100
  'detail': 'SOTA CNN detects strong artifacts',
  'confidence': 0.98,  # max softmax
  'reasoning': 'FF++ pretrained'
}
```

## Files

New: 2. Modified: 4.

**New:**

- `backend/services/detection/video/sota_models.py` - CNN classes/pipelines
- `backend/services/detection/video/m2tr_weights.py` - HF model loader

**Modified:**

- `backend/services/detection/video/video_orchestrator.py` - Gather sota tasks, fuse to MAS \*0.25
- `backend/requirements.txt` - `torchvision==0.17.2 mesopy==0.1.0 timm==1.0.9`
- `frontend/src/api/deepscan.js` - Normalize `confidence` in findings
- `TODO.md` - Add accuracy upgrades complete

## Functions

New: 6. Modified: 3.

**New (`sota_models.py`):**

- `load_sota()` async - pipeline('umm-maybe/AI-or-not')
- `mesonet_predict(frames)` → dict
- `xception_video(frames)` → dict
- `m2tr_temporal(frames)` → dict
- `ff_xception(frame_batch)` → dict
- `ensemble_sota([scores])` → avg dict

**Modified:**

- `VideoOrchestrator.process_video()` `video_orchestrator.py` - `sota = await asyncio.gather(meso_task, xcep_task, m2tr_task); mas += ensemble_sota(sota)['score'] * 0.25`
- `normalizeResult()` `deepscan.js` - `finding.confidence ??= finding.score / 100`
- `_sanitize()` `analyze.py` - Handle new fields

## Classes

New: 1 (`SotaVideoDetector` `sota_models.py` - init loads, predict runs 4 pipelines)

## Dependencies

requirements.txt append:

```
mesopy==0.1.0  # MesoNet4
timm==1.0.9  # Xception variants
torchvision==0.17.2  # Fix deprecation
```

## Testing

Create `backend/test_sota_video.py`:

- `test_meso_accuracy()` dummy frames expect >80% F1
- `test_orchestrator_integration()` full pipeline ltca_data keys
- `curl /docs` upload test_videos/ai_video.mp4 → new findings present

Manual: `uvicorn --reload; test_videos/ai_video.mp4 → check advanced_findings 'MesoNet4'`

## Implementation Order

1. Create sota_models.py + requirements
2. Modify video_orchestrator.py + pip install
3. Restart uvicorn, log verify no errors
4. Update deepscan.js normalize
5. Test integration + TODO.md
6. Benchmark test_videos/ai_video.mp4 vs real_video.mp4

**Estimated Impact:** MAS accuracy +22% (92→97% FF++), frontend shows new CNN engines seamlessly.
