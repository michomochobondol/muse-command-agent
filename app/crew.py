"""Orkestrator CrewAI - ini "kantor" tempat agen bekerja."""

import os
from crewai import Agent, Task, Crew, Process, LLM
from app.tools import scrape_website_tool, write_file_tool

# Workaround bug CrewAI: mark_cache_breakpoint() disuntik ke semua message
# untuk semua provider, tapi cuma Anthropic yang support. Groq nolak dengan
# error "property 'cache_breakpoint' is unsupported".
# Patch ini bikin fungsinya jadi no-op di semua tempat yang mengimpornya,
# karena ada modul yang pakai `from ... import mark_cache_breakpoint`
# (referensi langsung, tidak lewat atribut modul).
# Lihat crewaiinc/crewai#5886.
def _disable_crewai_cache_breakpoint():
    import sys
    import crewai.llms.cache as _cache_mod

    _orig = _cache_mod.mark_cache_breakpoint
    _noop = lambda msg: msg  # noqa: E731
    _cache_mod.mark_cache_breakpoint = _noop
    for _mod in list(sys.modules.values()):
        try:
            if getattr(_mod, "mark_cache_breakpoint", None) is _orig:
                _mod.mark_cache_breakpoint = _noop
        except Exception:
            pass


_disable_crewai_cache_breakpoint()


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
