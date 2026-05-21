from backend.services.generator_service import generate_section

def research_agent(topic, context):
    return generate_section("Research Summary", topic, context)

def analysis_agent(topic, context):
    return generate_section("Analysis", topic, context)

def writer_agent(topic, context):
    sections = [
        "Abstract",
        "Introduction",
        "Literature Review",
        "Methodology",
        "Results",
        "Conclusion"
    ]

    content = {}

    for sec in sections:
        print(f"✍️ Generating {sec}...")
        content[sec] = generate_section(sec, topic, context)

    return content