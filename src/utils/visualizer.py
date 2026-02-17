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
    """
    Generates a shareable identity card PNG using Playwright.

    FIX NOTES (Railway/Container Deployment):
    1. Replaced 'networkidle' with 'domcontentloaded' + fixed wait to avoid CDN timeout.
    2. Replaced 'with sync_playwright()' context manager with manual lifecycle
       to prevent InvalidStateError on exception cleanup.
    3. Added --no-sandbox and container-safe Chromium flags.
    4. Inlined all CSS — removed Tailwind CDN and Google Fonts external dependencies.
    """
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

    # 3. FULLY SELF-CONTAINED HTML TEMPLATE
    # FIX: All CSS is inlined. No external CDN calls (Tailwind, Google Fonts).
    # This eliminates the networkidle timeout entirely.
    html_content = f"""
    <html>
    <head>
        <style>
            /* === BASE RESET & FONTS === */
            @import url('data:text/css,');
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ margin: 0; padding: 0; background-color: transparent; font-family: 'Segoe UI', Arial, sans-serif; }}

            /* === TECH FONT (fallback to system monospace if Orbitron unavailable) === */
            .tech-font {{ font-family: 'Courier New', 'Lucida Console', monospace; letter-spacing: 2px; }}

            /* === CARD LAYOUT === */
            .card {{
                width: 600px; height: 900px; position: relative; overflow: hidden;
                padding: 40px; display: flex; flex-direction: column; align-items: center;
                background: {get_theme_gradient(meta.get('theme', 'CYBERPUNK'))};
                box-shadow: inset 0 0 100px rgba(0,0,0,0.8);
                border: 1px solid rgba(16, 185, 129, 0.3);
            }}

            /* === SCANLINE ANIMATION === */
            .scanline {{
                width: 100%; height: 2px; background: rgba(16, 185, 129, 0.1);
                position: absolute; z-index: 20; animation: scan 4s linear infinite;
            }}
            @keyframes scan {{ from {{ top: 0; }} to {{ top: 100%; }} }}

            /* === GLASS EFFECT === */
            .glass {{
                background: rgba(255, 255, 255, 0.03);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.1);
            }}

            /* === GLOW TEXT === */
            .glow-text {{ text-shadow: 0 0 10px rgba(16, 185, 129, 0.8); }}

            /* === CORNER DECORATIONS === */
            .corner-tl {{ position: absolute; top: 0; left: 0; width: 32px; height: 32px; border-top: 2px solid #10b981; border-left: 2px solid #10b981; }}
            .corner-br {{ position: absolute; bottom: 0; right: 0; width: 32px; height: 32px; border-bottom: 2px solid #10b981; border-right: 2px solid #10b981; }}

            /* === HERO IMAGE === */
            .hero-wrapper {{ position: relative; width: 100%; height: 288px; margin-bottom: 32px; margin-top: 16px; }}
            .hero-glow {{ position: absolute; inset: -4px; background: rgba(16, 185, 129, 0.2); filter: blur(4px); border-radius: 12px; }}
            .hero-img {{ position: relative; width: 100%; height: 100%; object-fit: cover; border-radius: 12px; border: 1px solid rgba(255,255,255,0.2); }}

            /* === TITLE SECTION === */
            .title-section {{ text-align: center; margin-bottom: 32px; }}
            .title-protocol {{ color: #10b981; font-size: 10px; letter-spacing: 0.5em; text-transform: uppercase; font-weight: bold; margin-bottom: 8px; }}
            .title-name {{ font-size: 42px; color: white; text-transform: uppercase; letter-spacing: -1px; }}
            .title-divider {{ height: 1px; width: 192px; margin: 8px auto 0; background: linear-gradient(to right, transparent, #10b981, transparent); }}

            /* === STATS GRID === */
            .stats-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; width: 100%; margin-bottom: 40px; }}
            .stat-card {{ padding: 16px; border-radius: 12px; border-left: 4px solid rgba(16, 185, 129, 0.5); }}
            .stat-header {{ display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 8px; }}
            .stat-tech-label {{ font-size: 8px; font-weight: bold; color: #10b981; text-transform: uppercase; letter-spacing: -0.5px; }}
            .stat-label {{ font-size: 10px; color: rgba(255,255,255,0.5); }}
            .stat-bars {{ display: flex; gap: 2px; }}
            .bar {{ height: 8px; flex: 1; border-radius: 2px; }}
            .bar-filled {{ background: #10b981; box-shadow: 0 0 8px rgba(16, 185, 129, 0.8); }}
            .bar-empty {{ background: rgba(255, 255, 255, 0.1); }}

            /* === QUEST LINE === */
            .quest-wrapper {{ margin-top: auto; width: 100%; text-align: center; }}
            .quest-box {{ padding: 24px; border-radius: 16px; border-color: rgba(16, 185, 129, 0.2); }}
            .quest-text {{ color: #cbd5e1; font-size: 14px; font-style: italic; line-height: 1.6; }}

            /* === FOOTER === */
            .footer {{ margin-top: 32px; display: flex; justify-content: space-between; align-items: center; width: 100%; opacity: 0.3; }}
            .footer-text {{ font-size: 8px; letter-spacing: 0.15em; color: white; text-transform: uppercase; }}
        </style>
    </head>
    <body>
        <div id="card" class="card">
            <div class="scanline"></div>
            <div class="corner-tl"></div>
            <div class="corner-br"></div>

            <div class="hero-wrapper">
                <div class="hero-glow"></div>
                <img src="{hero_image_src}" class="hero-img">
            </div>

            <div class="title-section">
                <p class="title-protocol">Protocol 2026 // Auth_Confirmed</p>
                <h1 class="tech-font title-name glow-text">{meta.get('archetype', 'ASCENDANT')}</h1>
                <div class="title-divider"></div>
            </div>

            <div class="stats-grid">
                {render_stat("Career/Finance", stats.get('career_finance', 0), "POWER")}
                {render_stat("Health", stats.get('health_fitness', 0), "VITALITY")}
                {render_stat("Personal Growth", stats.get('personal_growth_learning', 0), "WISDOM")}
                {render_stat("Spirituality", stats.get('spirituality_inner_peace', 0), "SPIRIT")}
            </div>

            <div class="quest-wrapper">
                <div class="quest-box glass">
                    <p class="quest-text">"{meta.get('quest_line', '')}"</p>
                </div>
                <div class="footer">
                    <span class="footer-text">SATH-CHAKRA AI SYSTEM</span>
                    <span class="footer-text">v2.0.26_STABLE</span>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    # 4. Render to PNG — MANUAL PLAYWRIGHT LIFECYCLE (no context manager)
    output_dir = "data/shares"
    os.makedirs(output_dir, exist_ok=True)
    path = f"{output_dir}/share_{user_id}.png"

    playwright = None
    browser = None
    try:
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--single-process",
            ]
        )
        page = browser.new_page(viewport={"width": 600, "height": 900})
        page.set_content(html_content)

        # FIX: Use domcontentloaded + fixed delay instead of networkidle.
        # Since HTML is now fully self-contained (no external CDN calls),
        # we only need the DOM to be parsed + a brief render settle time.
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(2000)

        page.locator("#card").screenshot(path=path, omit_background=True)
        print(f"DEBUG: Identity card generated at {path}")
        return path

    except Exception as e:
        print(f"Playwright card generation failed: {e}")
        return None
    finally:
        # FIX: Manual cleanup prevents InvalidStateError cascade
        try:
            if browser:
                browser.close()
        except Exception:
            pass
        try:
            if playwright:
                playwright.stop()
        except Exception:
            pass


def render_stat(label, value, tech_label):
    try:
        val = int(value)
    except (TypeError, ValueError):
        val = 0

    bars = "".join([
        f'<div class="bar {"bar-filled" if i < val else "bar-empty"}"></div>'
        for i in range(10)
    ])

    return f"""
    <div class="stat-card glass">
        <div class="stat-header">
            <p class="stat-tech-label">{tech_label}</p>
            <p class="stat-label">{label}</p>
        </div>
        <div class="stat-bars">
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
