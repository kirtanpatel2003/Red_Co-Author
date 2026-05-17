"""Constructor: build the matched (direct, CoJP) prompt pair for a run.

Direct path:  user's prompt sent verbatim (the refusal baseline).
CoJP path:    drafter's [MISSING]-laden outline wrapped in domain framing.
"""

from autoredteam.templates.task_framing import Domain, cojp_template


def build_direct_prompt(prompt: str) -> str:
    return prompt


def build_cojp_prompt(draft: str, domain: Domain) -> str:
    return cojp_template(domain).format(draft=draft)
