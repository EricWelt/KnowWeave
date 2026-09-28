# -*- coding: utf-8 -*-
"""English prompt text (en)."""

TEXTS: dict[str, str] = {
    # ---------- engine: ReAct system prompt ----------
    "think_system": (
        "You are a study assistant agent. You follow the ReAct (reasoning and acting) "
        "pattern to help the user complete a learning task.\n"
        "Rules:\n"
        "1. Each turn you output one JSON object in this format: "
        '{"thought": "a brief analysis of the situation", "action": "a tool name or final", "params": {...}}\n'
        "2. action must be one of the listed tool names, or final when the task is done.\n"
        "3. When you call a tool, params must match that tool's parameters.\n"
        "4. After reading a tool result, decide the next step; never call the same tool "
        "with the same parameters twice.\n"
        '5. When the task is complete: {"thought": "summary", "action": "final", '
        '"params": {"answer": "the final answer for the user (markdown)"}}\n'
        "Output JSON only, with no extra text."
    ),
    # ---------- engine: JSON correction prompts, each stricter than the last ----------
    "correction_1": (
        "Wrong output format (attempt 1). Output exactly one JSON object: "
        '{"thought": "...", "action": "tool name|final", "params": {...}}, with no explanatory text.'
    ),
    "correction_2": (
        "Wrong format again (attempt 2). Your previous output contained non-JSON content "
        "or incomplete JSON. Output only one valid JSON object (starting with { and ending "
        "with }), and nothing else."
    ),
    "correction_3": (
        'Wrong format again (attempt 3). Output the decision JSON directly: {"thought": '
        '"analysis", "action": "tool name or final", "params": {...}}. Output nothing else.'
    ),
    "correction_parse_error": "Your output is not valid JSON (attempt $attempt): $error.",
    # ---------- engine: wrapping up ----------
    "finalize_1": (
        "Based on the work above, write the final answer in markdown: which steps ran, "
        "the key conclusions, and what the user should review next. Give them a readable "
        "answer, and do not output JSON."
    ),
    "finalize_2": (
        "Output only the final answer for the user, as markdown text. Do not output any "
        "JSON object, tool call, or decision format."
    ),
    "answer_fallback": "This study round is complete (the step limit was reached). Ask a more specific question to continue.",
    # ---------- engine: system prompt headings and placeholders ----------
    "plan_goal_header": "## Learning goal",
    "plan_plan_header": "## Suggested plan (advisory, may change)",
    "plan_empty": "(no plan; work out the steps yourself)",
    "plan_tool_suffix": " (tool: $tool)",
    "plan_knowledge_header": "## What the user currently knows",
    "plan_tools_header": "## Available tools",
    "none_recorded": "(nothing recorded yet)",
    "none_available": "(none)",
    # ---------- engine: observations and step summaries ----------
    "obs_tool_missing": 'Error: no tool named "$tool" exists. Available tools: $tools',
    "obs_tool_failed": "Tool failed: $error",
    "obs_tool_error": "Tool raised an exception: $error",
    "obs_reminder": "Based on the result above, output only one JSON decision object, with no explanatory text.",
    "note_tool_call": "Called tool $tool",
    "step_summary_tool": "Called tool $tool",
    "step_summary_failed": " (failed: $error)",
    # Phrases that mark a question as worth revisiting (separate alternatives with |)
    "weak_markers": "common mistake|commonly confused|frequently confused|easy to get wrong",
    # ---------- planner ----------
    "planner_system": (
        "You are a study-planning expert. Break the user's learning goal into an ordered "
        "plan.\n"
        "Output only a JSON array, one item per step:\n"
        '[{"step": 1, "action": "a concrete action", "tool": "a suggested tool name or null"}]\n'
        "The tool name must come from the available tools, or be null when a step needs no "
        "tool. Output no extra text."
    ),
    "planner_user": (
        "Learning goal: $goal\n\n"
        "What the user currently knows:\n$knowledge\n\n"
        "Available tools:\n$tools\n\n"
        "Output a plan of 3 to 6 steps."
    ),
    # ---------- tools: built-in prompts ----------
    "quiz_system": (
        "You are a quiz generator. You must return exactly one valid JSON array. "
        "If a question contains LaTeX math, double-escape every backslash "
        "(write \\\\frac and \\\\|, for example)."
    ),
    "quiz_user": (
        "Generate $count multiple-choice questions from the notes below.\n"
        "The JSON format must be exactly:\n"
        "[\n"
        "    {\n"
        '        "question": "the question",\n'
        '        "options": ["A. first option", "B. second option", "C. third option", "D. fourth option"],\n'
        '        "answer": "A. first option",\n'
        '        "explanation": "why that answer is correct"\n'
        "    }\n"
        "]\n"
        "\n"
        "Notes:\n"
        "$contents"
    ),
    "summary_system": (
        "You are a study assistant. Based on the notes, output a JSON object: "
        '{"summary": "a structured summary in markdown", "key_concepts": ["concept 1", ...], '
        '"suggested_review_focus": ["what to review"]}. Output JSON only.'
    ),
    "summary_user": "Notes:\n$contents",
    "explain_system": (
        "You are a teacher who uses the Feynman technique. Explain the concept in the "
        "plainest language possible, covering all of: a simple explanation, an analogy, "
        "a concrete example, and related concepts. Output only a JSON object, with no "
        "extra text."
    ),
    "explain_user": "Explain this concept: $concept",
    "cross_ref_system": "You are a knowledge-graph assistant. For each pair of notes, write one sentence explaining how they relate. Output a JSON array.",
    "cross_ref_user": (
        'The note "$title" relates to the following notes:\n'
        "$titles\n"
        'Output [{"title": ..., "reason": "..."}]'
    ),
    "relevance_high": "high",
    # ---------- tools: error messages (they reach the model and may reach the UI) ----------
    "err_notes_not_found": "No usable notes were found",
    "err_note_ids_empty": "note_ids cannot be empty",
    "err_note_missing": "Note not found",
    "err_quiz_not_array": "The model did not return an array of questions",
    "err_not_json_object": "The model did not return a JSON object",
    # ---------- API layer ----------
    "err_session_missing": "Session not found",
    "err_goal_empty": "The learning goal cannot be empty",
    "err_agent_failed": "Agent run failed: $error",
}
