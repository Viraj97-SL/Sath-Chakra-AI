import matplotlib.pyplot as plt
import numpy as np
import os
from PIL import Image, ImageDraw, ImageFont
import json
import re
from playwright.sync_api import sync_playwright

def generate_chakra_plot(current_vals, ideal_vals, user_id):
    """ Generates a dual-layered Spider (Radar) Graph. Refers to: Strategic alignment of life dimensions. """
    labels = [
        'Career/Finance', 'Health', 'Relationships', 'Spirituality',
        'Growth', 'Fun', 'Environment', 'Legacy'
    ]
    num_vars = len(labels)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]

    def close_loop(data):
        return data + data[:1]

    # Use a transparent background for social media overlay
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)

    ax.plot(angles, close_loop(ideal_vals), color='#2ecc71', linewidth=3, label='Ideal Identity')
    ax.fill(angles, close_loop(ideal_vals), color='#2ecc71', alpha=0.2)

    ax.plot(angles, close_loop(current_vals), color='#e74c3c', linewidth=3, label='Current Status')
    ax.fill(angles, close_loop(current_vals), color='#e74c3c', alpha=0.4)

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_thetagrids(np.degrees(angles[:-1]), labels, color="white", fontweight='bold')
    ax.set_ylim(0, 10)

    # Hide standard grids for a cleaner "Game Stats" look
    ax.set_facecolor('none')

    plt.legend(loc='upper right', bbox_to_anchor=(1.2, 1.1))

    output_dir = "data/plots"
    os.makedirs(output_dir, exist_ok=True)
    file_path = f"{output_dir}/chakra_{user_id}.png"

    # Transparent save is critical for the social card compositor
    plt.savefig(file_path, transparent=True, bbox_inches='tight')
    plt.close()

    return file_path

def generate_identity_card(user_id, data, social_json):
    # Use Regex to extract only the content between curly braces
    try:
        json_match = re.search(r'\{.*\}', social_json, re.DOTALL)
        if json_match:
            meta = json.loads(json_match.group())
        else:
            raise ValueError("No JSON found in social_copy")
    except Exception as e:
        print(f"JSON Parse Error: {e}")
        # Fallback defaults to prevent 500 error
        meta = {
            "archetype": "The Awakened Path",
            "quest_line": "Forging a legacy of balance and growth.",
            "theme": "STOIC"
        }

    stats = data['current_status']

    html_content = f"""
    <html>
    <head>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@900&family=Inter:wght@400;900&display=swap" rel="stylesheet">
        <style>
            .mythic-font {{ font-family: 'Cinzel', serif; }}
            .card-bg {{ background: {get_theme_gradient(meta['theme'])}; }}
        </style>
    </head>
    <body class="bg-black flex items-center justify-center m-0 p-0">
        <div id="card" class="w-[600px] h-[900px] card-bg p-12 flex flex-col justify-between border-[12px] border-white/10 relative overflow-hidden">
            <div class="absolute top-0 left-0 w-full h-full opacity-20 pointer-events-none">
                <svg width="100%" height="100%"><rect width="100%" height="100%" fill="url(#grid)" /></svg>
            </div>
            <div class="text-center z-10">
                <h1 class="mythic-font text-5xl text-emerald-400 uppercase tracking-tighter mb-2">{meta['archetype']}</h1>
                <p class="text-white/40 text-xs font-black tracking-[0.4em] uppercase">2026 Identity Artifact</p>
            </div>
            <div class="grid grid-cols-2 gap-6 z-10">
                {render_stat("⚔ POWER", stats['career_finance'])}
                {render_stat("❤️ VITALITY", stats['health_fitness'])}
                {render_stat("🧠 WISDOM", stats['personal_growth_learning'])}
                {render_stat("🔮 SPIRIT", stats['spirituality_inner_peace'])}
            </div>
            <div class="space-y-8 z-10 text-center">
                <p class="italic text-slate-300 text-xl leading-relaxed px-4">"{meta['quest_line']}"</p>
                <div class="pt-8 border-t border-white/10 font-black text-[10px] tracking-[0.5em] text-white/20 uppercase">
                    SATH-CHAKRA AI · PROTOCOL 2026
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    # Render HTML to PNG using Playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 600, "height": 900})
        page.set_content(html_content)
        path = f"data/shares/share_{user_id}.png"
        page.locator("#card").screenshot(path=path)
        browser.close()

    return path

def render_stat(label, value):
    return f"""
    <div class="bg-black/40 border border-white/5 p-4 rounded-2xl">
        <p class="text-[9px] font-black text-slate-500 mb-2">{label}</p>
        <div class="flex gap-1">
            {"".join(['<div class="h-1.5 w-full bg-emerald-500 rounded-full"></div>' if i < value else '<div class="h-1.5 w-full bg-white/5 rounded-full"></div>' for i in range(10)])}
        </div>
    </div>
    """

def get_theme_gradient(theme):
    themes = {
        "GREEK_MYTH": "radial-gradient(circle at 50% 50%, #064e3b 0%, #022c22 100%)",
        "SHONEN_ANIME": "linear-gradient(135deg, #4c1d95 0%, #1e1b4b 100%)",
        "CYBERPUNK": "linear-gradient(to bottom, #111827, #000000)",
        "STOIC": "linear-gradient(to bottom, #1f2937, #111827)"
    }
    return themes.get(theme, themes["STOIC"])