"""System prompt for the AIRecon security agent."""

from __future__ import annotations

from pathlib import Path

from .config import get_config

with open(Path(__file__).parent / "prompts" / "system.txt", "r") as f:
    SYSTEM_PROMPT = f.read()


def _load_local_skills() -> str:
    """Load local skills from airecon/proxy/skills/*.md and append to prompt.

    Skills are listed as read_file references. The SOP and tool catalog will
    be auto-loaded via auto_load_skills_for_message() when triggered by keywords.
    """
    skills_dir = Path(__file__).resolve().parent / "skills"
    if not skills_dir.exists():
        return ""

    # Skills to embed directly (always available without read_file)
    EMBED_SKILLS = {
        "install.md",
        "scripting.md",
        "tool_catalog.md",
        "full_recon_sop.md",
        "browser_automation.md",
        "nuclei_doc.md",
        "sqlmap_doc.md",
        "dalfox_doc.md",
        "nmap_doc.md",
        "semgrep_doc.md",
    }

    embedded_parts: list[str] = []
    reference_parts: list[str] = []

    for path in sorted(skills_dir.rglob("*.md")):
        if path.name in EMBED_SKILLS:
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
                embedded_parts.append(
                    f'\n<embedded_skill name="{path.name}">\n{content}\n</embedded_skill>\n'
                )
            except Exception:
                reference_parts.append(f"- {path.absolute().as_posix()}")
        else:
            reference_parts.append(f"- {path.absolute().as_posix()}")

    result = ""

    if embedded_parts:
        result += (
            "\n\n<core_skills>\n"
            "The following skill documents are pre-loaded for you. "
            "You do NOT need to read_file these — they are already available:\n"
            + "".join(embedded_parts)
            + "</core_skills>\n"
        )

    if reference_parts:
        result += (
            "\n\n<available_skills>\n"
            "Additional skill documents available via read_file. "
            "Load the relevant one when you need specialized guidance:\n"
            + "\n".join(reference_parts)
            + "\n</available_skills>\n"
        )

    return result


# Keyword → skill file mapping for auto-loading
_SKILL_KEYWORDS: dict[str, str] = {
    "sql injection": "vulnerabilities/sql_injection.md",
    "sqli": "vulnerabilities/sql_injection.md",
    "xss": "vulnerabilities/xss.md",
    "cross-site scripting": "vulnerabilities/xss.md",
    "ssrf": "vulnerabilities/ssrf.md",
    "csrf": "vulnerabilities/csrf.md",
    "xxe": "vulnerabilities/xxe.md",
    "idor": "vulnerabilities/idor.md",
    "rce": "vulnerabilities/rce.md",
    "remote code execution": "vulnerabilities/rce.md",
    "lfi": "vulnerabilities/path_traversal_lfi_rfi.md",
    "rfi": "vulnerabilities/path_traversal_lfi_rfi.md",
    "path traversal": "vulnerabilities/path_traversal_lfi_rfi.md",
    "file upload": "vulnerabilities/insecure_file_uploads.md",
    "open redirect": "vulnerabilities/open_redirect.md",
    "subdomain takeover": "vulnerabilities/subdomain_takeover.md",
    "jwt": "vulnerabilities/authentication_jwt.md",
    "api": "vulnerabilities/api_testing.md",
    "graphql": "protocols/graphql.md",
    "active directory": "protocols/active_directory.md",
    "cloud": "technologies/cloud_security.md",
    "aws": "technologies/cloud_security.md",
    "firebase": "technologies/firebase_firestore.md",
    "supabase": "technologies/supabase.md",
    "race condition": "vulnerabilities/race_conditions.md",
    "toctou": "vulnerabilities/race_conditions.md",
    "time of check": "vulnerabilities/race_conditions.md",
    "double spend": "vulnerabilities/race_conditions.md",
    "double redeem": "vulnerabilities/race_conditions.md",
    "double refund": "vulnerabilities/race_conditions.md",
    "concurrent request": "vulnerabilities/race_conditions.md",
    "parallel request": "vulnerabilities/race_conditions.md",
    "turbo intruder": "vulnerabilities/race_conditions.md",
    "last-byte sync": "vulnerabilities/race_conditions.md",
    "single-packet attack": "vulnerabilities/race_conditions.md",
    "http2 race": "vulnerabilities/race_conditions.md",
    "race_http2": "vulnerabilities/race_conditions.md",
    "prototype pollution": "vulnerabilities/prototype_pollution.md",
    "web cache": "vulnerabilities/web_cache_poisoning.md",
    "cache poisoning": "vulnerabilities/web_cache_poisoning.md",
    "privilege escalation": "vulnerabilities/privilege_escalation.md",
    "mass assignment": "vulnerabilities/mass_assignment.md",
    "business logic": "vulnerabilities/business_logic.md",
    "workflow bypass": "vulnerabilities/business_logic.md",
    "state machine": "vulnerabilities/business_logic.md",
    "price manipulation": "vulnerabilities/business_logic.md",
    "price tampering": "vulnerabilities/business_logic.md",
    "coupon abuse": "vulnerabilities/business_logic.md",
    "discount abuse": "vulnerabilities/business_logic.md",
    "payment logic": "vulnerabilities/business_logic.md",
    "refund abuse": "vulnerabilities/business_logic.md",
    "quota bypass": "vulnerabilities/business_logic.md",
    "limit bypass": "vulnerabilities/business_logic.md",
    "inventory race": "vulnerabilities/business_logic.md",
    "idempotency": "vulnerabilities/business_logic.md",
    "saga": "vulnerabilities/business_logic.md",
    "information disclosure": "vulnerabilities/information_disclosure.md",
    "tls": "reconnaissance/full_recon_sop.md",
    "ssl": "reconnaissance/full_recon_sop.md",
    "dns": "reconnaissance/full_recon_sop.md",
    "javascript recon": "reconnaissance/full_recon_sop.md",
    "js recon": "reconnaissance/full_recon_sop.md",
    "nextjs": "frameworks/nextjs.md",
    "fastapi": "frameworks/fastapi.md",
    "exploitation": "vulnerabilities/exploitation.md",
    "full recon": "reconnaissance/full_recon_sop.md",
    "deep recon": "reconnaissance/full_recon_sop.md",
    "comprehensive": "reconnaissance/full_recon_sop.md",
    "pentest": "reconnaissance/full_recon_sop.md",
    "penetration test": "reconnaissance/full_recon_sop.md",
    "bug bounty": "reconnaissance/full_recon_sop.md",
    # Added missing keywords from TODO
    "ssti": "vulnerabilities/ssti.md",
    "server-side template injection": "vulnerabilities/ssti.md",
    "template injection": "vulnerabilities/ssti.md",
    "deserialization": "vulnerabilities/deserialization.md",
    "http smuggling": "vulnerabilities/http_smuggling.md",
    "request smuggling": "vulnerabilities/http_smuggling.md",
    "oauth": "vulnerabilities/oauth_saml.md",
    "saml": "vulnerabilities/oauth_saml.md",
    "websocket": "vulnerabilities/websocket.md",
    "ws": "vulnerabilities/websocket.md",
    "kubernetes": "vulnerabilities/kubernetes.md",
    "k8s": "vulnerabilities/kubernetes.md",
    "grpc": "vulnerabilities/grpc.md",
    "supply chain": "vulnerabilities/supply_chain.md",
    "ci/cd": "vulnerabilities/supply_chain.md",
    "waf": "vulnerabilities/waf_detection.md",
    "waf detection": "vulnerabilities/waf_detection.md",
    "bypass waf": "vulnerabilities/waf_detection.md",
    # Payload library auto-load
    "xss payload": "payloads/xss.md",
    "xss polyglot": "payloads/xss.md",
    "sql injection payload": "payloads/sqli.md",
    "sqli payload": "payloads/sqli.md",
    "ssrf payload": "payloads/ssrf.md",
    "xxe payload": "payloads/xxe.md",
    # Browser automation
    "browser_action": "tools/browser_automation.md",
    "browser automation": "tools/browser_automation.md",
    "headless browser": "tools/browser_automation.md",
    "chromium": "tools/browser_automation.md",
    "xss verification": "tools/browser_automation.md",
    # Advanced scripting templates — trigger scripting.md for script references
    "js secret": "tools/scripting.md",
    "js extractor": "tools/scripting.md",
    "secret extractor": "tools/scripting.md",
    "javascript secret": "tools/scripting.md",
    "js recon script": "tools/scripting.md",
    "idor scanner": "tools/scripting.md",
    "idor script": "tools/scripting.md",
    "sequential scan": "tools/scripting.md",
    "subdomain takeover script": "tools/scripting.md",
    "takeover checker": "tools/scripting.md",
    "ssti exploit": "tools/scripting.md",
    "ssti script": "tools/scripting.md",
    "template engine": "tools/scripting.md",
    "blind sqli extractor": "tools/scripting.md",
    "sqli extractor": "tools/scripting.md",
    "boolean blind": "tools/scripting.md",
    "bit extractor": "tools/scripting.md",
    "http smuggling script": "tools/scripting.md",
    "smuggling probe": "tools/scripting.md",
    "cl.te": "tools/scripting.md",
    "te.cl": "tools/scripting.md",
    "graphql batch": "tools/scripting.md",
    "alias batch": "tools/scripting.md",
    "graphql brute": "tools/scripting.md",
    "jwt attack": "tools/scripting.md",
    "jwt suite": "tools/scripting.md",
    "alg none": "tools/scripting.md",
    "algorithm confusion": "tools/scripting.md",
    "prototype pollution script": "tools/scripting.md",
    "broken access control script": "tools/scripting.md",
    "origin ip": "tools/scripting.md",
    "cloudflare bypass": "tools/scripting.md",
    "websocket fuzz": "tools/scripting.md",
    "cors exploit": "tools/scripting.md",
    "oauth script": "tools/scripting.md",
    # SSRF scripts
    "blind ssrf": "tools/scripting.md",
    "ssrf interactsh": "tools/scripting.md",
    "ssrf oob": "tools/scripting.md",
    "ssrf cloud": "tools/scripting.md",
    "ssrf aws": "tools/scripting.md",
    "ssrf metadata": "tools/scripting.md",
    "ssrf credential": "tools/scripting.md",
    "imds": "tools/scripting.md",
    # Cache poisoning scripts
    "cache poison script": "tools/scripting.md",
    "cache prober": "tools/scripting.md",
    "web cache script": "tools/scripting.md",
    "x-forwarded-host": "tools/scripting.md",
    "unkeyed header": "tools/scripting.md",
    "fat get": "tools/scripting.md",
    "cache buster": "tools/scripting.md",
    # OAuth advanced scripts
    "pkce bypass": "tools/scripting.md",
    "pkce downgrade": "tools/scripting.md",
    "token reuse": "tools/scripting.md",
    "code reuse": "tools/scripting.md",
    "state fixation": "tools/scripting.md",
    "redirect uri bypass": "tools/scripting.md",
    "oauth advanced": "tools/scripting.md",
    "authorization code": "tools/scripting.md",
    # Advanced fuzzing
    "fuzzing": "tools/advanced_fuzzing.md",
    "zero-day": "tools/advanced_fuzzing.md",
    # nmap / naabu — auto-load doc with pre-conditions when mentioned
    "nmap": "tools/nmap_doc.md",
    "naabu": "tools/nmap_doc.md",
    "port scan": "tools/nmap_doc.md",
    "port scanning": "tools/nmap_doc.md",
    "masscan": "tools/nmap_doc.md",
    # Nuclei — auto-load doc with pre-conditions when nuclei is mentioned
    "nuclei": "tools/nuclei_doc.md",
    "nuclei scan": "tools/nuclei_doc.md",
    "nuclei template": "tools/nuclei_doc.md",
    # semgrep — auto-load doc with pre-conditions when mentioned
    "semgrep": "tools/semgrep_doc.md",
    "sast": "tools/semgrep_doc.md",
    "static analysis": "tools/semgrep_doc.md",
    "source code analysis": "tools/semgrep_doc.md",
    # caido — auto-load when mentioned
    "caido": "tools/caido.md",
    "caido-cli": "tools/caido.md",
    "caido-setup": "tools/caido.md",
    "web proxy": "tools/caido.md",
    "intercept": "tools/caido.md",
    "replay request": "tools/caido.md",
    "automate": "tools/caido.md",
    # dalfox — auto-load doc with pre-conditions when mentioned
    "dalfox": "tools/dalfox_doc.md",
    "xss scanner": "tools/dalfox_doc.md",
    "xss scan": "tools/dalfox_doc.md",
    "dom xss": "tools/dalfox_doc.md",
    "blind xss": "tools/dalfox_doc.md",
    "reflected xss": "tools/dalfox_doc.md",
    # sqlmap / ghauri — auto-load doc with pre-conditions when mentioned
    "sqlmap": "tools/sqlmap_doc.md",
    "ghauri": "tools/sqlmap_doc.md",
    "sql injection scanner": "tools/sqlmap_doc.md",
    # arjun / x8 — parameter discovery tools
    "arjun": "vulnerabilities/sql_injection.md",
    "x8": "vulnerabilities/sql_injection.md",
    "parameter discovery": "vulnerabilities/sql_injection.md",
    "hidden parameter": "vulnerabilities/sql_injection.md",
    "parameter pollution": "tools/advanced_fuzzing.md",
    "expert testing": "tools/advanced_fuzzing.md",
    "creative exploit": "tools/advanced_fuzzing.md",
    "bypass": "tools/advanced_fuzzing.md",
    "waf bypass": "tools/advanced_fuzzing.md",
}


def auto_load_skills_for_message(user_message: str) -> str:
    """Auto-detect relevant skills from user message and return their content.

    Returns skill content ready for injection into conversation context.
    """
    skills_dir = Path(__file__).resolve().parent / "skills"
    if not skills_dir.exists():
        return ""

    msg_lower = user_message.lower()
    matched_skills: set[str] = set()

    for keyword, skill_path in _SKILL_KEYWORDS.items():
        if keyword in msg_lower:
            matched_skills.add(skill_path)

    if not matched_skills:
        return ""

    # Limit to 4 skills to avoid context explosion but allow more relevant loading
    parts: list[str] = []
    for skill_rel in list(matched_skills)[:4]:
        skill_file = skills_dir / skill_rel
        if skill_file.exists():
            try:
                content = skill_file.read_text(encoding="utf-8", errors="replace")
                # Tool reference docs get a higher budget; other skills stay at 4000
                limit = 12000 if skill_rel.startswith("tools/") else 4000
                if len(content) > limit:
                    content = (
                        content[:limit]
                        + f"\n... (truncated at {limit} chars, use read_file for full content: {skill_file.absolute().as_posix()})"
                    )
                parts.append(f"[AUTO-LOADED SKILL: {skill_rel}]\n{content}")
            except Exception:
                pass

    if not parts:
        return ""

    return (
        "[SYSTEM: RELEVANT SKILLS AUTO-LOADED based on your request]\n"
        + "\n---\n".join(parts)
    )


def get_system_prompt() -> str:
    """Return the system prompt for the security agent."""
    prompt = SYSTEM_PROMPT

    cfg = get_config()
    if cfg.allow_destructive_testing:
        prompt = prompt.replace(
            "You have FULL AUTHORIZATION for non-destructive penetration testing",
            "You have FULL AUTHORIZATION for UNRESTRICTED DESTRUCTIVE penetration testing",
        )
        safety_override = """
<safety_override>
WARNING: DESTRUCTIVE MODE ENABLED
- You are authorized to perform destructive actions in this session.
- Use maximum threads and deep recursion. Ignore polite rate limits.
- Zero false positives remain mandatory: never report without a working PoC.
  A crash is NOT a vulnerability unless you understand WHY and can reproduce it.
  Verification is MANDATORY. Hypothetical vulnerabilities are failures.
</safety_override>
"""
        prompt = prompt.replace(
            "<execution_guidelines>", safety_override + "\n<execution_guidelines>"
        )

    return prompt + _load_local_skills()
