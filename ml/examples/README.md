# Example outputs

Produced by running the pipeline on **synthetic** pulse data
(`make_synthetic_data.py` → `train.py` → `evaluate.py`). Clean vs noisy synthetic
signals are easily separable, so the metrics are 100% — this only proves the
pipeline runs end to end.

**Your real numbers, trained on webcam data you collect, will be lower and more
interesting.** Real "good" and "bad" pulse windows overlap (a slightly shaky but
usable reading, dim light, etc.), so the confusion matrix will show real mistakes
— exactly what's worth discussing in a writeup.
