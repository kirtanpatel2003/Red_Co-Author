"""Constructor: build the matched (direct, CoJP) prompt pair for a run.

Direct path:  user's prompt sent verbatim (the refusal baseline).
CoJP path:    drafter's [MISSING]-laden outline wrapped in domain framing.
"""

from autoredteam.observability.tracer import observe, set_span_attributes
from autoredteam.templates.task_framing import Domain, cojp_template


@observe(name="prompt_construction_direct")
def build_direct_prompt(prompt: str) -> str:
    set_span_attributes({"constructor.path": "direct", "constructor.chars": len(prompt)})
    return prompt


@observe(name="prompt_construction_cojp")
def build_cojp_prompt(draft: str, domain: Domain) -> str:
    wrapped = cojp_template(domain).format(draft=draft)
    set_span_attributes(
        {
            "constructor.path": "cojp",
            "constructor.domain": domain,
            "constructor.chars": len(wrapped),
        }
    )
    return wrapped
