---
name: step-out-a-layer
description: When a fix keeps growing or iterating (round 3+, compat shims, encoding gymnastics), stop and re-ask the problem one layer out — the elaborate solution usually means you're solving the wrong problem. Use when stuck in revision loops, when complexity is snowballing, or when the user says "step back / forest for the trees".
---

# Step Out a Layer

You are elaborately solving a problem that should not exist. The tell is never
the problem itself — it's the *shape of your solution*.

## Triggers — invoke this check when you see:

- **Round 3 on the same decision** (a threshold, an encoding, a predicate that
  keeps being wrong in new ways).
- **Compat gymnastics**: designing wire formats, sentinels, or shims so N
  versions/components can all tolerate a weird state.
- **The fix keeps growing**: what started as one line now has a state machine,
  a migration story, and frozen-reader tests.
- **"Handle" instead of "eliminate"**: your plan copes with a bad state on
  every path rather than preventing the state.
- The user says "step back", "forest for the trees", or sounds lost about
  what you're even solving.

## The Move

Ask, in order, and **verify each answer empirically before moving on**:

1. **What state am I engineering around?** Name it in one sentence.
   ("Process start times are unobtainable on macOS 26.")
2. **Why does that state exist?** Go to the *source*, not the symptom.
   ("Because we read one specific sysctl OID that Apple removed.")
3. **Can the state be eliminated instead of handled?** Is there another way to
   get the same data / avoid the same conflict / not enter the state at all?
   ("`ps -o lstart=` still returns it. Verified live on the host.")
4. **What does the elimination heal that the workaround wouldn't?** A
   layer-out fix usually cures the *class*: the workaround fixed 1 of 8 probe
   sites; the source fix healed all 8.

If step 3's answer is genuinely "no, the state is irreducible", the workaround
was right — proceed with it, now with a written justification. That's a valid
outcome; the sin is never asking.

## Worked example (2026-07-24, rbox)

A repo wedged with "prepared Git child incarnation unavailable". Fix v1: map
the probe's `unknown` state into the crash journal → broke two frozen readers
→ fix v2 was designing an impossible-host sentinel valid across three binary
versions. **Trigger: compat gymnastics, round 3.** Layer out: the probe was
`unknown` only because `darwinProcessStart` reads a sysctl macOS 26 removed —
and `ps -o lstart=` still worked (one SSH command to verify). Real fix: ~20-line
fallback at the source. The entire journal-compat project evaporated, and 7
other silently-degraded call sites healed with it.

## Anti-patterns

- Asking the question but accepting a *reasoned* answer where an *empirical*
  one was available (one command would have settled it — run the command).
- Stepping out so far you re-litigate settled scope ("should this feature
  exist?") when the loop is at the mechanism level. Step out ONE layer, check,
  then another if needed.
- Using this to abandon hard work that is genuinely irreducible. The output of
  the check can be "the workaround stands."

## Pairing

After the layer-out fix is chosen, the abandoned workaround often still
contains a small durable improvement (a clearer error, a transient-defer
instead of a permanent wedge) — salvage that, drop the scaffolding.
