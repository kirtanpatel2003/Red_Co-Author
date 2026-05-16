"""v1 smoke-test entry point.

Hardcoded keyword and domain. Chains: draft -> CoJP prompt -> target response.
Prints all three intermediate strings so a human can eyeball the pipeline.
"""

from autoredteam.pipeline.drafter import make_draft
from autoredteam.pipeline.constructor import build_cojp_prompt
from autoredteam.pipeline.runner import run_target

KEYWORD = "Canvas LMS"
DOMAIN = "cyberattack"

SEP = "=" * 72


def _banner(title: str) -> None:
    print(f"\n{SEP}\n{title}\n{SEP}")


def main() -> None:
    _banner(f"v1 smoke test  |  keyword={KEYWORD!r}  domain={DOMAIN!r}")

    _banner("[1/3] DRAFT (mistral)")
    draft = make_draft(KEYWORD)
    print(draft)

    _banner("[2/3] COJP PROMPT (constructor)")
    cojp_prompt = build_cojp_prompt(draft, DOMAIN)
    print(cojp_prompt)

    _banner("[3/3] TARGET RESPONSE (qwen3:8b)")
    response = run_target(cojp_prompt)
    print(response)

    _banner("v1 pipeline complete")


if __name__ == "__main__":
    main()
