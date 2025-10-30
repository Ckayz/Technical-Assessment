# PROMPTS.md  

## Overview  
For this project, I used **ChatGPT (GPT-5)** and **Claude AI (Claude Code)** as coding copilots to speed up development of both the **Frontend Dashboard** and the **Data Pipeline** challenge. My approach was to use ChatGPT for **system design, structured planning, and architecture decisions**, and then use Claude for **hands-on code generation and refinement**.  

This document summarizes:  
- The prompts I used  
- How I integrated outputs from both tools  
- What worked well  
- What didn’t  

---

## Tools Used  
- **ChatGPT (GPT-5)**: For breaking down requirements, drafting decision matrices, and generating step-by-step AI prompts I could feed into Claude.  
- **Claude AI (Claude Code)**: For generating working Next.js + Python code, iterating on debugging, and refining individual modules.  

---

## Prompts I Used  

### 1. **Frontend Dashboard (Required)**  
- **ChatGPT Prompt:**  
  > “I need to build a real-time trading dashboard with Next.js 14, TypeScript, Tailwind. It should connect to Hyperliquid WS, show 3 pairs (BTC, ETH, SOL), agent positions, real-time PnL. Must handle disconnects and have responsive design. Can you outline the architecture, state management choice, and testing strategy?”  

  - **Output:** ChatGPT gave me a clean breakdown (Next.js + Zustand + WebSocket utils + Vitest tests).  

- **Claude Prompt:**  
  > “Based on this architecture, generate the code for a MarketTicker component that connects to a WebSocket, updates Zustand store, and animates price changes. Use TypeScript and Tailwind.”  

  - **Output:** Claude generated complete React components with types, which I adapted into my Next.js app.  

---

### 2. **Option B: Data Pipeline (Chosen)**  
- **ChatGPT Prompt:**  
  > “Help me decide between Option A (Python worker) vs Option B (Data pipeline). Which is easier? Then give me step-by-step prompts I can feed into Claude so I can build Option B cleanly.”  

  - **Output:** ChatGPT explained the trade-offs, recommended Option B, and drafted modular prompts for config, subgraph client, CoinGecko client, transform, IO, orchestrator, and tests.  

- **Claude Prompt (for subgraph.py):**  
  > “Write a Python function that queries the Uniswap v3 subgraph for swap events in the last 60 minutes. Use httpx, handle pagination, and return a list of structured events with token symbols and amounts.”  

- **Claude Prompt (for coingecko.py):**  
  > “Create a rate-limited CoinGecko client in Python using httpx + tenacity. It should fetch USD prices for a list of tokens, retry with backoff if rate-limited, and cache results in memory.”  

- **Claude Prompt (for transform.py):**  
  > “Take a list of swap events and enrich them with USD values from CoinGecko. Then aggregate by trading pair to produce a DataFrame with count, total volume, and average volume.”  

- **Claude Prompt (for main.py):**  
  > “Orchestrate the whole pipeline: load config, fetch swaps, fetch prices, enrich, summarize, write JSON and CSV outputs, and update last_processed_block in state.json. Print run stats.”  

---

## What Worked Well  
- **ChatGPT for planning:** Broke down complex instructions into smaller, logical prompts. Helped me understand *why* to choose Redis vs Timescale vs ClickHouse, and why Option B was better for me.  
- **Claude for code:** Generated clean, working TypeScript and Python modules. It handled async logic and Tailwind styling quickly.  
- **Division of labor:** ChatGPT was like a senior architect, Claude was like a pair-programmer. This balance saved time.  

---

## What Didn’t Work Well  
- **WebSocket schema mismatch:** Claude assumed a certain message format from Hyperliquid WS. I had to manually adjust based on the actual API.  
- **Over-complex outputs:** Sometimes Claude generated too much boilerplate. I had to trim it down to keep it simple.  
- **Testing gaps:** Neither tool wrote perfect tests without my guidance. I had to prompt multiple times to get minimal working pytest/Vitest tests.  
- **Retries/Backoff:** ChatGPT suggested `tenacity`, but Claude’s first code didn’t implement jitter correctly — I had to refine prompts.  

---

## Final Reflection  
Using AI tools made it much faster to build both parts of the challenge. The key was **prompting in small, modular steps** instead of asking for the whole project in one go. ChatGPT helped me think like a system designer, while Claude helped me translate that plan into working code.  
