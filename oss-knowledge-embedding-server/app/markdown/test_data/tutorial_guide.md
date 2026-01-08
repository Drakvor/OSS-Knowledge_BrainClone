# Getting Started with Machine Learning

Welcome to this comprehensive guide on machine learning! This tutorial will take you from beginner to intermediate level.

## What is Machine Learning?

Machine learning is a branch of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed. Instead of following pre-programmed instructions, ML systems analyze data to identify patterns and make predictions.

### Types of Machine Learning

There are three main types of machine learning:

1. **Supervised Learning**: Uses labeled training data
   - Classification: Predicting categories (spam/not spam)
   - Regression: Predicting continuous values (house prices)

2. **Unsupervised Learning**: Finds hidden patterns in data
   - Clustering: Grouping similar data points
   - Dimensionality reduction: Simplifying complex data

3. **Reinforcement Learning**: Learns through trial and error
   - Agent interacts with environment
   - Receives rewards or penalties for actions

## Setting Up Your Environment

Before we start coding, let's set up a Python environment for machine learning.

### Step 1: Install Python

First, make sure you have Python 3.7+ installed:

```bash
# Check Python version
python --version

# If you need to install Python, visit python.org
# Or use a package manager:
brew install python  # macOS
sudo apt-get install python3  # Ubuntu
```

### Step 2: Create Virtual Environment

It's best practice to create a virtual environment for your projects:

```bash
# Create virtual environment
python -m venv ml_env

# Activate it (Windows)
ml_env\Scripts\activate

# Activate it (macOS/Linux)
source ml_env/bin/activate
```

### Step 3: Install Required Libraries

Install the essential machine learning libraries:

```bash
pip install numpy pandas matplotlib scikit-learn jupyter
```

Here's what each library does:

- **NumPy**: Numerical computing with arrays
- **Pandas**: Data manipulation and analysis
- **Matplotlib**: Creating visualizations
- **Scikit-learn**: Machine learning algorithms
- **Jupyter**: Interactive notebooks

## Your First ML Project: Iris Classification

Let's build a simple classifier to predict iris flower species. This is a classic beginner project!

### Loading the Data

```python
import numpy as np
import pandas as pd
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

# Load the iris dataset
iris = load_iris()
X = iris.data  # Features: sepal/petal length and width
y = iris.target  # Target: species (0, 1, 2)

print("Dataset shape:", X.shape)
print("Number of classes:", len(iris.target_names))
print("Class names:", iris.target_names)
```

**Output:**
```
Dataset shape: (150, 4)
Number of classes: 3
Class names: ['setosa' 'versicolor' 'virginica']
```

### Exploring the Data

Understanding your data is crucial in machine learning:

```python
# Convert to DataFrame for easier exploration
df = pd.DataFrame(X, columns=iris.feature_names)
df['species'] = iris.target_names[y]

# Display first few rows
print(df.head())

# Basic statistics
print("\nDataset Statistics:")
print(df.describe())

# Check for missing values
print("\nMissing values:", df.isnull().sum().sum())
```

### Visualizing the Data

Visualization helps us understand relationships between features:

```python
import matplotlib.pyplot as plt
import seaborn as sns

# Set up the plotting style
plt.style.use('seaborn')
fig, axes = plt.subplots(2, 2, figsize=(12, 8))

features = iris.feature_names
for i, feature in enumerate(features):
    row, col = i // 2, i % 2
    sns.boxplot(data=df, x='species', y=feature, ax=axes[row, col])
    axes[row, col].set_title(f'{feature} by Species')

plt.tight_layout()
plt.show()
```

This creates box plots showing how each feature varies across species.

### Training the Model

Now let's train our first machine learning model:

```python
# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"Training set size: {X_train.shape[0]} samples")
print(f"Test set size: {X_test.shape[0]} samples")

# Create and train the model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Make predictions
y_pred = model.predict(X_test)

# Evaluate the model
accuracy = accuracy_score(y_test, y_pred)
print(f"\nAccuracy: {accuracy:.2%}")
```

**Expected Output:**
```
Training set size: 120 samples
Test set size: 30 samples

Accuracy: 100.00%
```

### Understanding the Results

Let's dive deeper into our model's performance:

```python
# Detailed classification report
print("Classification Report:")
print(classification_report(y_test, y_pred, target_names=iris.target_names))

# Feature importance
feature_importance = pd.DataFrame({
    'feature': iris.feature_names,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print("\nFeature Importance:")
print(feature_importance)
```

This shows which features (measurements) are most important for classification.

## Advanced Topics

### Cross-Validation

Cross-validation gives us a more robust estimate of model performance:

```python
from sklearn.model_selection import cross_val_score

# Perform 5-fold cross-validation
cv_scores = cross_val_score(model, X, y, cv=5)

print("Cross-validation scores:", cv_scores)
print(f"Average CV score: {cv_scores.mean():.2%}")
print(f"Standard deviation: {cv_scores.std():.3f}")
```

### Hyperparameter Tuning

Optimize your model's parameters for better performance:

```python
from sklearn.model_selection import GridSearchCV

# Define parameter grid
param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [3, 5, 7, None],
    'min_samples_split': [2, 5, 10]
}

# Perform grid search
grid_search = GridSearchCV(
    RandomForestClassifier(random_state=42),
    param_grid,
    cv=5,
    scoring='accuracy'
)

grid_search.fit(X_train, y_train)

print("Best parameters:", grid_search.best_params_)
print("Best cross-validation score:", grid_search.best_score_)
```

## Common Pitfalls and Best Practices

### 1. Data Leakage

**Problem**: Using future information to predict the past.

```python
# BAD: Scaling before splitting
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)  # Uses information from test set!
X_train, X_test = train_test_split(X_scaled, y)

# GOOD: Scale after splitting
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)  # Only transform, don't fit!
```

### 2. Overfitting

**Signs of overfitting**:
- High training accuracy but low test accuracy
- Large gap between training and validation performance

**Solutions**:
- Use cross-validation
- Regularization techniques
- More training data
- Simpler models

### 3. Evaluation Metrics

Don't rely solely on accuracy, especially with imbalanced datasets:

```python
from sklearn.metrics import precision_recall_fscore_support

# Calculate precision, recall, and F1-score
precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred)

print("Per-class metrics:")
for i, class_name in enumerate(iris.target_names):
    print(f"{class_name}: Precision={precision[i]:.3f}, "
          f"Recall={recall[i]:.3f}, F1={f1[i]:.3f}")
```

## Next Steps

Congratulations! You've completed your first machine learning project. Here's what to explore next:

1. **Try different algorithms**: SVM, Neural Networks, Gradient Boosting
2. **Work with real datasets**: Kaggle competitions, UCI ML repository
3. **Learn feature engineering**: Creating new features from existing data
4. **Deep learning**: TensorFlow, PyTorch for neural networks
5. **Specialized domains**: Computer vision, NLP, time series

### Recommended Resources

- **Books**:
  - "Hands-On Machine Learning" by Aurélien Géron
  - "Pattern Recognition and Machine Learning" by Christopher Bishop
  
- **Online Courses**:
  - Andrew Ng's Machine Learning Course (Coursera)
  - Fast.ai Practical Deep Learning
  
- **Practice Platforms**:
  - Kaggle: Real competitions and datasets
  - Google Colab: Free GPU-enabled notebooks

### Final Tips

> **Remember**: Machine learning is as much about understanding your data as it is about algorithms. Always start with exploratory data analysis!

Good luck on your machine learning journey! 🚀

---

*This tutorial covered the basics of machine learning with Python. For more advanced topics, check out our [Deep Learning Guide](./deep-learning.md) and [Data Preprocessing Techniques](./preprocessing.md).*