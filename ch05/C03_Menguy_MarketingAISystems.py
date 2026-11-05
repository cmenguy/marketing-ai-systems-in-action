"""A batch runner: concurrent, resumable, and producing a manifest (Listing 5.3).

A campaign launch is not one asset, and treating it as a loop over single
generations is how a launch that should take minutes takes hours and fails halfway
with no record of what got done. The unit of work is the batch, and a batch has
requirements a single call does not: it runs concurrently against a rate-limited
API, it survives partial failure, and it produces a manifest of exactly what was
generated so the launch is auditable and resumable.

The batch is also where cost and time become computable (chapter 8): a known token
bill, a burst profile, and the draft-cheap / final-expensive routing that only
pays off at batch scale.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from C01_Menguy_MarketingAISystems import GenerationSpec, sample_facts


def expand(brief, campaign, segments, channels, facts, fingerprint):
    # Variant expansion from the chapter text, used here to build the specs
    # the batch runs: one spec per (segment, channel) pair.
    specs = []
    for segment in segments:
        for channel in channels:
            specs.append(GenerationSpec(
                brief=brief,
                segment=segment,
                channel=channel,
                campaign_code=campaign,
                facts=facts,
                prompt_fingerprint=fingerprint,
            ))
    return specs


def run_batch(specs, generate_one, done_codes, max_workers=8):
    pending = [s for s in specs
               if (s.campaign_code, s.segment, s.channel) not in done_codes]
    manifest, failures = [], []
    with ThreadPoolExecutor(max_workers) as pool:
        futures = {pool.submit(generate_one, s): s for s in pending}
        for fut in as_completed(futures):
            spec = futures[fut]
            try:
                manifest.append(fut.result())
            except Exception as err:  # noqa: BLE001 - collect, never fatal
                failures.append((spec, str(err)))
    return manifest, failures


if __name__ == "__main__":
    specs = expand(
        brief="Launch the Cascade shell for spring.",
        campaign="cascade-spring-2026",
        segments=("loyalty", "lapsed_12mo"),
        channels=("email", "sms"),
        facts=sample_facts(),
        fingerprint="copy.launch:v3",
    )

    def flaky_generate(spec):
        # One variant hits a transient error; the rest succeed.
        if spec.segment == "lapsed_12mo" and spec.channel == "sms":
            raise TimeoutError("provider timeout")
        return {"code": spec.campaign_code, "segment": spec.segment,
                "channel": spec.channel, "copy": "<generated>",
                "prompt_fingerprint": spec.prompt_fingerprint}

    manifest, failures = run_batch(specs, flaky_generate, done_codes=set())
    print(f"generated {len(manifest)}, failed {len(failures)}")
    assert len(manifest) == 3 and len(failures) == 1, "partial failure survives"

    # Resume: only the failed spec is re-run, and this time it succeeds.
    done = {(m["code"], m["segment"], m["channel"]) for m in manifest}
    manifest2, failures2 = run_batch(
        specs, lambda s: {"code": s.campaign_code, "segment": s.segment,
                          "channel": s.channel, "copy": "<generated>",
                          "prompt_fingerprint": s.prompt_fingerprint},
        done_codes=done)
    print(f"resume filled {len(manifest2)} hole(s), failed {len(failures2)}")
    assert len(manifest2) == 1 and not failures2, "resume regenerates only the hole"
    print("OK: partial failure is non-fatal and a re-run fills only the gaps.")
