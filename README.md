# gafferOSv2 ⚽

A tactical intelligence system for semi-professional football teams, combining match data and machine learning to generate **data-driven insights and decision support**.

---

## 🚀 Overview

gafferOSv2 uses historical match data (StatsBomb) and engineered performance metrics to:

* Predict match outcomes
* Analyze team strengths (attack vs defense dynamics)
* Model team form and matchup differences
* Lay the foundation for **tactical decision-making (e.g., formation adjustments)**

---

## ⚙️ Current Progress

* PostgreSQL database and REST API implemented
* 1100+ matches processed (La Liga, UCL, Premier League)
* 30+ engineered features from match data
* Rolling form and team-vs-opponent differential features
* Exploratory Data Analysis completed
* Initial XGBoost model trained (WIP, ~74% accuracy)

---

## 📊 Key Insights

* Match outcomes are primarily driven by:

  * Offensive output
  * Defensive solidity
  * Shot quality

* Home advantage has a measurable impact

* Several features are highly correlated, requiring pruning

* Teams exhibit strong tactical identity:

  * ~63% of matches use their most common formation

---

## 🧠 Core Idea

Rather than asking:

> “Which formation is best?”

gafferOS aims to answer:

> **“What is the best tactical adjustment for this team in this situation?”**

This is achieved by:

* Learning team tendencies (form + formation identity)
* Comparing realistic tactical variations
* Evaluating outcomes using the trained model

---

## 🛠️ Tech Stack

Python • FastAPI • PostgreSQL • XGBoost

---

## 🔄 Pipeline

```
Data → Feature Engineering → ML Model → API → Tactical Insights
```

---

## 📁 Structure

```
backend/
├── api/        # REST endpoints
├── core/       # business logic
├── db/         # database models
├── ml/         # data + training pipeline
└── main.py
```

---

## 🎯 Goal

To make **practical tactical analytics** accessible to teams without elite-level resources.

---

## 📄 Status

Active development — evolving from prediction system to **tactical decision engine**
