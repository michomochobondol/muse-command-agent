"""Orkestrator CrewAI - ini "kantor" tempat agen bekerja."""

import os
from crewai import Agent, Task, Crew, Process, LLM
from app.tools import scrape_website_tool, write_file_tool


def get_llm() -> LLM:
    """LLM via Groq (free tier, OpenAI-compatible)."""
    return LLM(
        model=os.getenv("GROQ_MODEL", "groq/openai/gpt-oss-120b"),
        api_key=os.getenv("GROQ_API_KEY"),
    )


def build_crew(objective: str) -> Crew:
    llm = get_llm()

    researcher = Agent(
        role="Researcher",
        goal="Mengumpulkan data faktual dari web terkait objektif",
        backstory=(
            "Peneliti yang teliti, selalu verifikasi sumber "
            "dan mengutip URL asal data."
        ),
        tools=[scrape_website_tool],
        llm=llm,
        verbose=True,
    )

    writer = Agent(
        role="Writer",
        goal="Menyusun hasil riset jadi ringkasan yang jelas",
        backstory=(
            "Penulis yang bisa menjelaskan hal kompleks "
            "dengan bahasa sederhana."
        ),
        tools=[write_file_tool],
        llm=llm,
        verbose=True,
    )

    research_task = Task(
        description=(
            f"Kumpulkan data faktual tentang: {objective}. "
            "Gunakan tool scrape_website jika butuh data dari URL. "
            "Kembalikan poin-poin fakta beserta sumber URL-nya."
        ),
        expected_output="Kumpulan fakta poin-poin dengan sumber URL.",
        agent=researcher,
    )

    write_task = Task(
        description=(
            "Susun hasil riset jadi ringkasan Bahasa Indonesia yang rapi "
            "dalam format markdown."
        ),
        expected_output="Ringkasan markdown dalam Bahasa Indonesia.",
        agent=writer,
    )

    crew = Crew(
        agents=[researcher, writer],
        tasks=[research_task, write_task],
        process=Process.sequential,
        verbose=True,
    )
    return crew
