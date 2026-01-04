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
            "archetype": "The Awakened Path",
            "quest_line": "Forging a legacy of balance and growth.",
            "theme": "STOIC",
            "image_prompt": "Illustration of a stoic philosopher in ancient setting"
        }

    stats = data['current_status']

    # 2. Generate Image & Convert to Base64 (Fixes Path Issues)
    client = InferenceClient(token=os.getenv("HF_TOKEN"))
    try:
        # Returns a PIL Image object
        image = client.text_to_image(
            meta['image_prompt'],
            model="stabilityai/stable-diffusion-xl-base-1.0"
        )

        # Save to buffer directly (skip disk to avoid path issues)
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        hero_image_src = f"data:image/png;base64,{img_str}"

    except Exception as e:
        print(f"HF Image Gen Error: {e}")
        # Fallback 1x1 pixel transparent or placeholder
        hero_image_src = "https://via.placeholder.com/600x300?text=Hero+Image"

    html_content = f"""
    <html>
    <head>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@900&family=Inter:wght@400;900&display=swap" rel="stylesheet">
        <style>
            .mythic-font {{ font-family: 'Cinzel', serif; }}
            .card-bg {{ background: {get_theme_gradient(meta.get('theme', 'STOIC'))}; }}
        </style>
    </head>
    <body class="bg-black flex items-center justify-center m-0 p-0">
        <div id="card" class="w-[600px] h-[900px] card-bg p-12 flex flex-col justify-between border-[12px] border-white/10 relative overflow-hidden">
            <div class="absolute top-0 left-0 w-full h-full opacity-20 pointer-events-none" 
                 style="background-image: radial-gradient(circle, #ffffff 1px, transparent 1px); background-size: 20px 20px;">
            </div>

            <img src="{hero_image_src}" alt="Archetype" class="w-full h-64 object-cover rounded-xl border border-white/20 shadow-2xl z-10 mb-6">

            <div class="text-center z-10">
                <h1 class="mythic-font text-4xl text-emerald-400 uppercase tracking-tighter mb-2 drop-shadow-lg">{meta.get('archetype', 'Unknown')}</h1>
                <p class="text-white/40 text-[10px] font-black tracking-[0.4em] uppercase">2026 Identity Artifact</p>
            </div>

            <div class="grid grid-cols-2 gap-4 z-10 my-4">
                {render_stat("⚔ POWER", stats.get('career_finance', 0))}
                {render_stat("❤️ VITALITY", stats.get('health_fitness', 0))}
                {render_stat("🧠 WISDOM", stats.get('personal_growth_learning', 0))}
                {render_stat("🔮 SPIRIT", stats.get('spirituality_inner_peace', 0))}
            </div>

            <div class="space-y-6 z-10 text-center mt-auto">
                <p class="italic text-slate-300 text-lg leading-relaxed px-4 font-serif">"{meta.get('quest_line', '')}"</p>
                <div class="pt-6 border-t border-white/10 font-black text-[10px] tracking-[0.4em] text-white/20 uppercase">
                    SATH-CHAKRA AI · PROTOCOL 2026
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    # 3. Render HTML to PNG
    output_dir = "data/shares"
    os.makedirs(output_dir, exist_ok=True)
    path = f"{output_dir}/share_{user_id}.png"

    with sync_playwright() as p:
        # Note: You may need to run 'playwright install chromium' in your Dockerfile/deployment
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 600, "height": 900})
        page.set_content(html_content)
        page.locator("#card").screenshot(path=path)
        browser.close()

    return path


def render_stat(label, value):
    # Safe convert to int just in case
    try:
        val = int(value)
    except:
        val = 0

    return f"""
    <div class="bg-black/40 border border-white/5 p-3 rounded-xl backdrop-blur-sm">
        <p class="text-[9px] font-black text-slate-400 mb-1 uppercase tracking-wider">{label}</p>
        <div class="flex gap-1">
            {"".join(['<div class="h-1.5 w-full bg-emerald-500 rounded-full shadow-[0_0_5px_rgba(16,185,129,0.5)]"></div>' if i < val else '<div class="h-1.5 w-full bg-white/5 rounded-full"></div>' for i in range(10)])}
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