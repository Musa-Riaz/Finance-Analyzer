import pandas as pd
import numpy as np 
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import mean_absolute_error
from sklearn.ensemble import RandomForestRegressor

# Rule based categorization
CATEGORY_RULES = {
    "Mobile Top-Up":  ["top-up", "ufone", "jazz", "telenor", "zong"],
    "Food & Dining":  ["crusteez", "food", "restaurant", "cafe", "pizza", "eat"],
    "Streaming":      ["spotify", "netflix", "youtube"],
    "Education":      ["nust", "university", "college", "school", "tuition"],
    "Utilities":      ["electric", "gas", "water", "internet", "bill"],
    "Self Transfer":  ["muhammad musa riaz", "musa riaz"],
}

def rule_based_category(description: str) -> str | None:
    #first converting to lowercase
    desc_lower = description.lower()
    for category, keywords in CATEGORY_RULES.items():
        if any(kw in desc_lower for kw in keywords):
            return category
    return None

# Preparing text for clustering
def prepare_text_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["text_for_ml"] =( 
        df["description"].fillna("")+ " "+df["type"].fillna("")
    )
    #clean the text
    df["text_for_ml"] = (
        df["text_for_ml"].str.lower().
        str.replace(r"[|\/\-]", " ", regex=True).
        str.replace(r"\s+", " ", regex=True).
        str.strip()
    )

    return df

def cluster_transactions(df: pd.DataFrame, n_clusters: int = 6) -> pd.DataFrame:
    df = df.copy()


    # Prepare text features first — this adds the "text_for_ml" column
    df = prepare_text_features(df)

    # Apply rule-based categories first
    df["category"] = df["description"].apply(rule_based_category)
    # .apply() runs rule_based_category on every row's description
    # rows that matched a rule now have a category, others have None

    # Split into categorized and uncategorized
    categorized = df[df["category"].notna()].copy()
    # .notna() is the opposite of .isna() — returns True where value is NOT null
    uncategorized = df[df["category"].isna()].copy()

    # If everything got categorized by rules, no need for ML
    if len(uncategorized) == 0:
        return df

    # --- TF-IDF Vectorization ---
    # TfidfVectorizer converts text into a matrix of numbers
    # Each row = one transaction, each column = one word
    # The value = that word's TF-IDF score for that transaction
    vectorizer = TfidfVectorizer(
        max_features=50,
        # Only consider the top 50 most important words
        # With small datasets, using too many features hurts more than helps
        stop_words="english",
        # Ignore common English words like "to", "from", "the"
        # These appear everywhere and add no signal
        ngram_range=(1, 2),
        # Consider both single words AND pairs of adjacent words
        # So "fund transfer" becomes one feature, not just "fund" and "transfer" separately
    )

    # fit_transform() does two things in one call:
    # 1. "fit" — learns the vocabulary from your text
    # 2. "transform" — converts the text into numbers using that vocabulary
    # This is a core scikit-learn pattern you'll see constantly
    # The result is a sparse matrix — an efficient way to store mostly-zero data
    text_matrix = vectorizer.fit_transform(uncategorized["text_for_ml"])

    # Also include the transaction AMOUNT as a feature
    # Spending patterns (small vs large amounts) help distinguish categories
    amounts = uncategorized["amount"].abs().values.reshape(-1, 1)
    # .values converts a pandas Series to a numpy array
    # .reshape(-1, 1) reshapes it from [1, 2, 3] to [[1], [2], [3]]
    # scikit-learn expects 2D arrays — rows are samples, columns are features
    # -1 means "figure out this dimension automatically"

    # Scale the amounts so they're in a similar range to TF-IDF scores
    # Without this, a large amount like 25000 would dominate the clustering
    # StandardScaler makes the mean=0 and standard deviation=1
    # This is called "feature normalization" — crucial in ML
    scaler = StandardScaler()
    amounts_scaled = scaler.fit_transform(amounts)

    # Combine text features and amount into one feature matrix
    # numpy's hstack() stacks arrays horizontally (side by side)
    # We need to convert the sparse matrix to dense first with .toarray()
    import numpy as np
    combined_features = np.hstack([text_matrix.toarray(), amounts_scaled])

    # --- KMeans ---
    kmeans = KMeans(
        n_clusters=n_clusters,
        random_state=42,
        # random_state=42 makes results reproducible
        # KMeans starts with random centers — same seed = same starting point = same result
        # 42 is a convention in ML (from The Hitchhiker's Guide to the Galaxy)
        n_init=10,
        # Run the algorithm 10 times with different starting points
        # Pick the best result — reduces chance of getting stuck in a bad solution
    )

    # fit_predict() trains the model AND returns cluster labels in one call
    # Returns an array like [0, 2, 1, 0, 3, ...] — one cluster number per transaction
    cluster_labels = kmeans.fit_predict(combined_features)

    # Assign cluster labels back to the uncategorized rows
    uncategorized = uncategorized.copy()
    uncategorized["cluster"] = cluster_labels

    # Give each cluster a readable name based on what's in it
    # We look at the most common TYPE in each cluster as a hint
    cluster_names = {}
    for cluster_id in range(n_clusters):
        cluster_rows = uncategorized[uncategorized["cluster"] == cluster_id]
        # value_counts() counts occurrences of each unique value
        # like a frequency table — similar to lodash's _.countBy()
        most_common_type = cluster_rows["type"].value_counts().index[0]
        # .index[0] gets the most frequent value (value_counts sorts descending)
        cluster_names[cluster_id] = f"Transfer — {most_common_type}"

    uncategorized["category"] = uncategorized["cluster"].map(cluster_names)
    # .map() on a Series with a dict replaces each value using the dict as a lookup
    # like doing array.map(x => dict[x]) in JS

    # Combine categorized (rule-based) and newly categorized (ML) rows
    result = pd.concat([categorized, uncategorized], ignore_index=True)
    result = result.sort_values("timestamp").reset_index(drop=True)
    # sort back into chronological order
    # drop=True means don't add the old index as a column

    return result

def spending_by_category(df: pd.DataFrame) -> pd.DataFrame:
    out = df[df["direction"] == "OUT"].copy()

    return (
        out.groupby("category")["amount"]
        .agg(
            total=lambda x: round(abs(x.sum()), 2),
            count="count",
            avg=lambda x: round(abs(x.mean()), 2),
        )
        .sort_values("total", ascending=False)
        .reset_index()
    )

def detect_anomalies(df: pd.DataFrame, contamination: float = 0.08) -> pd.DataFrame:
    df = df.copy()
    #feature engineering
    df["feat_amount"] = df["amount"].abs()
    df["feat_hour"] = df["timestamp"].dt.hour
    daily_counts = df.groupby("date")["amount"].transform("count")
    df["feat_daily_count"] = daily_counts
    df["feat_direction"] = (df["direction"] == "IN").astype(int)
    #feature scaling
    feature_cols = ["feat_amount", "feat_hour", "feat_daily_count", "feat_direction"]
    features = df[feature_cols].values
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)

    #Isolation forest
    model = IsolationForest(
        contamination=contamination,
        n_estimators=100,
        random_state = 42
    )
    predictions = model.fit_predict(features_scaled)
    df["is_anomaly"] =  predictions == -1
    #get the anomaly score
    scores = model.decision_function(features_scaled)
    df["anomaly_score"] = scores   
    # We need to refit because fit_predict doesn't store the model
    # In production you'd save the model — we'll do that in the FastAPI phase

    # Clean up the temporary feature columns — they were just for the model
    df = df.drop(columns=feature_cols)
    return df


def get_anomaly_report(df: pd.DataFrame) -> pd.DataFrame:
    # Filter to only anomalous transactions
    anomalies = df[df["is_anomaly"] == True].copy()

    # Sort by anomaly score ascending — most anomalous first
    anomalies = anomalies.sort_values("anomaly_score", ascending=True)

    # Add a human readable reason for WHY it might be flagged
    # This is rule-based reasoning on top of the ML output
    # A good pattern: ML finds anomalies, rules explain them
    def explain_anomaly(row):
        reasons = []
        # Calculate stats from the full dataframe for comparison
        # We use the outer df here via closure — same as JS closures
        mean_amount = df["amount"].abs().mean()
        std_amount = df["amount"].abs().std()
        # std() = standard deviation — measures how spread out values are
        # A value more than 2 standard deviations from the mean is unusual

        if abs(row["amount"]) > mean_amount + 2 * std_amount:
            reasons.append(f"Unusually large amount")

        if row["feat_hour"] if "feat_hour" in row else row["timestamp"].hour < 6:
            hour = row["timestamp"].hour
            if hour < 6:
                reasons.append(f"Unusual time ({hour}:00)")

        if not reasons:
            reasons.append("Unusual pattern vs your history")

        return ", ".join(reasons)

    anomalies["reason"] = anomalies.apply(explain_anomaly, axis=1)
    # axis=1 means apply the function row by row
    # axis=0 would apply column by column
    # You'll use axis=1 whenever your function needs to look at multiple columns

    return anomalies[["timestamp", "description", "amount", "direction", "category", "is_anomaly", "anomaly_score", "reason"]]


def prepare_monthly_features(df: pd.DataFrame) -> pd.DataFrame:
    #monthly spendings
    monthly = (
        df[df["direction"] == "OUT"]
        .groupby("month")["amount"]
        .apply(lambda x: abs(x.sum()))
        .reset_index()
    )
    monthly.columns = ["month", "total_spent"]

    #monthly incomes
    monthly_income = (
        df[df["direction"] == "IN"]
        .groupby("month")["amount"]
        .sum()
        .reset_index()
    )
    monthly_income.columns = ["month", "total_income"]
    # merging them
    monthly = pd.merge(monthly, monthly_income, on="month", how="inner")
    # sorting 
    monthly = monthly.sort_values("month").reset_index(drop=True)
    #numeric column for months
    monthly["month_index"] = range(1, len(monthly) + 1)
    # range(1, 5) gives [1, 2, 3, 4]

    # Add a human readable label for charts
    monthly["month_label"] = pd.to_datetime(monthly["month"]).dt.strftime("%b %Y")

    return monthly


def train_spending_model(monthly_df: pd.DataFrame):
    X = monthly_df[["month_index"]].values
    y = monthly_df["total_spent"].values

    # Keep a simple linear baseline and compare against a non-linear ensemble.
    baseline_model = LinearRegression()
    baseline_model.fit(X, y)

    ensemble_model = RandomForestRegressor(
        n_estimators=220,
        max_depth=6,
        min_samples_leaf=1,
        random_state=42,
    )
    ensemble_model.fit(X, y)

    # --- Leave-One-Out Cross Validation ---
    loo_errors = []
    for i in range(len(monthly_df)):
        X_train = np.delete(X, i, axis=0)
        y_train = np.delete(y, i, axis=0)
          # Test set: just row i
        X_test = X[i].reshape(1, -1)
        # reshape(1, -1) converts a 1D array to a 2D row — needed by scikit-learn
        y_test = y[i]

        # Compare linear and ensemble model per fold and keep the lower error.
        temp_linear_model = LinearRegression()
        temp_linear_model.fit(X_train, y_train)

        temp_ensemble_model = RandomForestRegressor(
            n_estimators=180,
            max_depth=6,
            min_samples_leaf=1,
            random_state=42,
        )
        temp_ensemble_model.fit(X_train, y_train)
        # .fit() is where the actual learning happens
        # It finds the slope and intercept that minimize prediction error
        # This is the "training" step you learned in theory

        linear_prediction = temp_linear_model.predict(X_test)[0]
        ensemble_prediction = temp_ensemble_model.predict(X_test)[0]
        prediction = ensemble_prediction if abs(ensemble_prediction - y_test) <= abs(linear_prediction - y_test) else linear_prediction
        # .predict() returns an array — [0] gets the single value

        error = abs(prediction - y_test)
        loo_errors.append(error)

    avg_error = sum(loo_errors) / len(loo_errors)

    # Pick final model by in-sample MAE as a practical tie-breaker for now.
    baseline_mae = mean_absolute_error(y, baseline_model.predict(X))
    ensemble_mae = mean_absolute_error(y, ensemble_model.predict(X))

    final_model = ensemble_model if ensemble_mae <= baseline_mae else baseline_model

    # The coefficient (slope) tells us the monthly trend
    # Positive = spending increasing month over month
    # Negative = spending decreasing
    if hasattr(final_model, "coef_"):
        slope = float(final_model.coef_[0])
        intercept = float(final_model.intercept_)
        model_name = "linear_regression"
    else:
        # Estimate slope from first and last predicted points for non-linear models.
        start_pred = float(final_model.predict(np.array([[X.min()]]))[0])
        end_pred = float(final_model.predict(np.array([[X.max()]]))[0])
        denom = max(float(X.max() - X.min()), 1.0)
        slope = (end_pred - start_pred) / denom
        intercept = start_pred
        model_name = "random_forest"

    metadata = {
        "slope": round(slope, 2),
        "intercept": round(intercept, 2),
        "avg_monthly_change": round(slope, 2),
        "avg_loo_error": round(avg_error, 2),
        "num_months_trained": len(monthly_df),
        "model": final_model,
        "model_name": model_name,
    }

    return final_model, metadata

def forecast_next_months(model, monthly_df: pd.DataFrame, n_months: int = 3) -> pd.DataFrame:
    last_month_index = monthly_df["month_index"].max()
    last_month = pd.to_datetime(monthly_df["month"].max())
    # pd.to_datetime() converts "2026-02" string to a proper datetime

    forecasts = []

    for i in range(1, n_months + 1):
        future_index = last_month_index + i

        # Predict spending for this future month
        X_future = np.array([[future_index]])
        predicted_spending = model.predict(X_future)[0]

        # Calculate the future month label
        # pd.DateOffset(months=i) adds i months to a date
        # This correctly handles month boundaries (Jan + 1 = Feb, Dec + 1 = Jan next year)
        future_date = last_month + pd.DateOffset(months=i)
        future_label = future_date.strftime("%b %Y")

        forecasts.append({
            "month_label": future_label,
            "predicted_spending": round(max(predicted_spending, 0), 2),
            # max(..., 0) prevents negative predictions which make no sense for spending
            "is_forecast": True,
        })

    # Add is_forecast=False to historical data so we can distinguish them in charts
    historical = monthly_df[["month_label", "total_spent"]].copy()
    historical = historical.rename(columns={"total_spent": "predicted_spending"})
    historical["is_forecast"] = False

    # Combine historical + forecast
    result = pd.concat([historical, pd.DataFrame(forecasts)], ignore_index=True)

    return result
    