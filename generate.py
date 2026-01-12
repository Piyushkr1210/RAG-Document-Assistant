def generate_answer(query, retrieved):
    """
    Generates an evidence-grounded answer.
    Refuses to answer if no valid evidence exists.
    """

    # 1️⃣ No evidence → refuse
    if not retrieved:
        return "❌ Cannot answer. No evidence found."

    # 2️⃣ Detect cross-modal conflict
    modalities = set(r["type"] for r in retrieved)
    conflict_detected = len(modalities) > 1

    # 3️⃣ Build answer header
    answer = "📌 Evidence-Grounded Response\n\n"

    if conflict_detected:
        answer += (
            "⚠️ **Cross-modal conflict detected.**\n"
            "Evidence comes from multiple source types. Please verify sources.\n\n"
        )

    # 4️⃣ Add evidence snippets with citations
    answer += "### Retrieved Evidence:\n\n"

    for r in retrieved:
        snippet = r["content"][:250].replace("\n", " ")
        answer += (
            f"- **Source:** {r['type'].upper()} ({r['source']})\n"
            f"  > {snippet}...\n\n"
        )

    # 5️⃣ Safety footer
    answer += (
        "⚠️ This response is generated strictly from the retrieved evidence above.\n"
        "No external knowledge or assumptions were used."
    )

    return answer
