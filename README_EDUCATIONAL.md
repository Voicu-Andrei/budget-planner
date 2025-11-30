# Budget Planner - Educational Documentation
## Discrete Mathematics & Probability Concepts

This document explains all the discrete mathematics, probability, and statistical concepts used in the Budget Planner application, including where they're implemented and how they work.

---

## Table of Contents
1. [Overview](#overview)
2. [Arrays and Data Structures](#arrays-and-data-structures)
3. [Statistical Measures](#statistical-measures)
4. [Probability Distributions](#probability-distributions)
5. [Z-Score and Anomaly Detection](#z-score-and-anomaly-detection)
6. [Monte Carlo Simulation](#monte-carlo-simulation)
7. [Confidence Intervals](#confidence-intervals)
8. [Expected Value](#expected-value)
9. [Implementation Examples](#implementation-examples)
10. [Potential Teacher Questions](#potential-teacher-questions)

---

## Overview

This application demonstrates practical applications of discrete mathematics and probability theory in personal finance. The core mathematical concepts enable:

- Statistical analysis of spending patterns
- Anomaly detection using probability
- Future outcome prediction through simulation
- Quantifying uncertainty and risk

**Primary Math Concepts Used**:
1. Arrays/Lists for data storage
2. Mean, Variance, Standard Deviation
3. Normal (Gaussian) Distribution
4. Z-scores for standardization
5. Monte Carlo Simulation
6. Confidence Intervals
7. Expected Value
8. Percentiles

---

## Arrays and Data Structures

### What: Arrays and Lists
Arrays are fundamental data structures that store collections of elements.

### Where Used:
- **File**: `math_engine.py`, `database.py`
- **Purpose**: Store transactions, simulation results, monthly totals

### Example from Code:
```python
# Line 33 in math_engine.py
amounts = [t['amount'] for t in transactions]

# Line 164 in math_engine.py (Monte Carlo)
ending_balances = []
for _ in range(simulations):
    # ... calculations ...
    ending_balances.append(ending_balance)
```

### Why Important:
Arrays allow us to store multiple data points and perform mathematical operations on entire datasets at once, enabling statistical analysis.

---

## Statistical Measures

### 1. Mean (Average)

**Formula**:
```
μ = (Σ xi) / n
```
Where xi are individual values and n is the count.

**Where Used**:
- **File**: `math_engine.py`, line 54
- **Function**: `calculate_category_stats()`

**Code**:
```python
mean = np.mean(monthly_values) if monthly_values else 0
```

**Purpose**: Calculate average spending per category to understand typical behavior.

**Example**: If you spent [$200, $180, $220, $190] on groceries over 4 months, mean = $197.50

---

### 2. Standard Deviation

**Formula**:
```
σ = √[(Σ(xi - μ)²) / (n-1)]
```

**Where Used**:
- **File**: `math_engine.py`, line 55
- **Function**: `calculate_category_stats()`

**Code**:
```python
std_dev = np.std(monthly_values, ddof=1) if len(monthly_values) > 1 else 0
```

**Note**: We use `ddof=1` for sample standard deviation (Bessel's correction).

**Purpose**: Measure how much spending varies from the average. High std_dev means inconsistent spending.

**Example**:
- Groceries: $200 ± $20 (consistent)
- Dining: $150 ± $80 (very variable)

---

### 3. Variance

**Formula**:
```
σ² = (Σ(xi - μ)²) / (n-1)
```

**Where Used**:
- **File**: `math_engine.py`, line 56
- **Function**: `calculate_category_stats()`

**Code**:
```python
variance = np.var(monthly_values, ddof=1) if len(monthly_values) > 1 else 0
```

**Purpose**: Variance is the square of standard deviation. Used as a measure of volatility.

**Relationship**: variance = std_dev²

---

## Probability Distributions

### Normal (Gaussian) Distribution

**Formula (Probability Density Function)**:
```
f(x) = (1 / (σ√(2π))) * e^(-(x-μ)² / (2σ²))
```

**Where**:
- μ = mean
- σ = standard deviation
- π ≈ 3.14159
- e ≈ 2.71828

**Where Used**:
- **File**: `math_engine.py`, line 167
- **Function**: `run_monte_carlo_simulation()`

**Code**:
```python
sampled_amount = np.random.normal(dist['mean'], dist['std_dev'])
```

**Purpose**: We assume spending follows a normal distribution. This means:
- Most months spending is near the average
- Extreme values are rare
- Distribution is symmetric

**Real-World Application**:
If grocery spending averages $200 with std dev $30:
- 68% of months: $170-$230 (within 1σ)
- 95% of months: $140-$260 (within 2σ)
- 99.7% of months: $110-$290 (within 3σ)

**Visual Representation**:
```
        *
      * | *
    *   |   *
  *     |     *
*       |       *
------------------------
      μ (mean)
```

---

## Z-Score and Anomaly Detection

### Z-Score (Standard Score)

**Formula**:
```
z = (x - μ) / σ
```

**Where**:
- x = individual transaction amount
- μ = mean of all transactions in category
- σ = standard deviation

**Where Used**:
- **File**: `math_engine.py`, lines 82-92
- **Function**: `detect_anomaly()`

**Code**:
```python
def detect_anomaly(category, amount, threshold=2.0):
    stats = calculate_category_stats(category)

    if not stats or stats['transaction_std'] == 0:
        return False, 0.0

    # Calculate z-score
    z_score = (amount - stats['transaction_mean']) / stats['transaction_std']

    # If |z_score| > threshold, it's an anomaly
    is_anomaly = abs(z_score) > threshold

    return is_anomaly, float(z_score)
```

**Interpretation**:
- z = 0: Exactly average
- z = 1: One standard deviation above mean
- z = -1: One standard deviation below mean
- z = 2: Two standard deviations above mean (unusual)
- z > 3: Very unusual (less than 0.3% probability)

**Example**:
```
Dining Out average: $15 per transaction
Standard deviation: $10

New transaction: $45
z = (45 - 15) / 10 = 3.0

Conclusion: 3 standard deviations above normal = ANOMALY!
```

**Why 2.0 Threshold?**
In a normal distribution, values beyond 2 standard deviations occur less than 5% of the time. This is a reasonable threshold for "unusual."

**Displayed to User**:
When adding a transaction, if flagged:
```
⚠️ Unusual Transaction Detected!
This transaction is 3.0 standard deviations from your average.
```

---

## Monte Carlo Simulation

### What is Monte Carlo?
A computational technique that uses repeated random sampling to obtain numerical results. Named after the Monte Carlo casino in Monaco.

### How It Works:
1. Define probability distributions for each variable
2. Randomly sample from these distributions many times
3. Run the calculation for each sample
4. Analyze the distribution of outcomes

### Where Used:
- **File**: `math_engine.py`, lines 95-199
- **Function**: `run_monte_carlo_simulation()`
- **Page**: Prediction page

### Algorithm:
```python
def run_monte_carlo_simulation(simulations=1000, adjustments=None):
    # 1. Get historical statistics for each category
    category_distributions = {}
    for category in categories:
        stats = calculate_category_stats(category)
        category_distributions[category] = {
            'mean': stats['mean'],
            'std_dev': stats['std_dev']
        }

    # 2. Run simulations
    ending_balances = []
    for _ in range(simulations):
        total_spending = 0

        # 3. Sample from each category's distribution
        for category, dist in category_distributions.items():
            sampled_amount = np.random.normal(dist['mean'], dist['std_dev'])
            sampled_amount = max(0, sampled_amount)  # No negative spending
            total_spending += sampled_amount

        # 4. Calculate outcome
        ending_balance = monthly_budget - fixed_expenses - total_spending
        ending_balances.append(ending_balance)

    # 5. Analyze results
    return statistical_analysis(ending_balances)
```

### Example Simulation:

**Historical Data**:
- Groceries: μ = $200, σ = $30
- Dining: μ = $150, σ = $70
- Entertainment: μ = $80, σ = $50
- Budget: $2000
- Fixed Expenses: $855

**Simulation 1**:
- Groceries: sample($200, $30) = $195
- Dining: sample($150, $70) = $140
- Entertainment: sample($80, $50) = $95
- Total Variable: $430
- Ending Balance: $2000 - $855 - $430 = $715 ✅

**Simulation 2**:
- Groceries: sample($200, $30) = $225
- Dining: sample($150, $70) = $200
- Entertainment: sample($80, $50) = $120
- Total Variable: $545
- Ending Balance: $2000 - $855 - $545 = $600 ✅

**...Run 998 more times...**

**Results** (from 1000 simulations):
- 850 ended positive (85% probability of positive balance)
- 730 met savings goal (73% probability)
- Median outcome: $350 remaining

### Why Monte Carlo?
Real life is random! Your spending won't be exactly the average every month. Monte Carlo captures this randomness and shows you the range of possible outcomes, not just a single prediction.

**Mathematical Basis**:
By the Law of Large Numbers, as simulations → ∞, our estimate → true probability.

---

## Confidence Intervals

### What: A range that likely contains the true value

**Formula** (for normal distribution):
```
CI = μ ± (z* × σ/√n)
```

**Where**:
- z* = critical value (1.96 for 95% confidence)
- σ = standard deviation
- n = sample size

### Where Used:
- **File**: `math_engine.py`, line 253
- **Function**: `calculate_confidence_interval()`
- **Display**: Analysis page statistics

**Code**:
```python
def calculate_confidence_interval(data, confidence=0.90):
    if len(data) < 2:
        return (0, 0)

    mean = np.mean(data)
    std_err = stats.sem(data)  # Standard error of mean
    interval = std_err * stats.t.ppf((1 + confidence) / 2, len(data) - 1)

    return (mean - interval, mean + interval)
```

**Interpretation**:
"We are 90% confident that your true monthly spending on groceries is between $180 and $220"

**Example Output**:
```
Food & Groceries: $200 ± $30
90% Confidence Interval: [$185, $215]
```

---

## Expected Value

### Formula:
```
E[X] = Σ (xi × P(xi))
```

For continuous distributions:
```
E[X] = μ (the mean)
```

### Where Used:
- **Implicit** in Monte Carlo results
- **File**: `math_engine.py`, prediction calculations

**Example**:
```python
# Expected monthly spending
expected_spending = sum(category_means.values())

# Expected ending balance
expected_balance = monthly_budget - fixed_expenses - expected_spending
```

**Real Application**:
If you have:
- Groceries average: $200
- Dining average: $150
- Entertainment average: $80

Expected total variable spending = $200 + $150 + $80 = $430

---

## Percentiles

### What: The value below which a percentage of data falls

**Where Used**:
- **File**: `math_engine.py`, line 188
- **Function**: `run_monte_carlo_simulation()`

**Code**:
```python
percentiles = {
    'p10': float(np.percentile(balances, 10)),
    'p25': float(np.percentile(balances, 25)),
    'p50': float(np.percentile(balances, 50)),  # median
    'p75': float(np.percentile(balances, 75)),
    'p90': float(np.percentile(balances, 90))
}
```

**Interpretation**:
- **p10** (10th percentile): Worst case - only 10% of outcomes are worse
- **p25-p75**: Middle 50% of outcomes (likely range)
- **p50**: Median (half above, half below)
- **p90**: Best case - only 10% of outcomes are better

**Example Output**:
```
Best Case (p90):  $650 remaining
Likely Range:     $300-$500
Worst Case (p10): $150 remaining
```

---

## Implementation Examples

### Complete Example 1: Adding a Transaction with Anomaly Detection

**User Action**: Add $200 shopping transaction

**Step 1**: Retrieve historical data
```python
# Get all past Shopping transactions
transactions = db.execute('''
    SELECT amount FROM transactions
    WHERE category = 'Shopping'
''').fetchall()

amounts = [45, 60, 35, 50, 70, 40, 55]  # Example historical data
```

**Step 2**: Calculate statistics
```python
mean = np.mean(amounts)  # = 50.71
std_dev = np.std(amounts, ddof=1)  # = 12.25
```

**Step 3**: Calculate z-score
```python
new_amount = 200
z_score = (200 - 50.71) / 12.25  # = 12.19
```

**Step 4**: Check threshold
```python
threshold = 2.0
is_anomaly = abs(12.19) > 2.0  # True!
```

**Step 5**: Alert user
```
⚠️ This transaction is 12.2 standard deviations above your average Shopping spending!
```

### Complete Example 2: Monte Carlo Prediction

**Setup**:
- Budget: $2000
- Fixed Expenses: $855
- Historical Spending:
  - Groceries: μ=$200, σ=$30
  - Dining: μ=$150, σ=$70

**Run 3 Simulations** (normally 1000):

**Simulation 1**:
```python
groceries = np.random.normal(200, 30)  # = 195
dining = np.random.normal(150, 70)     # = 140
total_variable = 195 + 140              # = 335
balance = 2000 - 855 - 335              # = 810
```

**Simulation 2**:
```python
groceries = np.random.normal(200, 30)  # = 220
dining = np.random.normal(150, 70)     # = 200
total_variable = 220 + 200              # = 420
balance = 2000 - 855 - 420              # = 725
```

**Simulation 3**:
```python
groceries = np.random.normal(200, 30)  # = 185
dining = np.random.normal(150, 70)     # = 90
total_variable = 185 + 90               # = 275
balance = 2000 - 855 - 275              # = 870
```

**Results** (from 3 simulations):
```python
balances = [810, 725, 870]
mean_balance = np.mean(balances)  # = 801.67
prob_positive = 3/3 * 100         # = 100%
```

---

## Potential Teacher Questions & Answers

### Q1: "Why did you choose the normal distribution for spending?"

**Answer**: The normal distribution is appropriate because:
1. **Central Limit Theorem**: When many small random factors influence spending (daily decisions, prices, quantities), the sum tends toward normal distribution
2. **Real-world observation**: Most spending clusters around a typical amount with symmetric tails
3. **Simplicity**: While real spending may not be perfectly normal, it's a reasonable approximation that makes calculations tractable

**Alternative I considered**: Log-normal distribution for categories with high variance, but normal is simpler for demonstration.

---

### Q2: "Why use a z-score threshold of 2.0 for anomaly detection?"

**Answer**:
- In a normal distribution, 95% of values fall within 2 standard deviations
- This means only 5% of normal transactions are flagged as anomalies
- It balances sensitivity (catching real anomalies) with specificity (avoiding false alarms)
- Industry standard for outlier detection

**Shown in code**: `math_engine.py`, line 83

---

### Q3: "How accurate is your Monte Carlo simulation?"

**Answer**: The accuracy depends on:

1. **Number of simulations**: We use 1,000 which gives approximately ±3% error
   - Formula for error: ε ≈ 1/√n = 1/√1000 ≈ 0.032

2. **Quality of historical data**: Need at least 6 months for stable estimates
   - More data → better mean/std_dev estimates → more accurate predictions

3. **Assumptions**:
   - Assumes future spending patterns match historical
   - Assumes categories are independent (might not be true)

**Could improve by**:
- Running 10,000 simulations (slower but more precise)
- Using more sophisticated distributions
- Accounting for correlations between categories

---

### Q4: "What discrete math concepts are used besides probability?"

**Answer**:

1. **Arrays/Lists**: Core data structure for storing transactions
   - Indexing, iteration, list comprehensions

2. **Set Theory**: Categories form a finite set
   - {'Food', 'Dining', 'Entertainment', ...}

3. **Functions**: Mathematical functions implemented in code
   - f: category → statistics
   - f: transactions → probability

4. **Summation**: Used extensively
   - Σ amounts for totals
   - Σ (x - μ)² for variance

5. **Logic**: Boolean conditions
   - IF |z| > 2 THEN anomaly
   - Complex conditionals in health score

---

### Q5: "Can you explain the health score calculation in detail?"

**Answer**: The health score (0-100) is a weighted composite metric:

**Code location**: `math_engine.py`, line 202

**Component 1**: Budget adherence (40 points)
```python
if total_expenses <= monthly_budget:
    ratio = total_expenses / monthly_budget
    score += 40 * (1 - ratio * 0.5)
```
- Spending $0: 40 points
- Spending 50% of budget: 30 points
- Spending 100% of budget: 20 points

**Component 2**: Savings goal (30 points)
```python
remaining = monthly_budget - total_expenses
if remaining >= savings_goal:
    score += 30
elif remaining > 0:
    score += 30 * (remaining / savings_goal)
```
- Meeting goal: 30 points
- 50% of goal: 15 points
- No savings: 0 points

**Component 3**: Consistency (20 points)
- Would calculate variance across recent months
- Currently simplified to 15 points baseline

**Component 4**: Anomalies (10 points)
```python
if anomaly_count == 0:
    score += 10
elif anomaly_count <= 2:
    score += 5
```

**Example**:
- Spent $1,400 of $2,000 budget (70%) → 26 points
- Saved $320 of $300 goal → 30 points
- Good consistency → 15 points
- 1 anomaly → 5 points
- **Total**: 76/100 (Good)

---

### Q6: "How do you handle edge cases?"

**Answer**: Several safeguards are implemented:

**1. Division by zero**:
```python
if stats['transaction_std'] == 0:
    return False, 0.0  # Can't calculate z-score
```

**2. Insufficient data**:
```python
if len(monthly_values) < 2:
    std_dev = 0  # Need at least 2 points for std dev
```

**3. Negative spending** (simulation):
```python
sampled_amount = max(0, sampled_amount)  # Ensure non-negative
```

**4. Empty categories**:
```python
if not stats:
    return None  # No data available
```

---

### Q7: "What's the computational complexity of your main operations?"

**Answer**:

**Calculating category stats**: O(n) where n = number of transactions
- One pass to fetch from database
- NumPy operations are O(n)

**Anomaly detection**: O(n) average
- Calls calculate_category_stats which is O(n)

**Monte Carlo simulation**: O(s × c) where s = simulations, c = categories
- 1,000 simulations × 6 categories = 6,000 operations
- Each normal sample is O(1)
- Total: O(1) in practice (constant categories)

**Overall**: Application is efficient for personal use. Could optimize with caching for production scale.

---

### Q8: "How would you extend this to be more mathematically sophisticated?"

**Potential Enhancements**:

1. **Bayesian Updating**: Update probability distributions as new data arrives
   ```
   P(spending | new_data) ∝ P(new_data | spending) × P(spending)
   ```

2. **Multivariate Analysis**: Account for correlations between categories
   - Covariance matrix
   - Principal Component Analysis

3. **Time Series Analysis**: Seasonal patterns, trends
   - Moving averages
   - ARIMA models

4. **Machine Learning**: Predict categories from descriptions
   - Classification algorithms
   - Natural language processing

5. **Markov Chains**: Model spending state transitions
   - Transition probability matrices
   - State space models

6. **Hypothesis Testing**: Statistical significance of changes
   - T-tests for comparing months
   - Chi-square for category distribution

---

## Presentation Talking Points

### Opening (30 seconds)
"I built a budget tracking app that uses discrete mathematics and probability to help people manage money intelligently. It goes beyond simple tracking - it predicts future outcomes and detects unusual spending using statistical analysis."

### Core Math (2 minutes)
"The app uses three main mathematical techniques:

1. **Statistical Analysis**: Calculate mean, variance, and standard deviation for each spending category to understand patterns

2. **Z-Score Anomaly Detection**: Automatically flag unusual transactions by measuring how many standard deviations they are from the mean

3. **Monte Carlo Simulation**: Run 1,000 random scenarios to predict next month's outcomes with probability distributions"

### Live Demo (3 minutes)
1. Show dashboard with health score
2. Add unusual transaction → show anomaly alert
3. Navigate to Analysis → explain mean and std dev
4. Run Monte Carlo → show probability predictions
5. Adjust "what-if" scenarios → show how predictions change

### Why It Matters (30 seconds)
"This demonstrates how discrete math and probability aren't just theoretical - they solve real problems. The same techniques are used in finance, risk analysis, and machine learning."

### Questions Welcome
"I can explain any of the mathematical formulas, show you the code, or discuss how I could extend this further."

---

## Summary of Math Concepts by Location

| Concept | File | Line(s) | Function |
|---------|------|---------|----------|
| Arrays | math_engine.py | 33, 164 | Data storage |
| Mean | math_engine.py | 54 | calculate_category_stats |
| Std Dev | math_engine.py | 55 | calculate_category_stats |
| Variance | math_engine.py | 56 | calculate_category_stats |
| Z-Score | math_engine.py | 88 | detect_anomaly |
| Normal Dist | math_engine.py | 167 | run_monte_carlo_simulation |
| Percentiles | math_engine.py | 188-194 | run_monte_carlo_simulation |
| Histogram | math_engine.py | 197 | run_monte_carlo_simulation |
| Confidence Interval | math_engine.py | 253-261 | calculate_confidence_interval |

---

## Conclusion

This project demonstrates practical applications of:
- ✅ Probability distributions
- ✅ Statistical analysis
- ✅ Arrays and data structures
- ✅ Randomness and simulation
- ✅ Expected value and percentiles
- ✅ Real-world problem solving with math

All concepts from the discrete mathematics and probability syllabus are applied to create a genuinely useful tool.
