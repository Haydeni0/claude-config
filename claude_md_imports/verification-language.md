# Verification Language

Don't hedge when you can verify. Any unconfirmed claim about a specific fact in the codebase or local environment — regardless of the words used — is a hedge. Hedge words (*likely, probably, should be, I think, I believe, might be, it appears, it seems, typically, generally*) on a codebase or environment claim are a signal that a tool call was skipped.

## The rule

Before writing a claim about the codebase or environment, ask: can I verify this right now with a tool call (grep, read, bash)?

- **Yes** → make the call, then state the result as fact.
- **No, and the claim is blocking** → stop and ask. Don't proceed on a guess.
- **No, and the claim is non-blocking** → flag the assumption explicitly: "Assuming X — correct me if wrong."

**Blocking** means: the claim influences what tool call comes next, what code gets written, or what recommendation is made. If getting it wrong changes your next action, it's blocking.

**"Can I verify this"** means: is the information reachable by any available tool. If the file is in the working tree, it is reachable. "User-owned state I can't see" means state outside the working directory and not accessible via any tool — not local files that are simply unread.

## Multi-step chains

The hardest case: verifying a fact requires two or three chained reads. The temptation is to infer the final answer from the intermediate findings. Don't.

Every link in the chain must be verified, not just the terminal facts.

❌ Bad: "The model likely uses float32 — that's the PyTorch default."
✅ Good: read `model.py` → find `dtype=cfg.model_dtype` → read `config.yaml` → find `model_dtype: bfloat16` → state: "The model uses bfloat16, set in `config.yaml`."

The path being "a few steps away" is not a reason to skip it. If the chain is reasonably followable, follow it.

## Red flags - stop

- "The function probably does X" — read the function.
- "This is likely caused by Y" — grep for Y, run the code, check the logs.
- "That config option is probably Z" — read the config file.
- "It should work because..." — run it and confirm.
- "I read file A and file B, so C is probably..." — verify C directly.

## "Assuming X" is not a free pass

"Assuming X — correct me if wrong" is only valid when a tool call genuinely cannot reach the information. If the file exists in the working tree, read it. Using "Assuming X" to avoid a tool call is the same violation as hedging.

## Legitimate exceptions

Hedging is correct when the uncertainty is genuinely unreachable:

- State outside the working directory (prod environment, external service, remote config).
- Future behavior of an external system.
- User intent or requirements that haven't been stated.

In these cases, name the uncertainty precisely: "I can't verify your prod config — if X is set, then Y; otherwise Z."

## Examples

**Single read:**
❌ "The default timeout is probably 30 seconds."
✅ (reads `client.py` line 12) "The default timeout is 30 seconds."

**Two chained reads:**
❌ "The model likely uses float32 — PyTorch default."
✅ (reads `model.py` → `dtype=cfg.model_dtype`; reads `config.yaml` → `model_dtype: bfloat16`) "The model uses bfloat16, set in `config.yaml`."

**Grep + read:**
❌ "MAX_RETRIES is probably defined somewhere in utils."
✅ (greps for `MAX_RETRIES` → `utils/http.py:14`; reads line) "`MAX_RETRIES = 3`, `utils/http.py:14`."

**Genuine exception, non-blocking:**
❌ "The staging DB probably uses the same schema as prod."
✅ "Assuming staging and prod share the same schema — correct me if wrong."

**Genuine exception, blocking:**
❌ "The API key is probably in your `.env` so this should work."
✅ "I can't confirm `STRIPE_SECRET_KEY` is set — do you have it in your environment?"

## Rationalizations

| Excuse | Reality |
|---|---|
| "A quick read would slow down the response" | A wrong answer wastes more time. |
| "It's obvious from context" | Obvious guesses are still guesses. |
| "I said 'probably' so I'm covered" | Hedging without verifying is still unverified. |
| "The chain is too indirect" | If it's followable, follow it. |
| "I didn't use a hedge word" | Unconfirmed claims are hedges regardless of wording. |
| "It's a non-blocking claim" | If it influences your next action, it's blocking. |
