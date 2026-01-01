import os
from typing import TypedDict
# from langchain_google_genai import ChatGoogleGenerativeAI  # Gemini import
from langchain_groq import ChatGroq  # Added for Groq integration
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
from typing import TypedDict, Annotated

load_dotenv()

class AgentState(TypedDict):
    user_data: dict
    analysis_report: str
    action_plan: str
    language: str
    social_copy: str


# 2. Updated Analyzer Node for Groq (Llama 3)
def analyzer_node(state: AgentState):
    """Analyzes life dimensions using Groq Llama 3."""

    # --- GEMINI VERSION (Commented Out) ---
    # llm = ChatGoogleGenerativeAI(
    #     model="gemini-2.5-flash",
    #     temperature=0.7,
    #     google_api_key=os.getenv("GOOGLE_API_KEY")
    # )

    # --- GROQ VERSION (Active) ---
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.75,  # Increased slightly for better descriptive flow
        max_tokens=3096,  # Critical: Allows the full long-form response
        groq_api_key=os.getenv("GROQ_API_KEY")
    )

    prompt = f"""
    ඔබ ඉතා අත්දැකීම් බහුල මනෝවිද්‍යාඥයෙකු සහ ජීවන උපදේශකයෙකු ලෙස ක්‍රියා කරන්න. 
    (Act as a highly experienced psychologist and life coach).

    පහත දත්ත මත පදනම්ව අතිශය ගැඹුරු, විද්‍යාත්මක සහ දීර්ඝ (වචන 500-800 අතර) ජීවන චක්‍ර විශ්ලේෂණයක් සිදු කරන්න:

    පරිශීලක දත්ත:
    - වර්තමාන තත්ත්වය: {state['user_data']['current_status']}
    - අපේක්ෂිත අනන්‍යතාවය (2026): {state['user_data']['ideal_identity']}
    - සන්දර්භය: වයස {state['user_data']['age']}, රැකියාව: {state['user_data']['job_status']}

    කරුණාකර ඔබේ වාර්තාව මෙම අංශ ඔස්සේ සවිස්තරාත්මකව සකසන්න:

    1. **වර්තමාන ජීවන තත්ත්වය පිළිබඳ සවිස්තරාත්මක විග්‍රහය:** එක් එක් ක්ෂේත්‍රය (Career, Health, etc.) වෙන වෙනම ගෙන ඒවායේ වර්තමාන මට්ටම පරිශීලකයාගේ වයසට සහ රැකියාවට බලපාන ආකාරය විස්තර කරන්න.
    2. **අසමතුලිතතාවය (Eccentricity) සහ එහි බලපෑම:** ජීවන රෝදය අසමතුලිත වීම නිසා ඇතිවන මානසික ආතතිය සහ අනාගතයට ඇති අවදානම විද්‍යාත්මකව පැහැදිලි කරන්න.
    3. **'Legacy' සහ 'Strategic Alignment' ගැඹුරු විශ්ලේෂණය:** පරිශීලකයාගේ ඉහළ අභිලාෂයන් සහ ඔවුන් තැබීමට බලාපොරොත්තු වන 'Legacy' එක අතර ඇති සම්බන්ධය සහ ඒවා එකිනෙකට සමපාත (Align) කරන ආකාරය විස්තර කරන්න.
    4. **මනෝවිද්‍යාත්මක උපදෙස් සහ ක්‍රියාකාරී සැලැස්ම:** අවම වශයෙන් උපදෙස් 7-10ක් ලබාදෙන්න. සෑම උපදෙසක්ම 'මනෝවිද්‍යාත්මක පදනම' සහ 'ප්‍රායෝගිකව කළ යුතු දේ' ලෙස කොටස් දෙකකින් දක්වන්න.

    භාෂාව: {state['language']} (සිංහල)
    වාර්තාවේ ස්වරය: වෘත්තීය, දිරිමත් කරන සුළු සහ ඉතා පැහැදිලි විය යුතුය.
    """

    response = llm.invoke([HumanMessage(content=prompt)])
    return {"analysis_report": response.content}



def strategist_node(state: AgentState):
    """Generates a tactical 2026 roadmap."""
    # --- GEMINI VERSION ---
    # llm = ChatGoogleGenerativeAI(
    #     model="gemini-2.5-flash",
    #     temperature=0.3,
    #     google_api_key=os.getenv("GOOGLE_API_KEY")
    # )

    # --- GROQ VERSION ---
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        groq_api_key=os.getenv("GROQ_API_KEY")
    )

    prompt = f"""
        පහත විශ්ලේෂණය මත පදනම්ව 2026 වසර සඳහා 'Success Path' එකක් සකසන්න:
        විශ්ලේෂණය: {state['analysis_report']}

        සැලැස්ම පහත පරිදි සකස් කරන්න:
        1. පළමු මාස 3: අත්තිවාරම දැමීම (Quick Wins).
        2. මාස 6-9: වර්ධනය සහ අනුකූලතාවය (Consistency).
        3. මාස 12: සමාලෝචනය සහ ඊළඟ වසර සඳහා සැලසුම් කිරීම.
        4. සෑම පියවරකටම මනෝවිද්‍යාත්මක 'Nudge' එකක් ඇතුළත් කරන්න.

        සියලුම කරුණු {state['language']} භාෂාවෙන් සරලව සහ පැහැදිලිව ලබාදෙන්න.
        """

    response = llm.invoke([HumanMessage(content=prompt)])
    return {"action_plan": response.content}


# 3. Event Planner Node
def event_planner_node(state: AgentState):
    """Extracts 3-month check-in dates and milestones for the calendar."""
    # --- GEMINI VERSION ---
    # llm = ChatGoogleGenerativeAI(
    #     model="gemini-2.5-flash",
    #     temperature=0.1,
    #     google_api_key=os.getenv("GOOGLE_API_KEY")
    # )

    # --- GROQ VERSION ---
    llm = ChatGroq(
        model="llama-3.1-8b-instant", # Llama 8B is faster for extraction tasks
        temperature=0.1,
        groq_api_key=os.getenv("GROQ_API_KEY")
    )

    prompt = f"""
    Based on this 2026 Action Plan: {state['action_plan']}

    Identify 4 specific dates for "3-Month Re-checks" starting from Jan 2026.
    Return the output ONLY as a list of events in this format:
    DATE: YYYY-MM-DD | TITLE: [Event Name]
    """

    response = llm.invoke([HumanMessage(content=prompt)])
    return {"action_plan": state['action_plan'] + "\n\n### Calendar Milestones\n" + response.content}


def social_media_node(state: AgentState):
    """Acts as the Game Master to define the user's 2026 Mythic Identity."""
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0.8,
        groq_api_key=os.getenv("GROQ_API_KEY")
    )

    prompt = f"""
    Analyze these life gaps (Current vs Ideal): {state['user_data']}

    Task: Define a 2026 Mythic Identity Card.
    1. Choose an Archetype (e.g., The Phoenix, The Relentless Builder, The Balanced Guardian).
    2. Write a 'Quest Line' (1 sentence, epic tone): e.g., 'In 2026, you forge wealth without sacrificing inner peace.'
    3. Select a Theme: 'GREEK_MYTH', 'SHONEN_ANIME', 'CYBERPUNK', or 'STOIC'.

    Return ONLY a JSON object:
    {{
      "archetype": "string",
      "quest_line": "string",
      "theme": "string"
    }}
    """
    response = llm.invoke([HumanMessage(content=prompt)])
    # We store this JSON string to be parsed by the image generator
    return {"social_copy": response.content}

# 3. Update the Workflow Logic
workflow = StateGraph(AgentState)

# Nodes remain unchanged
workflow.add_node("analyze", analyzer_node)
workflow.add_node("strategize", strategist_node)
workflow.add_node("plan_events", event_planner_node)
workflow.add_node("social_media", social_media_node)

workflow.set_entry_point("analyze")
workflow.add_edge("analyze", "strategize")
workflow.add_edge("strategize", "plan_events")
workflow.add_edge("plan_events", "social_media")
workflow.add_edge("social_media", END)

chakra_agent = workflow.compile()