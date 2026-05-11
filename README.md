# gafferOSv2 ⚽

A tactical intelligence and squad analysis platform for semi-professional football teams, combining match data, machine learning, player profiling, and rule-based tactical reasoning to generate actionable coaching insights.

---

## 🚀 Overview

gafferOSv2 is designed to help football coaches and analysts make smarter tactical and squad decisions without requiring elite-level infrastructure.

The system combines:
- Match analytics
- Machine learning predictions
- Player form tracking
- Physical assessment data
- Tactical trait profiling
- Explainable tactical recommendations

to simulate a lightweight “football operations system” for clubs.

---

## 🧠 Core Philosophy

Instead of asking:

> “What is the best formation?”

gafferOS asks:

> **“What tactical adjustment best fits this squad, opponent, and match context?”**

The engine evaluates:
- Team strengths and weaknesses
- Opposition style
- Squad form and fatigue
- Tactical player traits
- Physical capabilities
- Match context (home/away, pressing intensity, etc.)

to recommend tactical setups and player selections.

---

## ⚙️ Current Features

### 📊 Match Intelligence
- Match outcome prediction using engineered StatsBomb features
- 30+ tactical and statistical metrics
- Rolling form analysis
- Team vs opponent differential modeling
- Home/away contextual adjustments

### 🧬 Player Profiling System
- Coach-assigned tactical trait system
- Position-specific trait banks
- Tactical tendency scoring
- Conflict validation for incompatible traits

### 🏃 Physical Assessment Engine
Converts real-world testing data into Football Manager-style attributes:
- Pace
- Acceleration
- Stamina
- Strength
- Heading
- Jumping

based on:
- Sprint times
- Beep tests
- Vertical jump
- Height/weight

### 🎯 Tactical Reasoning Engine
Hybrid ML + rule-based tactical decision system:
- Formation recommendations
- Press intensity logic
- Tactical focus selection
- Squad rotation considerations
- Trait-aware tactical reasoning

### 📈 Explainable Outputs
The system explains *why* recommendations are made instead of producing black-box predictions.

Example:
> “A 4-3-3 is recommended due to strong progressive passing profiles and high squad pace.”

---

## 📊 Project Progress

### Completed
- PostgreSQL schema design
- FastAPI backend architecture
- Match ingestion pipeline
- Feature engineering pipeline
- XGBoost outcome model
- Tactical engine v1
- Player trait system
- Physical-to-attribute calculator
- Squad form tracking
- REST API endpoints

### In Progress
- Tactical explainer upgrade
- Rotation advisor
- Deployment
- React frontend

### Planned
- Matchup-specific tactical adaptation
- Multi-club support
- Season management
- Advanced visual dashboards

---

## 🛠️ Tech Stack

### Backend
- Python
- FastAPI
- PostgreSQL
- SQLAlchemy

### Machine Learning
- XGBoost
- Pandas
- NumPy
- Scikit-learn

### Data
- StatsBomb Open Data

---

## 🔄 System Pipeline

```text
Match Data
    ↓
Feature Engineering
    ↓
ML Inference + Tactical Metrics
    ↓
Trait & Attribute Analysis
    ↓
Tactical Reasoning Engine
    ↓
Explainable Recommendations
```

---

## 📁 Project Structure

```text
backend/
├── api/              # REST API routes
├── core/             # tactical and business logic
├── db/               # database models and setup
├── ml/               # ML training + feature engineering
└── main.py
```

---

## 🎯 Vision

To provide semi-professional clubs with accessible tactical intelligence tools that are normally only available to elite football organizations.

---

## 📄 Current Status

Active development — transitioning from a prediction-focused system into a full tactical decision-support platform.
