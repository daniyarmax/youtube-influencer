# YouTube Influencer Analysis

## Project Overview

This project analyzes YouTube influencer data to identify trends, engagement patterns, and performance metrics of content creators.

The analysis was performed using Python, Pandas, SQL, and data visualization tools to extract meaningful business insights from influencer-related datasets.

---

## Objectives

- Analyze YouTube influencer performance
- Explore audience engagement metrics
- Identify top-performing creators
- Understand relationships between subscribers, views, and engagement
- Build analytical dashboards for visualization

---

## Tech Stack

- Python
- Pandas
- NumPy
- SQL
- Jupyter Notebook / Google Colab
- Tableau / Looker Studio
- Git & GitHub

---

## Project Structure

```bash
youtube-influencer/
│
├── data/               # Raw and cleaned datasets
├── notebooks/          # Jupyter/Colab notebooks
├── sql/                # SQL queries
├── dashboard/          # Dashboard screenshots
├── scripts/            # Data processing scripts
├── README.md
└── requirements.txt
```

---

## Data Analysis Process

### 1. Data Collection
- Imported YouTube influencer dataset
- Loaded data using Pandas

### 2. Data Cleaning
- Removed duplicates
- Handled missing values
- Standardized column formats

### 3. Exploratory Data Analysis (EDA)
- Subscriber distribution analysis
- Engagement metrics analysis
- Top categories identification
- Correlation analysis

### 4. Visualization
- Built dashboards and charts
- Visualized influencer performance metrics
- Compared engagement across categories

---

## Key Insights

- Channels with high subscriber counts do not always have the highest engagement rates
- Entertainment and lifestyle categories dominate audience interaction
- Views and subscriber growth show strong positive correlation
- Some mid-sized creators demonstrate better engagement efficiency than large influencers

---

## SQL Analysis

The project also includes SQL queries for:
- Aggregations
- Ranking influencers
- Calculating engagement metrics
- Filtering top-performing channels

Example:

```sql
SELECT channel_name,
       subscribers,
       views
FROM influencers
ORDER BY subscribers DESC;
```

---

## Dashboards

### Tableau Dashboard
Interactive dashboard created for influencer performance analysis.

### Looker Studio Dashboard
Visualization of engagement trends and audience metrics.

---

## How to Run the Project

### Clone Repository

```bash
git clone https://github.com/daniyarmax/youtube-influencer.git
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Notebook

Open Jupyter Notebook or Google Colab and run:

```bash
analysis.ipynb
```

---

## Future Improvements

- Add YouTube API integration
- Build automated ETL pipeline
- Deploy dashboard online
- Add machine learning predictions for engagement

---

## Author

Daniyar Maksut

GitHub:
https://github.com/daniyarmax
