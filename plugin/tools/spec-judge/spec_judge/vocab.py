"""The closed vocabularies of the evaluation surface.

``Category``, ``Severity``, and ``Role`` are shared by ``contracts.py`` (the
``Rubric`` a panel probes) and ``evaluator.py`` (the ``Concern``/``EvalRequest``/
``EvalResult`` shapes a seat exchanges). They live in their own module — rather
than on either of those — so both can import the same aliases without an
import cycle: ``evaluator.py`` already imports ``Rubric`` from ``contracts.py``.
"""

from __future__ import annotations

from typing import Literal

Category = Literal["B1", "B2", "B3", "B4"]
Severity = Literal["high", "medium", "low"]
Role = Literal["fault-seeker", "conformance-checker", "arbiter"]
