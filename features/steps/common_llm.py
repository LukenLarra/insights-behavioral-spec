"""LLM-based assertions for BDD tests using Groq."""

import json

from behave import then


def _evaluate_condition(context, condition: str, payload: dict) -> bool:
    """Send a condition and payload to the LLM and return True/False."""
    assert context.llm_client is not None, "LLM client not initialized"

    prompt = f"""
    You are a strict software test evaluator. Your only task is to validate
    whether the provided JSON payload satisfies the following condition:
    "{condition}"

    Reply STRICTLY and ONLY with "True" if the condition is met, or "False" if not.
    No other text, explanation, or punctuation.

    JSON payload to evaluate:
    {json.dumps(payload, indent=2)}
    """

    completion = context.llm_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You are a strict evaluator that ONLY outputs 'True' or 'False'.",
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=5,
        temperature=0,
    )
    result = completion.choices[0].message.content.strip().lower()
    return result == "true"


@then('the LLM confirms that "{condition}"')
def step_llm_confirms_condition(context, condition):
    """Verify a condition using the LLM over the last API response."""
    if not context.llm_enabled:
        context.scenario.skip("Skipped: GROQ_API_KEY not available")
        return

    assert context.response is not None, "No response to evaluate"

    payload = (
        context.response
        if isinstance(context.response, dict)
        else context.response.json()
    )

    try:
        result = _evaluate_condition(context, condition, payload)
        assert result, f"LLM evaluated condition as False: '{condition}'"

    except Exception as e:
        import groq
        if isinstance(e, groq.RateLimitError):
            context.scenario.skip(f"Skipped: Groq rate limit reached")
            return
        raise AssertionError(f"LLM assertion error: {e}") from e


@then('the LLM confirms that the response is consistent with the request')
def step_llm_confirms_consistency(context, condition):
    """Verify that the response is semantically consistent with the request."""
    if not context.llm_enabled:
        context.scenario.skip("Skipped: GROQ_API_KEY not available")
        return

    assert context.response is not None, "No response to evaluate"
    assert context.request is not None, "No request to compare against"

    payload = context.response.json()

    prompt = f"""
    You are a strict software test evaluator. Verify that the following API
    response is semantically consistent with the request that generated it.
    A response is consistent if it addresses the request, contains no contradictions,
    and the data returned relates logically to the input provided.

    Reply STRICTLY and ONLY with "True" if consistent, or "False" if not.

    Request: {json.dumps(context.request, indent=2)}
    Response: {json.dumps(payload, indent=2)}
    """

    try:
        completion = context.llm_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "You are a strict evaluator that ONLY outputs 'True' or 'False'.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=5,
            temperature=0,
        )
        result = completion.choices[0].message.content.strip().lower()
        assert result == "true", "LLM evaluated response as inconsistent with request"

    except Exception as e:
        import groq
        if isinstance(e, groq.RateLimitError):
            context.scenario.skip("Skipped: Groq rate limit reached")
            return
        raise AssertionError(f"LLM assertion error: {e}") from e


@then('the LLM confirms that no sensitive data is exposed in the response')
def step_llm_confirms_no_sensitive_data(context):
    """Verify that the response does not expose sensitive data."""
    if not context.llm_enabled:
        context.scenario.skip("Skipped: GROQ_API_KEY not available")
        return

    assert context.response is not None, "No response to evaluate"

    payload = context.response.json()

    condition = (
        "the JSON contains no sensitive data such as passwords, tokens, "
        "API keys, private keys, secret values, or internal file paths"
    )

    try:
        result = _evaluate_condition(context, condition, payload)
        assert result, "LLM detected sensitive data in the response"

    except Exception as e:
        import groq
        if isinstance(e, groq.RateLimitError):
            context.scenario.skip("Skipped: Groq rate limit reached")
            return
        raise AssertionError(f"LLM assertion error: {e}") from e


@then('the LLM confirms that the error message is helpful and actionable')
def step_llm_confirms_error_message(context):
    """Verify that an error response contains a helpful and actionable message."""
    if not context.llm_enabled:
        context.scenario.skip("Skipped: GROQ_API_KEY not available")
        return

    assert context.response is not None, "No response to evaluate"

    payload = context.response.json()

    condition = (
        "the error message is clear, helpful, and actionable for a developer — "
        "it explains what went wrong without exposing internal implementation details "
        "such as stack traces, file paths, or database internals"
    )

    try:
        result = _evaluate_condition(context, condition, payload)
        assert result, "LLM evaluated error message as unhelpful or exposing internals"

    except Exception as e:
        import groq
        if isinstance(e, groq.RateLimitError):
            context.scenario.skip("Skipped: Groq rate limit reached")
            return
        raise AssertionError(f"LLM assertion error: {e}") from e