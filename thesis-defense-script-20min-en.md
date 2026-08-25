# THESIS DEFENSE SCRIPT - 20 MINUTES

**Topic:** A Multi-Agent System for Vietnamese Financial Market Data Analysis and Summarization  
**Total duration:** 20:00 = 14:30 speaking + 5:30 demo video  
**Recommended pace:** Speak calmly at about 95-105 words per minute, including brief pauses and slide transitions. Emphasize the keywords shown on each slide rather than reading all visible text.

## Timing checkpoints

- Finish Slide 9 by **04:40**
- Finish Slide 16 by **09:30**
- Start the demo video at **12:20**
- Finish the demo video at **17:50**
- Finish the presentation at **20:00**

---

## Slide 1 - Title (00:00-00:27 | 27 seconds)

> Good morning, members of the committee and our supervisor. We are Nguyen Vinh Khang and Le Quoc Huy. Today, we are pleased to present our thesis, “A Multi-Agent System for Vietnamese Financial Market Data Analysis and Summarization,” featuring our decision-support system, Stockrium.

## Slide 2 - Table of Contents (00:27-00:40 | 13 seconds)

> Our presentation covers six parts: the introduction, related platforms, foundation, system architecture, the Stockrium demo, and future work and conclusion.

## Slide 3 - Market Context (00:40-01:05 | 25 seconds)

> According to VSDC, Vietnam had more than 11.8 million domestic individual trading accounts in 2025. This shows that access to stock market investment is expanding, and growing participation creates greater demand for accessible financial information and analytical tools. However, not every investor has enough time, data, or expertise to perform reliable analysis independently.

## Slide 4 - Difficulties (01:05-01:48 | 43 seconds)

> First, financial data is fragmented across many platforms, making collection and comparison time-consuming. Second, general-purpose language models may produce outdated or unreliable insights when they are not synchronized with current data. Third, unverified opinions from KOLs and online communities may encourage emotional or speculative decisions. Therefore, investors need an integrated and transparent system that can control, validate, and explain its analytical results.

## Slide 5 - Project Objectives (01:48-02:20 | 32 seconds)

> First, we aimed to build a decision-support platform that makes financial information easier to access, analyze, and summarize. Second, we developed an analysis and backtesting environment for comparing stocks and strategy configurations. Third, we aimed to construct a curated and up-to-date market dataset that can support future research and application development.

## Slide 6 - Application Scope (02:20-02:55 | 35 seconds)

> Stockrium is designed for Vietnamese individual investors, from beginners to experienced users. It supports market exploration, AI-assisted analysis, and a financial chatbot, but does not place orders or connect to brokerage accounts. It currently covers the 100 stocks in the VN100 and can later expand to HOSE, HNX, and UPCoM. Stockrium remains a decision-support tool and does not guarantee profit or replace an investor's judgment.

## Slide 7 - Other Platforms (02:55-03:27 | 32 seconds)

> SSI iBoard Pro provides AI-assisted fundamental and technical analysis. CVS on MoMo focuses on a simple, low-cost trading experience. Entrade X by DNSE offers conversational AI using technical, fundamental, and news data within its brokerage platform. However, there is still room for an independent, configurable system that clearly explains how its recommendations are produced.

## Slide 8 - Research Gap (03:27-04:07 | 40 seconds)

> First, Stockrium combines technical, fundamental, and news evidence in one multi-agent workflow for the Vietnamese stock market. Second, users can select the evidence sources, investment horizon, and relative weights. Third, its experimentation workspace compares supported analytical configurations, reference strategies, and stocks under consistent historical assumptions. Together, these features provide an integrated, configurable, transparent, and inspectable decision-support environment rather than a new price-prediction model.

## Slide 9 - Main Sources for Stock Analysis (04:07-04:40 | 33 seconds)

> Technical analysis evaluates price, volume, and indicators such as MA, RSI, MACD, Bollinger Bands, and KDJ to identify trends and momentum. Fundamental analysis evaluates financial health, growth, valuation, liquidity, and leverage using financial statements and key ratios. Finally, news and sentiment analysis identifies events that may affect investor expectations and stock performance.

## Slide 10 - System Architecture (04:40-05:27 | 47 seconds)

> On the client side, the React Native application and web interface communicate with the backend through HTTPS APIs. FastAPI receives requests, coordinates business logic, and returns results. Scheduled Python jobs collect market and news data from SSI and Serper. PostgreSQL stores structured data, Supabase Storage keeps backtesting artifacts, and Redis manages session state. AI services generate explanations, while Google Authentication supports user identity. This architecture separates the client, processing, storage, and external-service layers.

## Slide 11 - Multi-Agent Stock Analysis Pipeline (05:27-06:20 | 53 seconds)

> A request contains the stock symbol, mode, language, investment horizon, selected sources, and weights. The orchestrator creates a deterministic plan and activates the required branches. Three branches prepare news, multi-year fundamental evidence, and technical indicators. The specialized agents analyze these inputs independently and return scores with explanations. The recommendation node combines the scores, applies deterministic BUY-or-WAIT rules, and validates the trading plan. Finally, the aggregator generates the confidence level and summary, while the shared state keeps the process traceable.

## Slide 12 - Planning by Investment Horizon (06:20-07:01 | 41 seconds)

> Suppose the user selects FPT with a short-term horizon of one to three months. The fundamental branch uses five years of financial statements and indicators. The technical branch uses hourly price, volume, and indicator data from the latest three months. The article branch uses news and sentiment from the latest month. Therefore, each data window is adapted to the investment context instead of using one fixed configuration.

## Slide 13 - Specialized Analysis Agents (07:01-07:36 | 35 seconds)

> The Fundamental Agent evaluates the company's financial health and outlook. The Technical Agent evaluates trends, momentum, and trading signals, while the Article Agent summarizes relevant news and sentiment. Each agent returns a normalized score from zero to one with a natural-language explanation. This separation shows how each evidence source contributes to the final result.

## Slide 14 - Deterministic Recommendation (07:36-08:26 | 50 seconds)

> In this short-term example, the fundamental, technical, and article weights are 0.1, 0.6, and 0.3 respectively. The system produces BUY only when both the total score and technical score reach at least 0.6. A BUY result includes an entry price, take-profit level, stop-loss level, and maximum holding period; otherwise, the result is WAIT. These deterministic rules prevent the language model from making the final decision on its own.

## Slide 15 - Confidence and Summary (08:26-09:00 | 34 seconds)

> After the recommendation node produces a validated decision and trading plan, the aggregator creates two additional outputs. Confidence represents the consistency and strength of the evidence, while the summary explains the result. Users can therefore inspect the score from each source, the risk-management plan, the confidence level, and the reasoning behind the recommendation.

## Slide 16 - Stock Analysis Options (09:00-09:30 | 30 seconds)

> Users can choose a short-, medium-, or long-term horizon and analyze one stock, the VN30, or the VN100. They can include news, fundamental indicators, and selected technical indicators. Finally, they can adjust the weight of each evidence group, allowing comparison between different investment perspectives.

## Slide 17 - Backtesting Pipeline Overview (09:30-09:59 | 29 seconds)

> To evaluate the recommendations, we developed a backtesting pipeline. At each historical date, the system uses only information available at that time to produce BUY or WAIT. A BUY decision is simulated, while a WAIT decision is recorded. The process is repeated across multiple dates and summarized in a final report, limiting the use of future information.

## Slide 18 - Run Multi-Agent Analysis (09:59-10:26 | 27 seconds)

> This example backtests FPT for a medium-term strategy between January the first and August the first, 2026. For each record in the daily dataset, the system reruns the multi-agent analysis using only the information available at that time, producing signals under conditions closer to historical decisions.

## Slide 19 - Generate Trading Signal (10:26-10:50 | 24 seconds)

> At each date, the multi-agent result is converted into a trading signal. A BUY signal includes the entry price, take-profit level, stop-loss level, and maximum holding period. These parameters create a concrete plan that can be simulated and measured consistently.

## Slide 20 - Simulate Order Execution (10:50-11:16 | 26 seconds)

> A simulated order is executed on the next candle to avoid trading on the same data that produced the signal. The position then closes at the take-profit level, stop-loss level, or maximum holding period. These fixed exit rules make comparisons between configurations fairer.

## Slide 21 - Backtesting Result (11:16-11:43 | 27 seconds)

> After the simulation, the report includes total trades, winning and losing trades, win rate, total return, maximum drawdown, profit factor, and Sharpe ratio. Together, these metrics describe both performance and risk, instead of evaluating a strategy using only its win rate.

## Slide 22 - Backtesting Options (11:43-12:10 | 27 seconds)

> Users can backtest one stock or the VN30 using data from June 2024 to the present. The current version focuses on medium-term investing and allows users to select evidence sources and adjust their weights. This makes it possible to compare different configurations instead of receiving only one fixed recommendation.

## Slide 23 - Demo Video (12:10-17:50 | 10-second introduction + 5-minute-30-second video)

> We will now present a short demo of market exploration, AI-assisted stock analysis, and backtesting.

**[Start the video and do not speak over it.]**

## Slide 24 - Objectives Revisited (17:50-18:22 | 32 seconds)

> The application brings data and analytical results into one unified experience. It also allows users to configure analysis and backtesting to compare stocks or strategies, while the standardized data supports further research. Within this thesis, Stockrium remains a decision-support prototype, not an automated trading system.

## Slide 25 - Expert Feedback (18:22-18:49 | 27 seconds)

> Ms. Trinh, a securities analyst at FPT Securities, found Stockrium visually appealing, user-friendly, and comprehensive, and believed its AI explanations could reduce analysis time. Based on her feedback, we refined the horizon settings, contributor weights, specialized-agent prompts, chatbot interaction, and overall user experience.

## Slide 26 - Future Work (18:49-19:19 | 30 seconds)

> First, we will simulate more realistic trading conditions and expand the evaluation period and market coverage. Second, we will collect evaluations from more investment professionals to improve the analysis. Third, we will improve reliability, real-time delivery, security, performance, recovery, and usability through more resilient infrastructure and comprehensive testing.

## Slide 27 - Conclusion (19:19-19:49 | 30 seconds)

> In conclusion, Stockrium integrates three evidence sources in a transparent and configurable multi-agent workflow, helping users inspect recommendations and compare configurations through backtesting. However, it is not a new price-prediction model, does not guarantee market outperformance, and does not replace the investor's final judgment.

## Slide 28 - Thank You (19:49-20:00 | 11 seconds)

> Thank you to the committee and our supervisor for your time and attention. We are ready to answer your questions.

---

## Rehearsal guidance

1. Rehearse once with a timer without pausing between slides. If you run late, remove the final sentence from Slide 4, 10, 11, or 14 instead of rushing the conclusion.
2. When the demo ends, you should have approximately **2 minutes and 10 seconds** remaining. If the video runs a few seconds late, shorten Slides 24 and 25 first.
3. Do not read every word shown on the slides. Maintain eye contact and turn toward the screen only when referring to a diagram or formula.
4. Prepare an offline copy of the demo and test the audio before the presentation. If the video fails, move immediately to a short verbal walkthrough instead of repeatedly restarting it.
