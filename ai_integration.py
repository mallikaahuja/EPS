import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

# 1. Attribute suggestion for material, pressure, temp, etc.
def ai_suggest_attribute(prompt: str, fallback: str = "Unknown") -> str:
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert in process and instrumentation engineering."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=30,
            temperature=0.2
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[AI Attribute Fallback] {prompt} -> {fallback} (Error: {e})")
        return fallback

# 2. Recommend how to improve efficiency, safety, or sustainability
def ai_suggest_recommendations(component_summary: str, goal: str = "efficiency") -> str:
    try:
        prompt = (
            f"You are a senior chemical engineer. Given this process component or system:\n"
            f"'{component_summary}', suggest improvements to its {goal} in under 80 words."
        )
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You provide actionable P&ID design improvements."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.4
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[No suggestion available: {e}]"

# 3. Summarize what a component does in plain English
def ai_generate_summary(component: dict) -> str:
    try:
        desc = component.get("attributes", {}).get("description", "")
        subtype = component.get("subtype", "")
        tag = component.get("tag", "")
        prompt = (
            f"What is the function of this component in a vacuum system?\n\n"
            f"Tag: {tag}\nSubtype: {subtype}\nDescription: {desc}"
        )
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Explain P&ID components clearly to junior engineers."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=80,
            temperature=0.5
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception:
        return "This component regulates flow, pressure, or temperature in the vacuum process."

# 4. Suggest a clean 2D layout order of components
def ai_suggest_layout_sequence(component_tags: list) -> str:
    try:
        prompt = (
            f"Given the following components in a vacuum system:\n"
            f"{', '.join(component_tags)}\n"
            f"Suggest an optimal left-to-right process layout to minimize piping overlap."
        )
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You're an expert in industrial process layouts."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.3
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return "[AI layout suggestion unavailable]"

# 5. Audit for design issues (missing instruments, risky flows, etc.)
def ai_audit_safety_or_instrumentation(dsl_dict: dict) -> str:
    try:
        prompt = (
            f"Here is a simplified P&ID model as JSON:\n"
            f"{str(dsl_dict)[:2000]}\n"
            f"Review this process diagram and identify any missing safety valves, sensors, or potential risks."
        )
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You're a safety engineer reviewing P&IDs."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.4
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[Safety review failed: {e}]"

# 6. AI checklist for design quality (for final QA before export)
def ai_design_review_checklist(dsl_dict: dict) -> str:
    try:
        prompt = (
            f"As a senior process engineer, evaluate this P&ID design (truncated view):\n"
            f"{str(dsl_dict)[:2000]}\n"
            f"Give a checklist of 5 things this design gets right and 5 things that should be improved."
        )
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You provide critical process design QA feedback."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.4
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[Design review unavailable: {e}]"
