import matplotlib.pyplot as plt 
import matplotlib.ticker as mticker
import seaborn as sns
import pandas as pd

#global style setup for all the charts
sns.set_theme(style="whitegrid", palette="muted")

def balance_over_time(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(
        df["timestamp"], #x values
        df["balance"], #y values
        color="#4C72B0",
        linewidth=2,
        marker="o",
        markersize=4
    )
    ax.fill_between(df["timestamp"], df["balance"], alpha=0.1, color="#4C72B0")

    ax.set_title("Account Balance — January 2026", fontsize=14, pad=15)
    ax.set_xlabel("Date", fontsize=11)
    ax.set_ylabel("Balance (PKR)", fontsize=11)
    
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.show()

def plot_spending_by_type(df: pd.DataFrame):
    out = df[df["direction"] == "OUT"].copy()
    by_type = (
        out.groupby("type")["amount"]
        .apply(lambda x: abs(x.sum()))
        .sort_values(ascending=True)  # ascending so biggest bar is at the top
        .reset_index()
    )
    by_type.columns = ["type", "total"]
    fig, ax = plt.subplots(figsize=(10, 5))
    # barh = horizontal bar chart (easier to read long category names)
    sns.barplot(
        data=by_type,
        x="total",      # values (length of bar)
        y="type",       # categories (label of bar)
        ax=ax,          # which axes to draw on
        orient="h",     # horizontal
    )
    for bar in ax.patches:
        # bar.get_width() gives the value of the bar
        # bar.get_y() + bar.get_height()/2 centers the label vertically
        ax.text(
            bar.get_width() + 50,           # x position (slightly past the bar)
            bar.get_y() + bar.get_height() / 2,  # y position (center of bar)
            f"PKR {bar.get_width():,.0f}",  # the text — formatted with commas
            va="center",                    # vertical alignment
            fontsize=9,
        )

    ax.set_title("Spending by Transaction Type", fontsize=14, pad=15)
    ax.set_xlabel("Total Spent (PKR)", fontsize=11)
    ax.set_ylabel("")  # y label is obvious from the bars, no need to repeat it
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

    plt.tight_layout()
    plt.show()

def plot_daily_spending(df: pd.DataFrame):
    out = df[df["direction"] == "OUT"].copy()
     # Group by date and sum spending for each day
    daily = (
        out.groupby("date")["amount"]
        .apply(lambda x: abs(x.sum()))
        .reset_index()
    )
    daily.columns = ["date", "total_spent"]

    fig, ax = plt.subplots(figsize=(12, 5))

    # Bar chart — one bar per day
    sns.barplot(
        data=daily,
        x="date",
        y="total_spent",
        ax=ax,
        color="#4C72B0",
    )

    ax.set_title("Daily Spending — January 2026", fontsize=14, pad=15)
    ax.set_xlabel("Date", fontsize=11)
    ax.set_ylabel("Amount Spent (PKR)", fontsize=11)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

    # Convert date objects to strings for cleaner labels
    # date column contains Python date objects, so we format them as strings
    ax.set_xticklabels(
        [str(d) for d in daily["date"]],
        rotation=45,
        ha="right",
    )

    plt.tight_layout()
    plt.show()

def plot_income_vs_spending(df: pd.DataFrame):
    total_in = df[df["direction"] == "IN"]["amount"].sum()
    total_out = abs(df[df["direction"] == "OUT"]["amount"].sum())

    # We're building the data manually here as a simple dict
    # then converting to a DataFrame — useful pattern to know
    summary_df = pd.DataFrame({
        "category": ["Income", "Spending"],
        "amount": [total_in, total_out],
    })

    fig, ax = plt.subplots(figsize=(6, 5))

    sns.barplot(
        data=summary_df,
        x="category",
        y="amount",
        ax=ax,
        palette=["#55A868", "#C44E52"],  # green for income, red for spending
    )

    # Add value labels on top of each bar
    for bar in ax.patches:
        ax.text(
            bar.get_x() + bar.get_width() / 2,  # center horizontally on bar
            bar.get_height() + 200,              # slightly above the bar top
            f"PKR {bar.get_height():,.0f}",
            ha="center",
            fontsize=10,
            fontweight="bold",
        )

    ax.set_title("Income vs Spending — January 2026", fontsize=14, pad=15)
    ax.set_xlabel("")
    ax.set_ylabel("Amount (PKR)", fontsize=11)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

    plt.tight_layout()
    plt.show()  

def plot_monthly_income_vs_spending(monthly_df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(10, 5)) 
    melted = pd.melt(
        monthly_df,
        id_vars=["month_label"],
        # id_vars = columns to keep as-is (they become identifiers)
        value_vars=["total_income", "total_spent"],
        # value_vars = columns to melt into rows
        var_name="category",
        # var_name = what to call the new column that holds the old column names
        value_name="amount",
        # value_name = what to call the column that holds the values
    )
  # Clean up the category labels for the legend
    melted["category"] = melted["category"].replace({
        "total_income": "Income",
        "total_spent": "Spending"
    })
    # .replace() on a column with a dict swaps values — like a lookup table

    sns.barplot(
        data=melted,
        x="month_label",
        y="amount",
        hue="category",
        # hue = which column to use for color grouping
        # this is what creates the side-by-side grouped bars
        palette={"Income": "#55A868", "Spending": "#C44E52"},
        ax=ax,
    )
    ax.set_title("Income vs Spending by Month", fontsize=14, pad=15)
    ax.set_xlabel("")
    ax.set_ylabel("Amount (PKR)", fontsize=11)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.legend(title="")

    plt.tight_layout()
    plt.show()

def plot_monthly_net(monthly_df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(10, 5))

    # Color each bar based on whether net is positive or negative
    # This is a list comprehension producing a list of colors
    colors = ["#55A868" if n >= 0 else "#C44E52" for n in monthly_df["net"]]
    # Reading: "green if net is positive, red if negative, for each net value"

    bars = ax.bar(
        monthly_df["month_label"],  # x positions
        monthly_df["net"],          # bar heights
        color=colors,
    )
    # We use ax.bar() directly here instead of seaborn
    # because we need per-bar colors — seaborn doesn't support that easily
    # This is a good example of when to drop down to matplotlib directly

    # Draw a horizontal line at y=0 for reference
    ax.axhline(y=0, color="black", linewidth=0.8, linestyle="--", alpha=0.5)
    # axhline = "axis horizontal line"

    # Add value labels on each bar
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            # if positive, label goes above bar; if negative, below
            height + 100 if height >= 0 else height - 500,
            f"PKR {height:,.0f}",
            ha="center",
            fontsize=9,
        )

    ax.set_title("Net Savings by Month", fontsize=14, pad=15)
    ax.set_xlabel("")
    ax.set_ylabel("Net (PKR)", fontsize=11)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

    plt.tight_layout()
    plt.show()

def plot_top_recipients(df: pd.DataFrame):
    from finance_analyzer.analyzer import top_recipients
    # importing inside the function is valid Python
    # useful when you want to avoid circular imports
    # we'll explain this more when the project grows

    recipients = top_recipients(df)

    fig, ax = plt.subplots(figsize=(10, 6))

    sns.barplot(
        data=recipients,
        x="total_sent",
        y="recipient",
        orient="h",
        ax=ax,
        color="#4C72B0",
    )

    for bar in ax.patches:
        ax.text(
            bar.get_width() + 50,
            bar.get_y() + bar.get_height() / 2,
            f"PKR {bar.get_width():,.0f}",
            va="center",
            fontsize=9,
        )

    ax.set_title("Top Recipients — All Months", fontsize=14, pad=15)
    ax.set_xlabel("Total Sent (PKR)", fontsize=11)
    ax.set_ylabel("")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

    plt.tight_layout()
    plt.show()

def plot_spending_by_category(df: pd.DataFrame):
    from finance_analyzer.ml import spending_by_category

    cat_df = spending_by_category(df)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    # 1 row, 2 columns of charts side by side
    # axes is now an array of two ax objects — axes[0] and axes[1]

    # Left chart — bar chart of total by category
    sns.barplot(
        data=cat_df,
        x="total",
        y="category",
        orient="h",
        ax=axes[0],
        color="#4C72B0",
    )
    axes[0].set_title("Total Spending by Category", fontsize=13)
    axes[0].set_xlabel("Total Spent (PKR)")
    axes[0].set_ylabel("")
    axes[0].xaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, _: f"{x:,.0f}")
    )

    for bar in axes[0].patches:
        axes[0].text(
            bar.get_width() + 50,
            bar.get_y() + bar.get_height() / 2,
            f"PKR {bar.get_width():,.0f}",
            va="center", fontsize=8,
        )

    # Right chart — pie chart of category proportions
    axes[1].pie(
        cat_df["total"],
        labels=cat_df["category"],
        autopct="%1.1f%%",
        # autopct adds percentage labels — %1.1f%% means 1 decimal place
        startangle=90,
        # startangle rotates so the first slice starts at the top
    )
    axes[1].set_title("Spending Distribution", fontsize=13)

    plt.tight_layout()
    plt.show()


def plot_anomalies(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(13, 5))

    # Separate normal and anomalous transactions
    normal = df[df["is_anomaly"] == False]
    anomalies = df[df["is_anomaly"] == True]

    # Plot normal transactions as small dots
    ax.scatter(
        normal["timestamp"],
        normal["amount"].abs(),
        color="#4C72B0",
        alpha=0.5,
        s=40,        # s = marker size
        label="Normal",
        zorder=2,    # zorder controls layering — higher = drawn on top
    )

    # Plot anomalies as larger red dots
    ax.scatter(
        anomalies["timestamp"],
        anomalies["amount"].abs(),
        color="#C44E52",
        s=120,
        marker="X",   # X shape makes anomalies visually distinct
        label="Anomaly",
        zorder=3,
    )

    # Add labels next to each anomaly point
    for _, row in anomalies.iterrows():
        # iterrows() lets you loop through a DataFrame row by row
        # _ is the index (we don't need it, so we use _ as a throwaway variable)
        # row is a Series containing that row's values
        ax.annotate(
            f"PKR {abs(row['amount']):,.0f}",
            # annotate() adds a text label with an optional arrow
            xy=(row["timestamp"], abs(row["amount"])),
            # xy = the point to annotate
            xytext=(10, 10),
            # xytext = offset of the text from the point in pixels
            textcoords="offset points",
            fontsize=8,
            color="#C44E52",
        )

    ax.set_title("Transaction Anomalies", fontsize=14, pad=15)
    ax.set_xlabel("Date", fontsize=11)
    ax.set_ylabel("Amount (PKR)", fontsize=11)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.legend()
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.show()

def plot_forecast(forecast_df: pd.DataFrame, metadata: dict):
    fig, ax = plt.subplots(figsize=(12, 6))

    # Split into historical and forecast
    historical = forecast_df[forecast_df["is_forecast"] == False]
    future = forecast_df[forecast_df["is_forecast"] == True]

    # Plot historical as a solid line with dots
    ax.plot(
        historical["month_label"],
        historical["predicted_spending"],
        color="#4C72B0",
        linewidth=2.5,
        marker="o",
        markersize=8,
        label="Actual spending",
        zorder=3,
    )

    # Plot forecast as a dashed line with hollow dots
    # We need to connect the last historical point to the first forecast point
    # so the line doesn't have a gap — we do this by including the last historical point
    bridge = pd.concat([historical.tail(1), future])
    # .tail(1) gets the last row — like array.slice(-1) in JS

    ax.plot(
        bridge["month_label"],
        bridge["predicted_spending"],
        color="#4C72B0",
        linewidth=2,
        marker="o",
        markersize=8,
        linestyle="--",         # dashed line for forecast
        markerfacecolor="white", # hollow dots for forecast points
        markeredgewidth=2,
        label="Forecast",
        zorder=3,
    )

    # Add a shaded region to show uncertainty
    # Since our avg error is known, we shade ± that error around forecast
    avg_error = metadata["avg_loo_error"]
    forecast_indices = range(len(historical), len(forecast_df))
    forecast_x = future["month_label"].tolist()
    forecast_y = future["predicted_spending"].tolist()

    ax.fill_between(
        forecast_x,
        [y - avg_error for y in forecast_y],
        [y + avg_error for y in forecast_y],
        # list comprehension to add/subtract error from each forecast value
        alpha=0.15,
        color="#4C72B0",
        label=f"±PKR {avg_error:,.0f} uncertainty",
    )

    # Add value labels on each point
    for _, row in forecast_df.iterrows():
        ax.annotate(
            f"PKR {row['predicted_spending']:,.0f}",
            xy=(row["month_label"], row["predicted_spending"]),
            xytext=(0, 12),
            textcoords="offset points",
            ha="center",
            fontsize=9,
            color="#4C72B0" if not row["is_forecast"] else "#888888",
        )

    # Add a vertical line separating actual from forecast
    ax.axvline(
        x=len(historical) - 0.5,
        # x position between last historical and first forecast bar
        color="gray",
        linewidth=1,
        linestyle=":",
        alpha=0.7,
    )
    ax.text(
        len(historical) - 0.4,
        ax.get_ylim()[1] * 0.95,
        # ax.get_ylim() returns (min, max) of y axis — [1] gets the max
        "← Actual    Forecast →",
        fontsize=9,
        color="gray",
    )

    trend_direction = "↑ increasing" if metadata["slope"] > 0 else "↓ decreasing"
    ax.set_title(
        f"Monthly Spending Forecast  |  Trend: PKR {abs(metadata['slope']):,.0f}/month {trend_direction}",
        fontsize=13,
        pad=15,
    )
    ax.set_xlabel("")
    ax.set_ylabel("Total Spent (PKR)", fontsize=11)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.legend(fontsize=9)

    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.show()