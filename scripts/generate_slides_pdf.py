"""
World-Class Modern Pitch Deck Generator for REGRET
Matches contemporary brand design: Terracotta / Rust / Cream / Slate palette,
organic curved geometric accents, arched pill cards, donut payoff chart, and "R" logo.
Compiles pixel-perfect PDF via Edge headless engine.
"""

import subprocess
import sys
from pathlib import Path

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>REGRET — Autonomous AI Options Trading Pitch Deck</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;0,9..144,700;0,9..144,900;1,9..144,400;1,9..144,600&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --terracotta: #a63a2b;
            --terracotta-dark: #782417;
            --terracotta-soft: #c45b49;
            --cream: #f6f1e7;
            --cream-card: #ece4d2;
            --cream-border: #dcd1ba;
            --slate: #1c232d;
            --slate-card: #27313f;
            --slate-border: #384659;
            --ink: #191410;
            --oxblood: #8e2a24;
            --emerald: #246a48;
            --emerald-bg: #e5f2eb;
            --ochre: #c07a38;
            --font-display: 'Fraunces', Georgia, serif;
            --font-sans: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            --font-mono: 'JetBrains Mono', monospace;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
        body {
            font-family: var(--font-sans);
            background: #0d1117;
            color: var(--ink);
            margin: 0;
            padding: 0;
        }

        @page {
            size: 1920px 1080px;
            margin: 0;
        }

        .slide-deck {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 40px;
            padding: 40px 0;
        }

        .slide {
            width: 1920px;
            height: 1080px;
            position: relative;
            overflow: hidden;
            background: var(--cream);
            page-break-after: always;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            padding: 90px 110px;
        }

        @media print {
            .slide-deck { padding: 0; gap: 0; }
            .slide { box-shadow: none; }
            .no-print { display: none !important; }
        }

        /* Typography */
        .title-display {
            font-family: var(--font-display);
            font-weight: 700;
            letter-spacing: -0.02em;
            line-height: 1.05;
        }
        .mono { font-family: var(--font-mono); }

        /* Color Themes for Slides */
        .theme-terracotta {
            background: radial-gradient(1400px 900px at 15% 20%, #c45b49 0%, #8e2a24 60%, #5c1612 100%);
            color: #ffffff;
        }
        .theme-cream {
            background: #f7f2e8;
            color: var(--ink);
        }
        .theme-slate {
            background: radial-gradient(1400px 900px at 85% 15%, #2a3545 0%, #1a202a 60%, #11151c 100%);
            color: #ffffff;
        }

        /* Abstract Organic Background Shapes matching reference */
        .shape-blob-1 {
            position: absolute;
            width: 750px;
            height: 750px;
            border-radius: 50% 50% 0 50%;
            background: rgba(196, 91, 73, 0.18);
            filter: blur(10px);
            right: -120px;
            top: -120px;
            pointer-events: none;
        }
        .shape-blob-2 {
            position: absolute;
            width: 650px;
            height: 650px;
            border-radius: 50%;
            background: rgba(142, 42, 36, 0.15);
            filter: blur(40px);
            left: -150px;
            bottom: -150px;
            pointer-events: none;
        }
        .shape-arch {
            position: absolute;
            width: 420px;
            height: 560px;
            border-radius: 210px 210px 0 0;
            background: rgba(214, 114, 94, 0.25);
            right: 120px;
            bottom: 0;
            pointer-events: none;
        }
        .shape-curve-terracotta {
            position: absolute;
            width: 800px;
            height: 800px;
            border-radius: 0 400px 400px 0;
            background: rgba(42, 53, 69, 0.35);
            right: -100px;
            top: 140px;
            pointer-events: none;
        }

        /* R Logo Icon */
        .r-logo-box {
            display: inline-flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            width: 68px;
            height: 68px;
            border: 2px solid currentColor;
            border-radius: 12px;
            font-family: var(--font-display);
            font-weight: 700;
            font-size: 32px;
            line-height: 1;
            position: relative;
        }
        .r-logo-box .r-rule {
            width: 32px;
            height: 2.5px;
            background: currentColor;
            margin-top: 4px;
        }

        /* Header info */
        .slide-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: relative;
            z-index: 10;
        }
        .slide-badge {
            font-family: var(--font-sans);
            font-weight: 700;
            font-size: 14px;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            padding: 8px 18px;
            border-radius: 100px;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        .slide-badge.badge-light {
            background: rgba(255, 255, 255, 0.15);
            color: #ffffff;
            border: 1px solid rgba(255, 255, 255, 0.25);
        }
        .slide-badge.badge-dark {
            background: rgba(142, 42, 36, 0.1);
            color: var(--terracotta);
            border: 1px solid rgba(142, 42, 36, 0.2);
        }

        /* Arched Pill Cards from reference image */
        .arch-card {
            border-radius: 120px 120px 32px 32px;
            padding: 55px 35px 40px;
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            position: relative;
            transition: transform 0.2s;
        }
        .arch-card-cream {
            background: linear-gradient(180deg, rgba(236, 228, 210, 0.8) 0%, rgba(246, 241, 231, 0.95) 100%);
            border: 1.5px solid var(--cream-border);
        }
        .arch-card-terracotta {
            background: linear-gradient(180deg, rgba(196, 91, 73, 0.25) 0%, rgba(142, 42, 36, 0.4) 100%);
            border: 1.5px solid rgba(214, 114, 94, 0.4);
            color: #ffffff;
        }
        .arch-card-slate {
            background: linear-gradient(180deg, rgba(42, 53, 69, 0.85) 0%, rgba(26, 32, 42, 0.95) 100%);
            border: 1.5px solid var(--slate-border);
            color: #ffffff;
        }

        .icon-circle {
            width: 76px;
            height: 76px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 32px;
            margin-bottom: 24px;
        }

        /* Bento Grid Layouts */
        .bento-grid {
            display: grid;
            gap: 28px;
        }
        .bento-card {
            border-radius: 28px;
            padding: 36px 40px;
            position: relative;
            overflow: hidden;
        }

        /* Footer */
        .slide-footer {
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 14px;
            position: relative;
            z-index: 10;
            padding-top: 24px;
            border-top: 1px solid rgba(150, 150, 150, 0.2);
        }
    </style>
</head>
<body>

<div class="slide-deck">

    <!-- ========================================================================= -->
    <!-- SLIDE 1: COVER (Modern Business Strategy Aesthetic) -->
    <!-- ========================================================================= -->
    <div class="slide theme-terracotta">
        <div class="shape-curve-terracotta"></div>
        <div class="shape-blob-1" style="background: rgba(255,255,255,0.08);"></div>
        
        <div class="slide-header">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div class="r-logo-box" style="border-color: #ffffff; color: #ffffff;">
                    R
                    <div class="r-rule" style="background: #ffffff;"></div>
                </div>
                <div style="font-family: var(--font-display); font-size: 26px; font-weight: 700; letter-spacing: 0.15em; margin-left: 8px;">REGRET</div>
            </div>
            <div class="slide-badge badge-light">Alpaca AI Trading Agents Hackathon 2026</div>
        </div>

        <div style="max-width: 1100px; margin-top: 40px;">
            <div style="font-size: 20px; font-weight: 600; letter-spacing: 0.2em; text-transform: uppercase; color: #fbd5ce; margin-bottom: 16px;">Autonomous AI Quantitative System</div>
            <h1 class="title-display" style="font-size: 78px; margin-bottom: 28px; color: #ffffff;">
                Defined-Risk Options Trading With Zero Tail Risk
            </h1>
            <p style="font-size: 24px; line-height: 1.5; color: #fae2dd; max-width: 920px; font-weight: 400;">
                The next-generation trading agent combining <strong style="color: #fff; font-weight: 700;">Featherless AI qualitative market reasoning</strong> with <strong style="color: #fff; font-weight: 700;">deterministic Python mathematical risk bounds</strong>.
            </p>
        </div>

        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 24px; margin-top: 30px;">
            <div style="background: rgba(255,255,255,0.12); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.22); border-radius: 20px; padding: 22px 28px;">
                <div style="font-size: 38px; font-weight: 800; font-family: var(--font-mono); color: #fff;">$100,000</div>
                <div style="font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; color: #fcdcd6; margin-top: 4px;">Alpaca Paper Baseline</div>
            </div>
            <div style="background: rgba(255,255,255,0.12); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.22); border-radius: 20px; padding: 22px 28px;">
                <div style="font-size: 38px; font-weight: 800; font-family: var(--font-mono); color: #fff;">6 GATES</div>
                <div style="font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; color: #fcdcd6; margin-top: 4px;">Deterministic Safety</div>
            </div>
            <div style="background: rgba(255,255,255,0.12); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.22); border-radius: 20px; padding: 22px 28px;">
                <div style="font-size: 38px; font-weight: 800; font-family: var(--font-mono); color: #fff;">70-80%</div>
                <div style="font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; color: #fcdcd6; margin-top: 4px;">Target Spread Win Rate</div>
            </div>
            <div style="background: rgba(255,255,255,0.12); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.22); border-radius: 20px; padding: 22px 28px;">
                <div style="font-size: 38px; font-weight: 800; font-family: var(--font-mono); color: #fff;">0.0%</div>
                <div style="font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; color: #fcdcd6; margin-top: 4px;">Naked Loss Exposure</div>
            </div>
        </div>

        <div class="slide-footer" style="color: rgba(255,255,255,0.7); border-color: rgba(255,255,255,0.2);">
            <div>Live Alpaca Paper Account: <strong style="color: #fff; font-family: var(--font-mono);">PA3XUIGQ0VGB</strong></div>
            <div>REGRET · Project Pitch Deck</div>
            <div>Slide 01 of 08</div>
        </div>
    </div>


    <!-- ========================================================================= -->
    <!-- SLIDE 2: WHO WE ARE (Editorial Warm Layout) -->
    <!-- ========================================================================= -->
    <div class="slide theme-cream">
        <div class="shape-blob-1"></div>
        
        <div class="slide-header">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div class="r-logo-box" style="border-color: var(--ink); color: var(--oxblood);">
                    R
                    <div class="r-rule" style="background: var(--oxblood);"></div>
                </div>
                <div style="font-family: var(--font-display); font-size: 24px; font-weight: 700; letter-spacing: 0.12em; color: var(--ink);">REGRET</div>
            </div>
            <div class="slide-badge badge-dark">Who We Are</div>
        </div>

        <div style="display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 70px; align-items: center; margin: 30px 0;">
            <div>
                <h2 class="title-display" style="font-size: 60px; color: var(--ink); margin-bottom: 24px;">
                    Bridging AI Intelligence with Wall Street Guardrails
                </h2>
                <p style="font-size: 20px; line-height: 1.6; color: #52473b; margin-bottom: 24px;">
                    Modern traders face a dilemma: LLMs possess incredible macroeconomic synthesis and context parsing, yet they are mathematically brittle when calculating options Greeks and managing downside risk.
                </p>
                <p style="font-size: 20px; line-height: 1.6; color: #52473b;">
                    <strong>REGRET</strong> solves this by creating a hardened software barrier: AI generates the qualitative strategic thesis, while deterministic Python gates enforce 100% of the trade execution, Greek boundaries, and position limits.
                </p>
            </div>

            <div style="display: flex; flex-direction: column; gap: 20px;">
                <div class="bento-card" style="background: #efe7d7; border: 1.5px solid var(--cream-border);">
                    <div style="font-size: 14px; font-weight: 700; letter-spacing: 0.15em; text-transform: uppercase; color: var(--oxblood); margin-bottom: 8px;">Mission</div>
                    <div style="font-size: 20px; font-weight: 600; color: var(--ink); line-height: 1.4;">
                        To make quantitative, defined-risk options strategies autonomous, explainable, and mathematically protected against black-swan liquidation.
                    </div>
                </div>

                <div class="bento-card" style="background: #efe7d7; border: 1.5px solid var(--cream-border);">
                    <div style="font-size: 14px; font-weight: 700; letter-spacing: 0.15em; text-transform: uppercase; color: var(--ochre); margin-bottom: 8px;">Target Edge</div>
                    <div style="font-size: 20px; font-weight: 600; color: var(--ink); line-height: 1.4;">
                        Systematically harvesting elevated Implied Volatility overestimation and positive Theta time decay on high-volume indices and equities ($SPY, $QQQ, $NVDA).
                    </div>
                </div>
            </div>
        </div>

        <div class="slide-footer" style="color: #7a7164; border-color: var(--cream-border);">
            <div>Alpaca AI Trading Agents Hackathon</div>
            <div>Who We Are · Core Philosophy</div>
            <div>Slide 02 of 08</div>
        </div>
    </div>


    <!-- ========================================================================= -->
    <!-- SLIDE 3: THE CHALLENGE WE FACE (Arched Pill Cards from Reference) -->
    <!-- ========================================================================= -->
    <div class="slide theme-cream">
        <div class="shape-blob-2"></div>

        <div class="slide-header">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div class="r-logo-box" style="border-color: var(--ink); color: var(--oxblood);">
                    R
                    <div class="r-rule" style="background: var(--oxblood);"></div>
                </div>
                <div style="font-family: var(--font-display); font-size: 24px; font-weight: 700; letter-spacing: 0.12em; color: var(--ink);">REGRET</div>
            </div>
            <div class="slide-badge badge-dark">The Challenge</div>
        </div>

        <div style="text-align: center; max-width: 900px; margin: 10px auto 30px;">
            <h2 class="title-display" style="font-size: 54px; color: var(--ink); margin-bottom: 14px;">
                The 3 Critical Flaws in AI Trading Bots
            </h2>
            <p style="font-size: 19px; color: #6e6456;">
                Why conventional language model trading bots destroy Sharpe ratios and fail institutional risk audits.
            </p>
        </div>

        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 32px;">
            
            <!-- Arched Card 1 -->
            <div class="arch-card arch-card-cream">
                <div class="icon-circle" style="background: #f8ded9; color: var(--oxblood);">📐</div>
                <h3 style="font-size: 22px; font-weight: 700; color: var(--ink); margin-bottom: 14px; font-family: var(--font-display);">
                    Hallucinated Math
                </h3>
                <p style="font-size: 16px; line-height: 1.55; color: #5c5245;">
                    LLMs cannot reliably calculate real-time options Greeks (&Delta;, &Gamma;, &Theta;) or margin collateral inside prompt space, generating catastrophic sizing errors.
                </p>
            </div>

            <!-- Arched Card 2 -->
            <div class="arch-card arch-card-cream" style="border-color: rgba(166,58,43,0.3); background: #fdf5f3;">
                <div class="icon-circle" style="background: #f8ded9; color: var(--oxblood);">💥</div>
                <h3 style="font-size: 22px; font-weight: 700; color: var(--oxblood); margin-bottom: 14px; font-family: var(--font-display);">
                    Naked Tail Risk
                </h3>
                <p style="font-size: 16px; line-height: 1.55; color: #5c5245;">
                    Unconstrained agents execute naked short options without purchasing outer wings, creating unlimited loss liability on single-day market volatility surges.
                </p>
            </div>

            <!-- Arched Card 3 -->
            <div class="arch-card arch-card-cream">
                <div class="icon-circle" style="background: #f8ded9; color: var(--oxblood);">🔒</div>
                <h3 style="font-size: 22px; font-weight: 700; color: var(--ink); margin-bottom: 14px; font-family: var(--font-display);">
                    Black Box Fragility
                </h3>
                <p style="font-size: 16px; line-height: 1.55; color: #5c5245;">
                    End-to-end neural network bots provide zero explainability. When market regimes shift abruptly, unmonitored bots freeze or panic-sell at maximum drawdown.
                </p>
            </div>

        </div>

        <div class="slide-footer" style="color: #7a7164; border-color: var(--cream-border);">
            <div>The Problem We Solve</div>
            <div>Zero Unbounded Liability</div>
            <div>Slide 03 of 08</div>
        </div>
    </div>


    <!-- ========================================================================= -->
    <!-- SLIDE 4: HOW WE SOLVE IT (Dark Slate & Split Screen Layout) -->
    <!-- ========================================================================= -->
    <div class="slide theme-slate">
        <div class="shape-blob-1" style="background: rgba(56,189,248,0.08);"></div>

        <div class="slide-header">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div class="r-logo-box" style="border-color: #fff; color: #38bdf8;">
                    R
                    <div class="r-rule" style="background: #38bdf8;"></div>
                </div>
                <div style="font-family: var(--font-display); font-size: 24px; font-weight: 700; letter-spacing: 0.12em; color: #fff;">REGRET</div>
            </div>
            <div class="slide-badge badge-light">System Architecture</div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 60px; align-items: center; margin: 20px 0;">
            <div>
                <h2 class="title-display" style="font-size: 56px; color: #ffffff; margin-bottom: 20px;">
                    How We Solve It
                </h2>
                <p style="font-size: 19px; line-height: 1.6; color: #cbd5e1; margin-bottom: 30px;">
                    We created a strict separation of concerns that routes market intelligence through four hardened stages:
                </p>

                <div style="display: flex; flex-direction: column; gap: 16px;">
                    <div style="background: var(--slate-card); border: 1px solid var(--slate-border); border-radius: 16px; padding: 18px 24px; display: flex; gap: 16px; align-items: center;">
                        <span style="background: #38bdf8; color: #0f172a; font-weight: 800; border-radius: 8px; padding: 4px 10px; font-family: var(--font-mono); font-size: 13px;">01</span>
                        <div>
                            <div style="font-weight: 700; font-size: 16px; color: #fff;">Alpaca Market Data Screener</div>
                            <div style="font-size: 13px; color: #94a3b8;">Streams real-time stock bars & option chains. Computes 52-week IV Rank.</div>
                        </div>
                    </div>

                    <div style="background: var(--slate-card); border: 1px solid var(--slate-border); border-radius: 16px; padding: 18px 24px; display: flex; gap: 16px; align-items: center;">
                        <span style="background: #a855f7; color: #fff; font-weight: 800; border-radius: 8px; padding: 4px 10px; font-family: var(--font-mono); font-size: 13px;">02</span>
                        <div>
                            <div style="font-weight: 700; font-size: 16px; color: #fff;">Featherless AI Strategic Synthesis</div>
                            <div style="font-size: 13px; color: #94a3b8;">Qwen 2.5 72B & Llama 3.3 evaluate volatility skew and market regime bias.</div>
                        </div>
                    </div>

                    <div style="background: var(--slate-card); border: 1px solid var(--slate-border); border-radius: 16px; padding: 18px 24px; display: flex; gap: 16px; align-items: center;">
                        <span style="background: #34d399; color: #064e3b; font-weight: 800; border-radius: 8px; padding: 4px 10px; font-family: var(--font-mono); font-size: 13px;">03</span>
                        <div>
                            <div style="font-weight: 700; font-size: 16px; color: #fff;">6 Deterministic Hard Risk Gates</div>
                            <div style="font-size: 13px; color: #94a3b8;">Validates max loss ($500), daily halt ($2k), Theta > 0, and bid-ask spread.</div>
                        </div>
                    </div>

                    <div style="background: var(--slate-card); border: 1px solid var(--slate-border); border-radius: 16px; padding: 18px 24px; display: flex; gap: 16px; align-items: center;">
                        <span style="background: #38bdf8; color: #0f172a; font-weight: 800; border-radius: 8px; padding: 4px 10px; font-family: var(--font-mono); font-size: 13px;">04</span>
                        <div>
                            <div style="font-weight: 700; font-size: 16px; color: #fff;">Alpaca Multi-Leg (mleg) Order Router</div>
                            <div style="font-size: 13px; color: #94a3b8;">Submits native atomic credit spreads directly to paper-api.alpaca.markets.</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Terminal / Code Preview Card -->
            <div style="background: #0f172a; border: 1.5px solid #334155; border-radius: 24px; padding: 36px; box-shadow: 0 20px 40px rgba(0,0,0,0.4);">
                <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #1e293b; padding-bottom: 16px; margin-bottom: 20px;">
                    <div style="display: flex; gap: 8px;">
                        <div style="width: 12px; height: 12px; border-radius: 50%; background: #ef4444;"></div>
                        <div style="width: 12px; height: 12px; border-radius: 50%; background: #f59e0b;"></div>
                        <div style="width: 12px; height: 12px; border-radius: 50%; background: #10b981;"></div>
                    </div>
                    <div style="font-family: var(--font-mono); font-size: 12px; color: #64748b;">regret_autonomous_agent.py</div>
                </div>

                <div style="font-family: var(--font-mono); font-size: 13.5px; line-height: 1.7; color: #cbd5e1;">
                    <span style="color: #64748b;"># 1. Run live market screener</span><br>
                    <span style="color: #38bdf8;">metrics</span> = screener.calculate_iv_rank(<span style="color: #fde047;">"SPY"</span>)<br>
                    <span style="color: #f472b6;">if</span> metrics.iv_rank &gt;= <span style="color: #a78bfa;">35</span>:<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;<span style="color: #64748b;"># 2. Featherless AI Synthesis</span><br>
                    &nbsp;&nbsp;&nbsp;&nbsp;<span style="color: #38bdf8;">thesis</span> = llm.generate_strategy_thesis(metrics)<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;<span style="color: #64748b;"># 3. 6 Hard Python Risk Gates</span><br>
                    &nbsp;&nbsp;&nbsp;&nbsp;<span style="color: #38bdf8;">passed</span> = risk_engine.validate(thesis)<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;<span style="color: #f472b6;">if</span> passed.approved:<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style="color: #64748b;"># 4. Multi-leg Spread Routing</span><br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;broker.submit_spread_order(thesis.orders)<br>
                    <br>
                    <span style="color: #34d399;">&gt;&gt; [OK] Executed 5 defined-risk spreads on PA3XUIGQ0VGB</span>
                </div>
            </div>
        </div>

        <div class="slide-footer" style="color: #64748b; border-color: #334155;">
            <div>Quantitative Architecture</div>
            <div>Alpaca Trading API + Featherless AI</div>
            <div>Slide 04 of 08</div>
        </div>
    </div>


    <!-- ========================================================================= -->
    <!-- SLIDE 5: THE 6 HARD RISK GATES (Bento Shield Grid) -->
    <!-- ========================================================================= -->
    <div class="slide theme-cream">
        <div class="shape-blob-1"></div>

        <div class="slide-header">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div class="r-logo-box" style="border-color: var(--ink); color: var(--oxblood);">
                    R
                    <div class="r-rule" style="background: var(--oxblood);"></div>
                </div>
                <div style="font-family: var(--font-display); font-size: 24px; font-weight: 700; letter-spacing: 0.12em; color: var(--ink);">REGRET</div>
            </div>
            <div class="slide-badge badge-dark">Risk Engine</div>
        </div>

        <div style="text-align: center; max-width: 900px; margin: 10px auto 28px;">
            <h2 class="title-display" style="font-size: 54px; color: var(--ink); margin-bottom: 12px;">
                The 6 Hard Risk Gates
            </h2>
            <p style="font-size: 19px; color: #6e6456;">
                Every trade proposal must clear 100% of these hard-coded checks. Failure on any gate halts execution immediately.
            </p>
        </div>

        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px;">
            
            <div class="bento-card" style="background: #efe7d7; border: 1.5px solid var(--cream-border);">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                    <span style="font-size: 26px;">🛡️</span>
                    <div>
                        <div style="font-size: 11px; font-weight: 800; font-family: var(--font-mono); color: var(--oxblood);">GATE 01</div>
                        <div style="font-size: 18px; font-weight: 700; color: var(--ink);">Max Loss / Trade</div>
                    </div>
                </div>
                <p style="font-size: 15px; color: #52473b; line-height: 1.5;">Hard ceiling of <strong>$500 max loss</strong> per trade. Oversized allocation is mathematically blocked.</p>
            </div>

            <div class="bento-card" style="background: #efe7d7; border: 1.5px solid var(--cream-border);">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                    <span style="font-size: 26px;">⚡</span>
                    <div>
                        <div style="font-size: 11px; font-weight: 800; font-family: var(--font-mono); color: var(--oxblood);">GATE 02</div>
                        <div style="font-size: 18px; font-weight: 700; color: var(--ink);">Daily Circuit Breaker</div>
                    </div>
                </div>
                <p style="font-size: 15px; color: #52473b; line-height: 1.5;">Automatically halts all new trade entries if cumulative realized daily loss reaches <strong>$2,000</strong>.</p>
            </div>

            <div class="bento-card" style="background: #efe7d7; border: 1.5px solid var(--cream-border);">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                    <span style="font-size: 26px;">📊</span>
                    <div>
                        <div style="font-size: 11px; font-weight: 800; font-family: var(--font-mono); color: var(--oxblood);">GATE 03</div>
                        <div style="font-size: 18px; font-weight: 700; color: var(--ink);">Position Ceiling</div>
                    </div>
                </div>
                <p style="font-size: 15px; color: #52473b; line-height: 1.5;">Limits open positions to a maximum of <strong>5 concurrent spreads</strong> to eliminate concentration risk.</p>
            </div>

            <div class="bento-card" style="background: #efe7d7; border: 1.5px solid var(--cream-border);">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                    <span style="font-size: 26px;">💧</span>
                    <div>
                        <div style="font-size: 11px; font-weight: 800; font-family: var(--font-mono); color: var(--oxblood);">GATE 04</div>
                        <div style="font-size: 18px; font-weight: 700; color: var(--ink);">Bid-Ask Health</div>
                    </div>
                </div>
                <p style="font-size: 15px; color: #52473b; line-height: 1.5;">Rejects illiquid option contracts where the bid-ask width exceeds <strong>10% of credit received</strong>.</p>
            </div>

            <div class="bento-card" style="background: #efe7d7; border: 1.5px solid var(--cream-border);">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                    <span style="font-size: 26px;">📐</span>
                    <div>
                        <div style="font-size: 11px; font-weight: 800; font-family: var(--font-mono); color: var(--oxblood);">GATE 05</div>
                        <div style="font-size: 18px; font-weight: 700; color: var(--ink);">Greeks Sanity</div>
                    </div>
                </div>
                <p style="font-size: 15px; color: #52473b; line-height: 1.5;">Requires net positive Theta (<strong>&Theta; &gt; 0</strong>) and Delta strictly bounded within &plusmn;0.40.</p>
            </div>

            <div class="bento-card" style="background: #efe7d7; border: 1.5px solid var(--cream-border);">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                    <span style="font-size: 26px;">⏱️</span>
                    <div>
                        <div style="font-size: 11px; font-weight: 800; font-family: var(--font-mono); color: var(--oxblood);">GATE 06</div>
                        <div style="font-size: 18px; font-weight: 700; color: var(--ink);">Expiration Safety</div>
                    </div>
                </div>
                <p style="font-size: 15px; color: #52473b; line-height: 1.5;">Rejects contracts with <strong>&lt;7 DTE</strong> at entry to eliminate weekend assignment & pin risk.</p>
            </div>

        </div>

        <div class="slide-footer" style="color: #7a7164; border-color: var(--cream-border);">
            <div>Zero Tail Risk Architecture</div>
            <div>100% Deterministic Code</div>
            <div>Slide 05 of 08</div>
        </div>
    </div>


    <!-- ========================================================================= -->
    <!-- SLIDE 6: HOW WE MAKE MONEY / STRATEGY (Donut & Split Breakdown) -->
    <!-- ========================================================================= -->
    <div class="slide theme-cream">
        <div class="shape-blob-2"></div>

        <div class="slide-header">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div class="r-logo-box" style="border-color: var(--ink); color: var(--oxblood);">
                    R
                    <div class="r-rule" style="background: var(--oxblood);"></div>
                </div>
                <div style="font-family: var(--font-display); font-size: 24px; font-weight: 700; letter-spacing: 0.12em; color: var(--ink);">REGRET</div>
            </div>
            <div class="slide-badge badge-dark">Quantitative Strategy</div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 70px; align-items: center; margin: 20px 0;">
            <div>
                <h2 class="title-display" style="font-size: 56px; color: var(--ink); margin-bottom: 20px;">
                    How We Capture Positive Expectancy
                </h2>
                <p style="font-size: 19px; line-height: 1.6; color: #52473b; margin-bottom: 24px;">
                    Implied Volatility consistently overstates realized volatility >80% of the time. We sell elevated premium and close systematically:
                </p>

                <div style="display: flex; flex-direction: column; gap: 16px;">
                    <div style="background: #efe7d7; border-left: 4px solid var(--oxblood); border-radius: 12px; padding: 16px 20px;">
                        <div style="font-weight: 700; font-size: 17px; color: var(--ink);">🎯 50% Profit Target (Take Profit)</div>
                        <div style="font-size: 14px; color: #6e6456; margin-top: 4px;">Automatically closes spreads once 50% of maximum credit is captured, optimizing capital velocity.</div>
                    </div>
                    <div style="background: #efe7d7; border-left: 4px solid var(--ochre); border-radius: 12px; padding: 16px 20px;">
                        <div style="font-weight: 700; font-size: 17px; color: var(--ink);">🛑 2.0x Stop Loss Gate</div>
                        <div style="font-size: 14px; color: #6e6456; margin-top: 4px;">Closes open spreads if unrealized loss reaches 2.0x credit, cutting adverse moves immediately.</div>
                    </div>
                    <div style="background: #efe7d7; border-left: 4px solid var(--emerald); border-radius: 12px; padding: 16px 20px;">
                        <div style="font-weight: 700; font-size: 17px; color: var(--ink);">⏱️ 1 DTE Pin Risk Exit</div>
                        <div style="font-size: 14px; color: #6e6456; margin-top: 4px;">Closes all open positions 24 hours prior to expiration to eliminate weekend assignment uncertainty.</div>
                    </div>
                </div>
            </div>

            <!-- Strategy Donut Representation Card -->
            <div class="bento-card" style="background: #efe7d7; border: 1.5px solid var(--cream-border); display: flex; flex-direction: column; align-items: center; text-align: center;">
                <div style="font-size: 18px; font-weight: 700; font-family: var(--font-display); color: var(--ink); margin-bottom: 24px;">
                    Spread Payoff Profile
                </div>

                <!-- SVG Donut Chart -->
                <svg width="220" height="220" viewBox="0 0 42 42">
                    <circle class="donut-ring" cx="21" cy="21" r="15.91549430918954" fill="transparent" stroke="#e0d4be" stroke-width="6"></circle>
                    <circle class="donut-segment" cx="21" cy="21" r="15.91549430918954" fill="transparent" stroke="var(--oxblood)" stroke-width="6" stroke-dasharray="75 25" stroke-dashoffset="25"></circle>
                    <g class="donut-text">
                        <text x="50%" y="46%" text-anchor="middle" font-family="Plus Jakarta Sans" font-size="6.5" font-weight="800" fill="var(--ink)">75%</text>
                        <text x="50%" y="58%" text-anchor="middle" font-family="Plus Jakarta Sans" font-size="2.5" font-weight="700" fill="#7a7164">PROB OF PROFIT</text>
                    </g>
                </svg>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; width: 100%; margin-top: 24px;">
                    <div style="background: #f7f2e8; border: 1px solid var(--cream-border); padding: 14px; border-radius: 12px;">
                        <div style="font-size: 20px; font-weight: 800; font-family: var(--font-mono); color: var(--oxblood);">&gt; 0</div>
                        <div style="font-size: 11px; font-weight: 700; color: #7a7164; text-transform: uppercase;">Positive Theta</div>
                    </div>
                    <div style="background: #f7f2e8; border: 1px solid var(--cream-border); padding: 14px; border-radius: 12px;">
                        <div style="font-size: 20px; font-weight: 800; font-family: var(--font-mono); color: var(--emerald);">7-45</div>
                        <div style="font-size: 11px; font-weight: 700; color: #7a7164; text-transform: uppercase;">Target DTE Window</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="slide-footer" style="color: #7a7164; border-color: var(--cream-border);">
            <div>Statistical Options Edge</div>
            <div>Positive Expectancy Engine</div>
            <div>Slide 06 of 08</div>
        </div>
    </div>


    <!-- ========================================================================= -->
    <!-- SLIDE 7: WHAT WE'VE ACHIEVED (Leaderboard Live Execution Table) -->
    <!-- ========================================================================= -->
    <div class="slide theme-cream">
        <div class="shape-blob-1"></div>

        <div class="slide-header">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div class="r-logo-box" style="border-color: var(--ink); color: var(--oxblood);">
                    R
                    <div class="r-rule" style="background: var(--oxblood);"></div>
                </div>
                <div style="font-family: var(--font-display); font-size: 24px; font-weight: 700; letter-spacing: 0.12em; color: var(--ink);">REGRET</div>
            </div>
            <div class="slide-badge badge-dark">Leaderboard Traction</div>
        </div>

        <div>
            <h2 class="title-display" style="font-size: 50px; color: var(--ink); margin-bottom: 8px;">
                Live Alpaca Execution & Traction
            </h2>
            <p style="font-size: 18px; color: #6e6456; margin-bottom: 24px;">
                Account <code>PA3XUIGQ0VGB</code> actively trading with 10 covered legs across 5 defined-risk multi-leg spreads.
            </p>

            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 24px;">
                <div style="background: #efe7d7; border: 1.5px solid var(--cream-border); border-radius: 16px; padding: 18px 24px; text-align: center;">
                    <div style="font-size: 32px; font-weight: 800; font-family: var(--font-mono); color: var(--oxblood);">$100,000</div>
                    <div style="font-size: 12px; font-weight: 700; color: #7a7164; text-transform: uppercase;">Baseline Balance</div>
                </div>
                <div style="background: #efe7d7; border: 1.5px solid var(--cream-border); border-radius: 16px; padding: 18px 24px; text-align: center;">
                    <div style="font-size: 32px; font-weight: 800; font-family: var(--font-mono); color: var(--emerald);">5 SPREADS</div>
                    <div style="font-size: 12px; font-weight: 700; color: #7a7164; text-transform: uppercase;">Multi-Leg Executed</div>
                </div>
                <div style="background: #efe7d7; border: 1.5px solid var(--cream-border); border-radius: 16px; padding: 18px 24px; text-align: center;">
                    <div style="font-size: 32px; font-weight: 800; font-family: var(--font-mono); color: var(--ink);">10 LEGS</div>
                    <div style="font-size: 12px; font-weight: 700; color: #7a7164; text-transform: uppercase;">Active Covered Positions</div>
                </div>
                <div style="background: #efe7d7; border: 1.5px solid var(--cream-border); border-radius: 16px; padding: 18px 24px; text-align: center;">
                    <div style="font-size: 32px; font-weight: 800; font-family: var(--font-mono); color: var(--emerald);">95 / 95</div>
                    <div style="font-size: 12px; font-weight: 700; color: #7a7164; text-transform: uppercase;">Test Pass Rate (100%)</div>
                </div>
            </div>

            <!-- Table of active trades -->
            <div style="background: #efe7d7; border: 1.5px solid var(--cream-border); border-radius: 16px; overflow: hidden;">
                <table style="width: 100%; border-collapse: collapse; font-family: var(--font-mono); font-size: 14px;">
                    <thead>
                        <tr style="background: #e2d7be; text-align: left; color: var(--ink); font-size: 12px; letter-spacing: 0.05em; text-transform: uppercase;">
                            <th style="padding: 14px 20px;">Symbol</th>
                            <th style="padding: 14px 20px;">Setup Type</th>
                            <th style="padding: 14px 20px;">Short Leg</th>
                            <th style="padding: 14px 20px;">Long Protection</th>
                            <th style="padding: 14px 20px;">Max Loss</th>
                            <th style="padding: 14px 20px;">Alpaca Status</th>
                        </tr>
                    </thead>
                    <tbody style="color: #4a4338;">
                        <tr style="border-bottom: 1px solid var(--cream-border);"><td style="padding: 12px 20px; font-weight: 700; color: var(--ink);">SPY</td><td style="padding: 12px 20px;">Bear Call Spread</td><td style="padding: 12px 20px;">766.0 Call</td><td style="padding: 12px 20px;">767.0 Call</td><td style="padding: 12px 20px; font-weight: 700;">$15.00</td><td style="padding: 12px 20px; color: var(--emerald); font-weight: 700;">FILLED (mleg)</td></tr>
                        <tr style="border-bottom: 1px solid var(--cream-border);"><td style="padding: 12px 20px; font-weight: 700; color: var(--ink);">QQQ</td><td style="padding: 12px 20px;">Bear Call Spread</td><td style="padding: 12px 20px;">710.0 Call</td><td style="padding: 12px 20px;">711.0 Call</td><td style="padding: 12px 20px; font-weight: 700;">$15.00</td><td style="padding: 12px 20px; color: var(--emerald); font-weight: 700;">FILLED (mleg)</td></tr>
                        <tr style="border-bottom: 1px solid var(--cream-border);"><td style="padding: 12px 20px; font-weight: 700; color: var(--ink);">IWM</td><td style="padding: 12px 20px;">Bear Call Spread</td><td style="padding: 12px 20px;">294.0 Call</td><td style="padding: 12px 20px;">295.0 Call</td><td style="padding: 12px 20px; font-weight: 700;">$15.00</td><td style="padding: 12px 20px; color: var(--emerald); font-weight: 700;">FILLED (mleg)</td></tr>
                        <tr style="border-bottom: 1px solid var(--cream-border);"><td style="padding: 12px 20px; font-weight: 700; color: var(--ink);">NVDA</td><td style="padding: 12px 20px;">Bear Call Spread</td><td style="padding: 12px 20px;">225.0 Call</td><td style="padding: 12px 20px;">227.5 Call</td><td style="padding: 12px 20px; font-weight: 700;">$165.00</td><td style="padding: 12px 20px; color: var(--emerald); font-weight: 700;">FILLED (mleg)</td></tr>
                        <tr><td style="padding: 12px 20px; font-weight: 700; color: var(--ink);">AAPL</td><td style="padding: 12px 20px;">Bear Call Spread</td><td style="padding: 12px 20px;">325.0 Call</td><td style="padding: 12px 20px;">327.5 Call</td><td style="padding: 12px 20px; font-weight: 700;">$165.00</td><td style="padding: 12px 20px; color: var(--emerald); font-weight: 700;">FILLED (mleg)</td></tr>
                    </tbody>
                </table>
            </div>
        </div>

        <div class="slide-footer" style="color: #7a7164; border-color: var(--cream-border);">
            <div>Live Alpaca Paper Account: PA3XUIGQ0VGB</div>
            <div>Verified Broker Fills</div>
            <div>Slide 07 of 08</div>
        </div>
    </div>


    <!-- ========================================================================= -->
    <!-- SLIDE 8: LET'S WORK TOGETHER (Closing Terracotta Banner) -->
    <!-- ========================================================================= -->
    <div class="slide theme-terracotta">
        <div class="shape-curve-terracotta"></div>
        <div class="shape-blob-1" style="background: rgba(255,255,255,0.08);"></div>

        <div class="slide-header">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div class="r-logo-box" style="border-color: #fff; color: #fff;">
                    R
                    <div class="r-rule" style="background: #fff;"></div>
                </div>
                <div style="font-family: var(--font-display); font-size: 26px; font-weight: 700; letter-spacing: 0.15em; margin-left: 8px;">REGRET</div>
            </div>
            <div class="slide-badge badge-light">Conclusion & Vision</div>
        </div>

        <div style="max-width: 1050px; margin-top: 30px;">
            <h2 class="title-display" style="font-size: 74px; color: #ffffff; margin-bottom: 24px;">
                Let's Build the Future of AI Trading
            </h2>
            <p style="font-size: 24px; line-height: 1.5; color: #fae2dd; max-width: 900px; margin-bottom: 36px;">
                REGRET sets a new standard for autonomous trading agents: combining open-source LLM intelligence with mathematically unbreakable risk boundaries.
            </p>

            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px;">
                <div style="background: rgba(255,255,255,0.12); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.22); border-radius: 20px; padding: 24px;">
                    <div style="font-size: 18px; font-weight: 700; color: #fff; margin-bottom: 8px;">🚀 Live Web App</div>
                    <div style="font-size: 15px; color: #fae2dd; font-family: var(--font-mono);">https://regret.fly.dev</div>
                </div>
                <div style="background: rgba(255,255,255,0.12); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.22); border-radius: 20px; padding: 24px;">
                    <div style="font-size: 18px; font-weight: 700; color: #fff; margin-bottom: 8px;">⚡ Autonomous CLI</div>
                    <div style="font-size: 15px; color: #fae2dd; font-family: var(--font-mono);">regret agent start</div>
                </div>
                <div style="background: rgba(255,255,255,0.12); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.22); border-radius: 20px; padding: 24px;">
                    <div style="font-size: 18px; font-weight: 700; color: #fff; margin-bottom: 8px;">🏆 Paper Account</div>
                    <div style="font-size: 15px; color: #fae2dd; font-family: var(--font-mono);">PA3XUIGQ0VGB</div>
                </div>
            </div>
        </div>

        <div class="slide-footer" style="color: rgba(255,255,255,0.7); border-color: rgba(255,255,255,0.2); margin-top: 40px;">
            <div>Alpaca AI Trading Agents Hackathon Submission</div>
            <div>Built with Featherless AI & Alpaca API</div>
            <div>Slide 08 of 08</div>
        </div>
    </div>

</div>

</body>
</html>
"""

def main():
    html_path = Path("pitch_deck.html").resolve()
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(HTML_CONTENT)
    print(f"Generated {html_path}")

    # Compile to PDF using Microsoft Edge headless
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        "msedge",
    ]
    edge_exe = None
    for p in edge_paths:
        if Path(p).exists():
            edge_exe = str(p)
            break
    
    if not edge_exe:
        edge_exe = "msedge"

    pdf_output = Path("REGRET_Slide_Presentation.pdf").resolve()
    cmd = [
        edge_exe,
        "--headless",
        "--disable-gpu",
        "--run-all-compositor-stages-before-draw",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_output}",
        str(html_path.as_uri()),
    ]
    print("Compiling pixel-perfect PDF via Edge headless...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0 and pdf_output.exists():
        print(f"Successfully compiled {pdf_output} ({pdf_output.stat().st_size} bytes)!")
    else:
        print(f"Edge compile output: {res.stderr or res.stdout}")

if __name__ == "__main__":
    main()


def draw_slide_background(canvas_obj, doc_obj):
    canvas_obj.saveState()
    # 1. Dark primary background
    canvas_obj.setFillColor(colors.HexColor("#080c14"))
    canvas_obj.rect(0, 0, 792, 612, fill=1, stroke=0)

    # 2. Main content container card
    canvas_obj.setFillColor(colors.HexColor("#0f172a"))
    canvas_obj.setStrokeColor(colors.HexColor("#1e293b"))
    canvas_obj.setLineWidth(1)
    canvas_obj.roundRect(40, 42, 712, 524, 10, fill=1, stroke=1)

    # 3. Top cyan accent strip
    canvas_obj.setFillColor(colors.HexColor("#38bdf8"))
    canvas_obj.rect(40, 562, 712, 4, fill=1, stroke=0)

    canvas_obj.restoreState()


def create_deck(output_filename="REGRET_Slide_Presentation.pdf"):
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=landscape(letter),
        leftMargin=55,
        rightMargin=55,
        topMargin=52,
        bottomMargin=48,
    )

    styles = getSampleStyleSheet()

    # Typography Styles
    hero_title = ParagraphStyle(
        "HeroTitle",
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#ffffff"),
    )
    hero_cyan = ParagraphStyle(
        "HeroCyan",
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#38bdf8"),
    )
    slide_title = ParagraphStyle(
        "SlideTitle",
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#38bdf8"),
    )
    slide_subtitle = ParagraphStyle(
        "SlideSubtitle",
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#94a3b8"),
    )
    card_header = ParagraphStyle(
        "CardHeader",
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#f8fafc"),
    )
    card_body = ParagraphStyle(
        "CardBody",
        fontName="Helvetica",
        fontSize=8.5,
        leading=12.5,
        textColor=colors.HexColor("#cbd5e1"),
    )
    stat_number = ParagraphStyle(
        "StatNumber",
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=22,
        alignment=1, # Center
        textColor=colors.HexColor("#38bdf8"),
    )
    stat_label = ParagraphStyle(
        "StatLabel",
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=10,
        alignment=1, # Center
        textColor=colors.HexColor("#94a3b8"),
    )
    pill_cyan = ParagraphStyle(
        "PillCyan",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#38bdf8"),
    )
    pill_green = ParagraphStyle(
        "PillGreen",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#34d399"),
    )

    story = []

    # ==========================================
    # SLIDE 1: COVER / TITLE SLIDE
    # ==========================================
    story.append(Spacer(1, 20))
    story.append(Paragraph("REGRET", hero_cyan))
    story.append(Paragraph("Autonomous AI Options Trading with Zero Tail Risk", hero_title))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Separating LLM qualitative market reasoning from deterministic Python risk bounds.", slide_subtitle))
    story.append(Spacer(1, 16))

    # 4 Stat Callout Cards
    stat_boxes = [
        [
            [Paragraph("$100,000", stat_number)],
            [Paragraph("ALPACA PAPER ACCOUNT", stat_label)],
        ],
        [
            [Paragraph("6 GATES", stat_number)],
            [Paragraph("HARD RISK ENGINE", stat_label)],
        ],
        [
            [Paragraph("70 - 80%", stat_number)],
            [Paragraph("TARGET WIN RATE", stat_label)],
        ],
        [
            [Paragraph("0.0%", stat_number)],
            [Paragraph("NAKED TAIL RISK", stat_label)],
        ],
    ]
    stat_table = Table([[
        Table(stat_boxes[0], colWidths=[155]),
        Table(stat_boxes[1], colWidths=[155]),
        Table(stat_boxes[2], colWidths=[155]),
        Table(stat_boxes[3], colWidths=[155]),
    ]], colWidths=[168, 168, 168, 168])
    stat_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#1e293b")),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#1e293b")),
        ("BACKGROUND", (2, 0), (2, 0), colors.HexColor("#1e293b")),
        ("BACKGROUND", (3, 0), (3, 0), colors.HexColor("#1e293b")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (0, 0), 1, colors.HexColor("#334155")),
        ("BOX", (1, 0), (1, 0), 1, colors.HexColor("#334155")),
        ("BOX", (2, 0), (2, 0), 1, colors.HexColor("#334155")),
        ("BOX", (3, 0), (3, 0), 1, colors.HexColor("#334155")),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(stat_table)
    story.append(Spacer(1, 20))

    # Tech Badges
    badges_row = [
        Paragraph("<b>CORE STACK:</b>", ParagraphStyle("Hdr", fontName="Helvetica-Bold", fontSize=8.5, textColor=colors.HexColor("#64748b"))),
        Paragraph("Alpaca Trading API (mleg)", pill_cyan),
        Paragraph("Featherless.ai (Qwen 2.5 / Llama 3.3)", pill_cyan),
        Paragraph("Deterministic Risk Engine", pill_green),
        Paragraph("FastMCP Server", pill_cyan),
    ]
    t_badges = Table([badges_row], colWidths=[90, 150, 200, 145, 85])
    t_badges.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(t_badges)
    story.append(PageBreak())

    # ==========================================
    # SLIDE 2: THE PROBLEM (THE AI TRADING PARADOX)
    # ==========================================
    story.append(Paragraph("The Problem: Why Most AI Trading Agents Fail", slide_title))
    story.append(Paragraph("Large Language Models are powerful at qualitative synthesis but catastrophic at direct, unconstrained risk execution.", slide_subtitle))
    story.append(Spacer(1, 14))

    p_cards = [
        [
            [Paragraph("1. Hallucinated Math & Greeks", ParagraphStyle("CH1", fontName="Helvetica-Bold", fontSize=11, textColor=colors.HexColor("#f87171")))],
            [Paragraph("LLMs cannot accurately calculate multi-leg options Delta, Gamma, or expiration pin risk in real time. They hallucinate trade sizing and misestimate collateral bounds.", card_body)],
        ],
        [
            [Paragraph("2. Unbounded Naked Tail Risk", ParagraphStyle("CH2", fontName="Helvetica-Bold", fontSize=11, textColor=colors.HexColor("#f87171")))],
            [Paragraph("Direct prompt-to-trade agents often sell naked short options without protection, risking 100% account liquidation on single-day market volatility spikes.", card_body)],
        ],
        [
            [Paragraph("3. The 'Black Box' Execution Trap", ParagraphStyle("CH3", fontName="Helvetica-Bold", fontSize=11, textColor=colors.HexColor("#f87171")))],
            [Paragraph("Traditional ML trading algorithms offer zero explainability. When market regimes abruptly shift, unmonitored bots panic-sell or freeze, destroying portfolio Sharpe ratios.", card_body)],
        ],
    ]
    t_problem = Table([[
        Table(p_cards[0], colWidths=[210]),
        Table(p_cards[1], colWidths=[210]),
        Table(p_cards[2], colWidths=[210]),
    ]], colWidths=[224, 224, 224])
    t_problem.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1e1b2e")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#451a2e")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 16),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(t_problem)
    story.append(Spacer(1, 16))

    # Solution Callout Banner
    sol_banner = [
        Paragraph("<b>THE REGRET PRINCIPLE:</b>", ParagraphStyle("H", fontName="Helvetica-Bold", fontSize=9.5, textColor=colors.HexColor("#38bdf8"))),
        Paragraph("AI generates the strategic conviction — but hardened Python code owns 100% of mathematical risk, loss limits, and execution safety.", ParagraphStyle("B", fontName="Helvetica", fontSize=9.5, textColor=colors.HexColor("#e2e8f0"))),
    ]
    t_banner = Table([sol_banner], colWidths=[150, 520])
    t_banner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#06203a")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#0284c7")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(t_banner)
    story.append(PageBreak())

    # ==========================================
    # SLIDE 3: THE REGRET ARCHITECTURE & PIPELINE
    # ==========================================
    story.append(Paragraph("System Architecture: Separation of Intelligence & Math", slide_title))
    story.append(Paragraph("A closed-loop quantitative pipeline connecting Alpaca Market Data, Featherless AI, and Deterministic Risk.", slide_subtitle))
    story.append(Spacer(1, 14))

    arch_steps = [
        [
            [Paragraph("1. Market Screener", ParagraphStyle("AH1", fontName="Helvetica-Bold", fontSize=10, textColor=colors.HexColor("#38bdf8")))],
            [Paragraph("Alpaca Data API streams stock quotes & option chains across SPY, QQQ, NVDA, AAPL. Computes 52-week IV Rank in real time.", card_body)],
        ],
        [
            [Paragraph("2. Featherless AI Core", ParagraphStyle("AH2", fontName="Helvetica-Bold", fontSize=10, textColor=colors.HexColor("#38bdf8")))],
            [Paragraph("Qwen 2.5 72B / Llama 3.3 models analyze regime bias, macro sentiment, and volatility skew to formulate qualitative trade theses.", card_body)],
        ],
        [
            [Paragraph("3. 6 Hard Risk Gates", ParagraphStyle("AH3", fontName="Helvetica-Bold", fontSize=10, textColor=colors.HexColor("#34d399")))],
            [Paragraph("Deterministic Python gates validate max loss ($500), daily halt ($2k), Theta > 0, spread liquidity, and position limits.", card_body)],
        ],
        [
            [Paragraph("4. Multi-Leg Routing", ParagraphStyle("AH4", fontName="Helvetica-Bold", fontSize=10, textColor=colors.HexColor("#38bdf8")))],
            [Paragraph("Routes atomic defined-risk credit spread orders (order_class: 'mleg') directly to Alpaca paper-api.alpaca.markets.", card_body)],
        ],
    ]
    t_arch = Table([[
        Table(arch_steps[0], colWidths=[155]),
        Table(arch_steps[1], colWidths=[155]),
        Table(arch_steps[2], colWidths=[155]),
        Table(arch_steps[3], colWidths=[155]),
    ]], colWidths=[168, 168, 168, 168])
    t_arch.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1e293b")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#334155")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t_arch)
    story.append(Spacer(1, 16))

    # Developer Interfaces Row
    dev_row = [
        Paragraph("<b>DEVELOPER INTERFACES:</b>", ParagraphStyle("DH", fontName="Helvetica-Bold", fontSize=8.5, textColor=colors.HexColor("#94a3b8"))),
        Paragraph("<b>Web Dashboard:</b> React 18 + Tailwind SPA deployed on Fly.io", card_body),
        Paragraph("<b>CLI:</b> regret agent start --min-iv-rank 35", card_body),
        Paragraph("<b>MCP:</b> FastMCP Server for Claude/Cursor agents", card_body),
    ]
    t_dev = Table([dev_row], colWidths=[140, 200, 180, 150])
    t_dev.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBEFORE", (1, 0), (-1, -1), 0.5, colors.HexColor("#334155")),
        ("LEFTPADDING", (1, 0), (-1, -1), 8),
    ]))
    story.append(t_dev)
    story.append(PageBreak())

    # ==========================================
    # SLIDE 4: QUANTITATIVE STRATEGY (IV RANK REVERSION)
    # ==========================================
    story.append(Paragraph("Quantitative Strategy: High-Probability Options Edge", slide_title))
    story.append(Paragraph("Defined-risk credit spreads capturing volatility crush and accelerating Theta time decay.", slide_subtitle))
    story.append(Spacer(1, 14))

    strat_left = [
        [Paragraph("<b>Core Thesis: IV Overestimation</b>", card_header)],
        [Paragraph("Academic studies consistently prove that Implied Volatility overstates Realized Volatility over 80% of the time. When IV Rank is elevated (>35-50%), option sellers maintain statistical edge.", card_body)],
        [Spacer(1, 8)],
        [Paragraph("<b>Defined-Risk Spread Mechanics</b>", card_header)],
        [Paragraph("• <b>Bull Put Spread (Credit Put):</b> Sold in neutral/bullish regimes. Sells 0.20-0.30 Delta Put, buys $5 lower protective wing.<br/>• <b>Bear Call Spread (Credit Call):</b> Sold in neutral/bearish regimes. Sells 0.20-0.30 Delta Call, buys $5 higher protective wing.", card_body)],
    ]

    strat_right = [
        [Paragraph("<b>Optimal 7 to 45 DTE Window</b>", card_header)],
        [Paragraph("Targets the sweet spot where Theta time decay accelerates rapidly while minimizing unpredictable Gamma assignment spikes.", card_body)],
        [Spacer(1, 8)],
        [Paragraph("<b>Mathematical Risk Capping</b>", card_header)],
        [Paragraph("• <b>Max Profit:</b> 100% of Net Credit received.<br/>• <b>Max Loss:</b> Capped at (Spread Width - Credit) * 100.<br/>• <b>Win Rate:</b> ~70% to 80% expected probability.", card_body)],
    ]

    t_strat = Table([[
        Table(strat_left, colWidths=[310]),
        Table(strat_right, colWidths=[310]),
    ]], colWidths=[336, 336])
    t_strat.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1e293b")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#334155")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(t_strat)
    story.append(PageBreak())

    # ==========================================
    # SLIDE 5: THE 6 HARD RISK GATES
    # ==========================================
    story.append(Paragraph("The 6 Deterministic Hard Risk Gates", slide_title))
    story.append(Paragraph("Unbreakable security rules hardcoded in Python. If any gate fails, the trade is rejected immediately.", slide_subtitle))
    story.append(Spacer(1, 14))

    gate_items = [
        [
            [Paragraph("🛡️ Gate 1: Max Loss Per Trade", ParagraphStyle("GH1", fontName="Helvetica-Bold", fontSize=9.5, textColor=colors.HexColor("#34d399")))],
            [Paragraph("Hard ceiling of $500 maximum loss per trade. Prevents oversized allocation.", card_body)],
        ],
        [
            [Paragraph("⚡ Gate 2: Daily Loss Circuit Breaker", ParagraphStyle("GH2", fontName="Helvetica-Bold", fontSize=9.5, textColor=colors.HexColor("#34d399")))],
            [Paragraph("Halts all new trade entries if cumulative realized daily loss reaches $2,000.", card_body)],
        ],
        [
            [Paragraph("📊 Gate 3: Position Ceiling (Max 5)", ParagraphStyle("GH3", fontName="Helvetica-Bold", fontSize=9.5, textColor=colors.HexColor("#34d399")))],
            [Paragraph("Enforces maximum 5 concurrent open spreads to maintain portfolio diversification.", card_body)],
        ],
        [
            [Paragraph("💧 Gate 4: Bid-Ask Spread Health", ParagraphStyle("GH4", fontName="Helvetica-Bold", fontSize=9.5, textColor=colors.HexColor("#34d399")))],
            [Paragraph("Rejects illiquid option contracts where the bid-ask width exceeds 10% of total credit.", card_body)],
        ],
        [
            [Paragraph("📐 Gate 5: Greeks Sanity Check", ParagraphStyle("GH5", fontName="Helvetica-Bold", fontSize=9.5, textColor=colors.HexColor("#34d399")))],
            [Paragraph("Requires net positive Theta (Theta > 0) and Delta strictly bounded between -0.40 and +0.40.", card_body)],
        ],
        [
            [Paragraph("⏱️ Gate 6: Expiration Safety", ParagraphStyle("GH6", fontName="Helvetica-Bold", fontSize=9.5, textColor=colors.HexColor("#34d399")))],
            [Paragraph("Rejects contracts with <7 DTE at entry to eliminate weekend assignment & pin risk.", card_body)],
        ],
    ]

    t_gates = Table([
        [Table(gate_items[0], colWidths=[210]), Table(gate_items[1], colWidths=[210]), Table(gate_items[2], colWidths=[210])],
        [Table(gate_items[3], colWidths=[210]), Table(gate_items[4], colWidths=[210]), Table(gate_items[5], colWidths=[210])],
    ], colWidths=[224, 224, 224])
    t_gates.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1e293b")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#334155")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(t_gates)
    story.append(PageBreak())

    # ==========================================
    # SLIDE 6: ACTIVE POSITION & EXIT LIFECYCLE
    # ==========================================
    story.append(Paragraph("Active Position Lifecycle: Systematic Profit & Exit Rules", slide_title))
    story.append(Paragraph("Autonomous 24/7 background agent managing open spreads during live market hours.", slide_subtitle))
    story.append(Spacer(1, 14))

    rules_col = [
        [Paragraph("<b>Systematic Exit Rules</b>", card_header)],
        [Paragraph("• <b>🎯 50% Profit Target:</b> Closes spread when 50% max profit is achieved to maximize capital velocity.<br/>• <b>🛑 2.0x Stop Loss:</b> Automatically exits if unrealized loss reaches 2x credit received.<br/>• <b>⏱️ 1 DTE Pin Risk Exit:</b> Closes all positions at 1 DTE before expiration to eliminate assignment risk.", card_body)],
        [Spacer(1, 8)],
        [Paragraph("<b>Autonomous Loop Frequency</b>", card_header)],
        [Paragraph("Runs every 300 seconds (5 minutes) during market hours. Inspects live mark prices, evaluates P&L targets, and updates order states.", card_body)],
    ]

    terminal_col = [
        [Paragraph("<b>Live Terminal Execution Proof</b>", card_header)],
        [Paragraph("<font face='Courier' color='#38bdf8'>$ regret agent start --min-iv-rank 35</font><br/><font face='Courier' color='#94a3b8'>🚀 Starting REGRET Autonomous Options Agent...<br/>📊 Symbols: SPY, QQQ, IWM, NVDA, AAPL<br/>🛡️ Max Loss / Trade: $500.00 | Max Daily: $2,000<br/>✅ Executed 5 defined-risk multi-leg spreads<br/>● Live Alpaca Account: PA3XUIGQ0VGB</font>", ParagraphStyle("Term", fontName="Courier", fontSize=8, leading=12, textColor=colors.HexColor("#cbd5e1")))],
    ]

    t_lifecycle = Table([[
        Table(rules_col, colWidths=[310]),
        Table(terminal_col, colWidths=[310]),
    ]], colWidths=[336, 336])
    t_lifecycle.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#1e293b")),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#0f172a")),
        ("BOX", (0, 0), (0, 0), 1, colors.HexColor("#334155")),
        ("BOX", (1, 0), (1, 0), 1, colors.HexColor("#38bdf8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(t_lifecycle)
    story.append(PageBreak())

    # ==========================================
    # SLIDE 7: LIVE COMPETITION METRICS & RESULTS
    # ==========================================
    story.append(Paragraph("Live Competition Metrics: Alpaca Hackathon Leaderboard", slide_title))
    story.append(Paragraph("Account PA3XUIGQ0VGB initialized with $100,000.00 baseline with active multi-leg trades.", slide_subtitle))
    story.append(Spacer(1, 14))

    stats_grid = [
        [
            [Paragraph("<b>$100,000.00</b>", stat_number)],
            [Paragraph("STARTING EQUITY BASELINE", stat_label)],
        ],
        [
            [Paragraph("<b>5 TRADES</b>", stat_number)],
            [Paragraph("MULTI-LEG SPREADS EXECUTED", stat_label)],
        ],
        [
            [Paragraph("<b>10 LEGS</b>", stat_number)],
            [Paragraph("ACTIVE COVERED POSITIONS", stat_label)],
        ],
        [
            [Paragraph("<b>95 / 95</b>", stat_number)],
            [Paragraph("UNIT & INTEGRATION TESTS (100%)", stat_label)],
        ],
    ]
    t_stat_grid = Table([[
        Table(stats_grid[0], colWidths=[155]),
        Table(stats_grid[1], colWidths=[155]),
        Table(stats_grid[2], colWidths=[155]),
        Table(stats_grid[3], colWidths=[155]),
    ]], colWidths=[168, 168, 168, 168])
    t_stat_grid.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1e293b")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#334155")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(t_stat_grid)
    story.append(Spacer(1, 16))

    # Leaderboard assets table
    assets_data = [
        [Paragraph("<b>Symbol</b>", card_header), Paragraph("<b>Strategy</b>", card_header), Paragraph("<b>Short Leg</b>", card_header), Paragraph("<b>Hedge Leg (Long)</b>", card_header), Paragraph("<b>Max Loss</b>", card_header), Paragraph("<b>Status</b>", card_header)],
        [Paragraph("SPY", card_body), Paragraph("Bear Call Spread", card_body), Paragraph("766.0 Call", card_body), Paragraph("767.0 Call", card_body), Paragraph("$15.00", card_body), Paragraph("FILLED (mleg)", pill_green)],
        [Paragraph("QQQ", card_body), Paragraph("Bear Call Spread", card_body), Paragraph("710.0 Call", card_body), Paragraph("711.0 Call", card_body), Paragraph("$15.00", card_body), Paragraph("FILLED (mleg)", pill_green)],
        [Paragraph("IWM", card_body), Paragraph("Bear Call Spread", card_body), Paragraph("294.0 Call", card_body), Paragraph("295.0 Call", card_body), Paragraph("$15.00", card_body), Paragraph("FILLED (mleg)", pill_green)],
        [Paragraph("NVDA", card_body), Paragraph("Bear Call Spread", card_body), Paragraph("225.0 Call", card_body), Paragraph("227.5 Call", card_body), Paragraph("$165.00", card_body), Paragraph("FILLED (mleg)", pill_green)],
        [Paragraph("AAPL", card_body), Paragraph("Bear Call Spread", card_body), Paragraph("325.0 Call", card_body), Paragraph("327.5 Call", card_body), Paragraph("$165.00", card_body), Paragraph("FILLED (mleg)", pill_green)],
    ]
    t_assets = Table(assets_data, colWidths=[65, 120, 110, 130, 80, 130])
    t_assets.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#1e293b")),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#334155")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t_assets)
    story.append(PageBreak())

    # ==========================================
    # SLIDE 8: SUMMARY & ROADMAP
    # ==========================================
    story.append(Paragraph("Conclusion & Future Vision", slide_title))
    story.append(Paragraph("Setting the standard for autonomous, risk-bounded AI trading infrastructure.", slide_subtitle))
    story.append(Spacer(1, 14))

    c_left = [
        [Paragraph("<b>Why REGRET Wins</b>", card_header)],
        [Paragraph("• <b>First-Principles Safety:</b> Eliminates LLM financial hallucinations with mathematical risk gates.<br/>• <b>Deep Alpaca Integration:</b> Full support for multi-leg options, streaming data, and CLI.<br/>• <b>Open-Source AI Synergy:</b> Powered by serverless Featherless AI open models.<br/>• <b>Production-Grade Codebase:</b> 95 passing tests, FastMCP server, and live Fly.io deployment.", card_body)],
    ]

    c_right = [
        [Paragraph("<b>Post-Hackathon Roadmap</b>", card_header)],
        [Paragraph("• <b>Q4 2026:</b> Iron Condor & Earnings Volatility Crush strategy templates.<br/>• <b>Q1 2027:</b> Multi-account institutional risk pooling and live Alpaca OAuth onboarding.<br/>• <b>Q2 2027:</b> Autonomous hedging against macroeconomic black swan events using index collars.", card_body)],
    ]

    t_conclusion = Table([[
        Table(c_left, colWidths=[310]),
        Table(c_right, colWidths=[310]),
    ]], colWidths=[336, 336])
    t_conclusion.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1e293b")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#334155")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(t_conclusion)
    story.append(Spacer(1, 20))

    # Team & Links Footer Banner
    foot_banner = [
        Paragraph("<b>SUBMISSION ASSETS:</b>", ParagraphStyle("F", fontName="Helvetica-Bold", fontSize=9, textColor=colors.HexColor("#38bdf8"))),
        Paragraph("Alpaca Paper ID: <b>PA3XUIGQ0VGB</b>  |  Web: <b>https://regret.fly.dev</b>  |  CLI: <b>regret agent start</b>", ParagraphStyle("FB", fontName="Helvetica", fontSize=9, textColor=colors.HexColor("#f8fafc"))),
    ]
    t_foot = Table([foot_banner], colWidths=[150, 520])
    t_foot.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#06203a")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#0284c7")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(t_foot)

    doc.build(story, onFirstPage=draw_slide_background, onLaterPages=draw_slide_background, canvasmaker=ModernPitchCanvas)
    print(f"Generated standard ReportLab PDF: {output_filename}")


if __name__ == "__main__":
    create_deck("REGRET_Slide_Presentation.pdf")
