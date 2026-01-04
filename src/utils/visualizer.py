import matplotlib.pyplot as plt
import numpy as np
import os
import io
import base64
import json
import re
from PIL import Image
from playwright.sync_api import sync_playwright
from huggingface_hub import InferenceClient


def generate_chakra_plot(current_vals, ideal_vals, user_id):
    """ Generates a dual-layered Spider (Radar) Graph. """
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
    ax.set_facecolor('none')

    plt.legend(loc='upper right', bbox_to_anchor=(1.2, 1.1))

    output_dir = "data/plots"
    os.makedirs(output_dir, exist_ok=True)
    file_path = f"{output_dir}/chakra_{user_id}.png"

    plt.savefig(file_path, transparent=True, bbox_inches='tight')
    plt.close()

    return file_path


def generate_identity_card(user_id, data, social_json):
    # 1. Parse JSON safely
    try:
        json_match = re.search(r'\{.*\}', social_json, re.DOTALL)
        if json_match:
            meta = json.loads(json_match.group())
        else:
            raise ValueError("No JSON found")
    except Exception as e:
        print(f"JSON Parse Error: {e}")
        meta = {
            "archetype": "THE ASCENDANT",
            "quest_line": "Mastering every domain to reach unparalleled heights.",
            "theme": "CYBERPUNK",
            "image_prompt": "Futuristic anime warrior surrounded by glowing data shards, hyper-realistic, 8k"
        }

    stats = data['current_status']

    # 2. Generate Image via HuggingFace
    client = InferenceClient(token=os.getenv("HF_TOKEN"))
    try:
        image = client.text_to_image(
            meta['image_prompt'],
            model="stabilityai/stable-diffusion-xl-base-1.0"
        )
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        hero_image_src = f"data:image/png;base64,{img_str}"
    except Exception as e:
        print(f"HF Image Gen Error: {e}")
        hero_image_src = "https://via.placeholder.com/600x400/000000/FFFFFF?text=IDENTITY+CORE"

    # 3. Futuristic HTML Template
    # Changes: Added scanlines, glow effects, and precision layout to remove blank space
    html_content = f"""
    <html>
    <head>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;900&family=Inter:wght@300;900&display=swap" rel="stylesheet">
        <style>
            body {{ margin: 0; padding: 0; background-color: transparent; }}
            .tech-font {{ font-family: 'Orbitron', sans-serif; }}
            .card-bg {{ 
                background: {get_theme_gradient(meta.get('theme', 'CYBERPUNK'))};
                box-shadow: inset 0 0 100px rgba(0,0,0,0.8);
            }}
            .scanline {{
                width: 100%; height: 2px; background: rgba(16, 185, 129, 0.1);
                position: absolute; z-index: 20; animation: scan 4s linear infinite;
            }}
            @keyframes scan {{ from {{ top: 0; }} to {{ top: 100%; }} }}
            .glass {{ background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); }}
            .glow-text {{ text-shadow: 0 0 10px rgba(16, 185, 129, 0.8); }}
        </style>
    </head>
    <body>
        <div id="card" class="w-[600px] h-[900px] card-bg p-10 flex flex-col items-center border-[1px] border-emerald-500/30 relative overflow-hidden">
            <div class="scanline"></div>

            <div class="absolute top-0 left-0 w-8 h-8 border-t-2 border-l-2 border-emerald-500"></div>
            <div class="absolute bottom-0 right-0 w-8 h-8 border-b-2 border-r-2 border-emerald-500"></div>

            <div class="relative w-full h-72 mb-8 mt-4">
                <div class="absolute -inset-1 bg-emerald-500/20 blur-sm rounded-xl"></div>
                <img src="{hero_image_src}" class="relative w-full h-full object-cover rounded-xl border border-white/20 shadow-2xl">
            </div>

            <div class="text-center mb-8">
                <p class="text-emerald-500 text-[10px] tracking-[0.5em] uppercase font-bold mb-2">Protocol 2026 // Auth_Confirmed</p>
                <h1 class="tech-font text-5xl text-white uppercase tracking-tighter glow-text">{meta.get('archetype', 'ASCENDANT')}</h1>
                <div class="h-[1px] w-48 bg-gradient-to-r from-transparent via-emerald-500 to-transparent mx-auto mt-2"></div>
            </div>

            <div class="grid grid-cols-2 gap-4 w-full mb-10">
                {render_stat("Career/Finance", stats.get('career_finance', 0), "POWER")}
                {render_stat("Health", stats.get('health_fitness', 0), "VITALITY")}
                {render_stat("Personal Growth", stats.get('personal_growth_learning', 0), "WISDOM")}
                {render_stat("Spirituality", stats.get('spirituality_inner_peace', 0), "SPIRIT")}
            </div>

            <div class="mt-auto w-full text-center">
                <div class="glass p-6 rounded-2xl border-emerald-500/20">
                    <p class="text-slate-300 text-sm italic leading-relaxed">"{meta.get('quest_line', '')}"</p>
                </div>
                <div class="mt-8 flex justify-between items-center opacity-30">
                    <span class="text-[8px] tracking-widest text-white uppercase">SATH-CHAKRA AI SYSTEM</span>
                    <span class="text-[8px] tracking-widest text-white uppercase">v2.0.26_STABLE</span>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    # 4. Render to PNG with precise viewport clipping
    output_dir = "data/shares"
    os.makedirs(output_dir, exist_ok=True)
    path = f"{output_dir}/share_{user_id}.png"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        # Ensure the viewport matches the card div exactly
        page = browser.new_page(viewport={"width": 600, "height": 900})
        page.set_content(html_content)

        # Wait for fonts and base64 image to render
        page.wait_for_load_state("networkidle")

        # Screenshot specific element to eliminate blank space
        page.locator("#card").screenshot(path=path, omit_background=True)
        browser.close()

    return path


def render_stat(label, value, tech_label):
    try:
        val = int(value)
    except:
        val = 0

    # Technical progress bar look
    bars = "".join([
        f'<div class="h-2 w-full {"bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]" if i < val else "bg-white/10"} rounded-sm"></div>'
        for i in range(10)
    ])

    return f"""
    <div class="glass p-4 rounded-xl border-l-4 border-emerald-500/50">
        <div class="flex justify-between items-end mb-2">
            <p class="text-[8px] font-bold text-emerald-500 uppercase tracking-tighter">{tech_label}</p>
            <p class="text-[10px] text-white/50">{label}</p>
        </div>
        <div class="flex gap-[2px]">
            {bars}
        </div>
    </div>
    """

def get_theme_gradient(theme):
    themes = {
        "GREEK_MYTH": "radial-gradient(circle at 50% 30%, #1e293b 0%, #020617 100%)",
        "SHONEN_ANIME": "linear-gradient(135deg, #312e81 0%, #0f172a 100%)",
        "CYBERPUNK": "linear-gradient(to bottom, #111827, #000000)",
        "STOIC": "linear-gradient(to bottom, #374151, #111827)"
    }
    return themes.get(theme, themes["STOIC"])