"""Ask the agent from the command line. `demo` runs the scripted questions at their own clock values.

uv run python -m app.ask demo
uv run python -m app.ask claims TRN-051 "link up, counters zero after SFP replacement" --counters zero
uv run python -m app.ask access SITE-NILO --clock 2026-10-21T00:00:00
"""

import argparse

from app import ingest
from app.claims import access_for, claims_for

SYMPTOM = "link up, counters zero after SFP replacement"


def _show(title: str, answer: dict) -> None:
    print(f"\n=== {title}")
    print(f"Tier: {answer['tier']}")
    if "match_level" in answer:
        print(f"Match: {answer['match_level']}. {answer.get('match_note') or ''}".rstrip())
    print(f"Next step: {answer['next_step']}")
    if answer.get("action_kind"):
        print(f"Action kind: {answer['action_kind']}")
    if answer.get("prohibition"):
        print(f"Prohibition: {answer['prohibition']}")
    used = answer.get("observed_used", {})
    if used.get("counters_from"):
        print(f"Counters: {used['counters']}, from {used['counters_from']}")
    print(f"What would change this: {answer['what_would_change']}")
    if answer.get("ask_group"):
        print(f"Ask: {answer['ask_group']} (reason {answer['reason_code']})")
    if "boundary_known" in answer and not answer["boundary_known"]:
        print("Boundary: not known")
    if answer["evidence_rendered"]:
        print("Evidence:")
        for line in answer["evidence_rendered"].splitlines():
            print(f"  {line}" if line else "")


def demo() -> None:
    ingest.run(until="2026-10-14T22:00:00")
    _show("Before capture: TRN-051, clock 14.10.", claims_for("TRN-051", SYMPTOM))

    ingest.run(until="2026-10-20T12:00:00")
    _show("After capture: TRN-051, counters not known, clock 20.10.", claims_for("TRN-051", SYMPTOM))
    _show(
        "After capture: TRN-051, counters reported at zero",
        claims_for("TRN-051", SYMPTOM, observed={"counters": "zero"}),
    )
    _show(
        "A different symptom on TRN-051",
        claims_for("TRN-051", "intermittent CRC errors on uplink"),
    )
    _show(
        "After a reported failed bounce",
        claims_for("TRN-051", SYMPTOM, observed={"counters": "zero", "bounce_failed": True}),
    )
    _show("The newer generation before anyone narrowed the advice: TRN-100", claims_for("TRN-100", SYMPTOM))
    _show("Before driving to Nilo, clock 20.10.", access_for("SITE-NILO"))

    ingest.run(until="2026-10-21T00:00:00")
    _show("Before driving to Nilo, after the key moved, clock 21.10.", access_for("SITE-NILO"))
    _show("Where was the key on 10.10.?", access_for("SITE-NILO", at="2026-10-10"))

    ingest.run(until="2026-10-21T10:50:00")
    _show(
        "During the fault on TRN-051: nobody reports counters, the agent reads them, clock 21.10. 10:50",
        claims_for("TRN-051", SYMPTOM),
    )

    ingest.run(until="2026-10-31T00:00:00")
    _show("The newer generation after a reported failure: TRN-100, clock 31.10.", claims_for("TRN-100", SYMPTOM))

    ingest.run(until="2026-11-03T00:00:00")
    _show(
        "After two experts disagree: TRN-051, clock 3.11.",
        claims_for("TRN-051", SYMPTOM, observed={"counters": "zero"}),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask the agent.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("demo", help="Run the scripted questions.")

    claims = commands.add_parser("claims", help="What to do about a symptom on a unit.")
    claims.add_argument("entity")
    claims.add_argument("symptom")
    claims.add_argument("--clock", help="Rebuild the store as of this time first.")
    claims.add_argument("--at", help="A point in world time.")
    claims.add_argument("--link", choices=["up", "down", "unknown"])
    claims.add_argument("--counters", choices=["rising", "zero", "unknown"])
    claims.add_argument("--bounce-done", action="store_true")
    claims.add_argument("--bounce-failed", action="store_true")

    access = commands.add_parser("access", help="How to reach a place.")
    access.add_argument("place")
    access.add_argument("--clock", help="Rebuild the store as of this time first.")
    access.add_argument("--at", help="A point in world time.")

    args = parser.parse_args()
    if args.command == "demo":
        demo()
        return
    if args.clock:
        ingest.run(until=args.clock)
    if args.command == "access":
        _show(f"Access to {args.place}", access_for(args.place, at=args.at))
        return
    observed = {
        "link": args.link,
        "counters": args.counters,
        "bounce_done": args.bounce_done,
        "bounce_failed": args.bounce_failed,
    }
    _show(f"{args.entity}: {args.symptom}", claims_for(args.entity, args.symptom, args.at, observed))


if __name__ == "__main__":
    main()
