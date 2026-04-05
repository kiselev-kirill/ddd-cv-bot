import html


def render_markdown_to_html(markdown_text: str) -> str:
    lines = markdown_text.splitlines()
    rendered: list[str] = []

    for line in lines:
        if not line.strip():
            rendered.append("")
            continue

        stripped = line.strip()
        indent = len(line) - len(line.lstrip(" "))
        prefix = " " * min(indent, 4)

        if stripped.startswith("### "):
            rendered.append(f"<b>{html.escape(stripped[4:])}</b>")
            continue
        if stripped.startswith("## "):
            rendered.append(f"<b>{html.escape(stripped[3:])}</b>")
            continue
        if stripped.startswith("# "):
            rendered.append(f"<b>{html.escape(stripped[2:])}</b>")
            continue
        if stripped.startswith("- "):
            rendered.append(f"{prefix}• {html.escape(stripped[2:])}")
            continue

        rendered.append(f"{prefix}{html.escape(stripped)}")

    return "\n".join(rendered)
