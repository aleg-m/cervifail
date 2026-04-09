import argparse
import sys
# import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import r2_score, mean_squared_error
import warnings
warnings.filterwarnings("ignore")
 
 
def load_data(filepath: str, x_col: str | None, y_col: str | None):
    """Load CSV and extract X/Y columns."""
    try:
        df = pd.read_csv(filepath)
    except FileNotFoundError:
        sys.exit(f"[ERROR] File not found: {filepath}")
    except Exception as e:
        sys.exit(f"[ERROR] Could not read CSV: {e}")
 
    print(f"\n✓ Loaded '{filepath}'  ({len(df)} rows, {len(df.columns)} columns)")
    print(f"  Columns: {list(df.columns)}\n")
 
    # Default to first two columns if none specified
    x_col = x_col or df.columns[0]
    y_col = y_col or df.columns[1]
 
    if x_col not in df.columns:
        sys.exit(f"[ERROR] Column '{x_col}' not found. Available: {list(df.columns)}")
    if y_col not in df.columns:
        sys.exit(f"[ERROR] Column '{y_col}' not found. Available: {list(df.columns)}")
 
    # Drop rows with missing values in the selected columns
    df = df[[x_col, y_col]].dropna()
    X = df[x_col].values.reshape(-1, 1)
    y = df[y_col].values
    return X, y, x_col, y_col
 
 
def fit_polynomial(X, y, degree: int):
    """Apply PolynomialFeatures and fit a LinearRegression model."""
    poly = PolynomialFeatures(degree=degree, include_bias=True)
    X_poly = poly.fit_transform(X)
 
    model = LinearRegression()
    model.fit(X_poly, y)
 
    y_pred = model.predict(X_poly)
    r2 = r2_score(y, y_pred)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
 
    return model, poly, y_pred, r2, rmse
 
 
def print_equation(model, degree: int, x_col: str, y_col: str):
    """Print the fitted polynomial equation."""
    coef = model.coef_          # includes bias term at index 0 from PolynomialFeatures
    intercept = model.intercept_
 
    # PolynomialFeatures with include_bias=True: coef[0] corresponds to x^0 (= 1),
    # but LinearRegression absorbs intercept separately; coef[0] ≈ 0.
    # The meaningful coefficients start at coef[1].
    terms = [f"{intercept:.6f}"]
    for i in range(1, degree + 1):
        c = coef[i]
        sign = "+" if c >= 0 else "-"
        power = f"{x_col}" if i == 1 else f"{x_col}^{i}"
        terms.append(f"{sign} {abs(c):.6f}·{power}")
 
    print("=" * 60)
    print(f"  Polynomial Degree: {degree}")
    print(f"  Fitted Equation:")
    print(f"  {y_col} = " + " ".join(terms))
    print("=" * 60)
 
 
def save_plot(X, y, y_pred, degree: int, x_col: str, y_col: str, filepath: str):
    """Save a scatter + regression curve plot."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("[WARNING] matplotlib not installed — skipping plot.")
        return
 
    # Sort for a smooth curve
    sort_idx = X.flatten().argsort()
    X_sorted = X.flatten()[sort_idx]
    y_pred_sorted = y_pred[sort_idx]
 
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.scatter(X, y, color="#4C72B0", alpha=0.7, s=40, label="Data points", zorder=3)
    ax.plot(X_sorted, y_pred_sorted, color="#DD4444", linewidth=2.5,
            label=f"Poly fit (degree={degree})", zorder=4)
 
    ax.set_xlabel(x_col, fontsize=12)
    ax.set_ylabel(y_col, fontsize=12)
    ax.set_title(f"Polynomial Regression  |  {y_col} vs {x_col}  (degree={degree})", fontsize=13)
    ax.legend(fontsize=11)
    ax.grid(True, linestyle="--", alpha=0.4)
 
    fig.tight_layout()
    fig.savefig(filepath, dpi=150)
    print(f"  Plot saved → {filepath}")
 
 
def main():
    parser = argparse.ArgumentParser(description="Polynomial Linear Regression on CSV data")
    parser.add_argument("--file",   required=True,  help="Path to CSV file")
    parser.add_argument("--x",      default=None,   help="Independent variable column name")
    parser.add_argument("--y",      default=None,   help="Dependent variable column name")
    parser.add_argument("--degree", type=int, default=2, help="Polynomial degree (default: 2)")
    parser.add_argument("--plot",   action="store_true", help="Save a plot of the fit")
    args = parser.parse_args()
 
    if args.degree < 1:
        sys.exit("[ERROR] Degree must be at least 1.")
 
    # ── Load data ──────────────────────────────────────────────────────────────
    X, y, x_col, y_col = load_data(args.file, args.x, args.y)
 
    # ── Fit model ─────────────────────────────────────────────────────────────
    model, poly, y_pred, r2, rmse = fit_polynomial(X, y, args.degree)
 
    # ── Report ────────────────────────────────────────────────────────────────
    print_equation(model, args.degree, x_col, y_col)
    print(f"\n  Goodness of Fit:")
    print(f"    R²   = {r2:.6f}")
    print(f"    RMSE = {rmse:.6f}")
    print()
 
    # ── Optional plot ─────────────────────────────────────────────────────────
    if args.plot:
        plot_path = args.file.rsplit(".", 1)[0] + f"_poly{args.degree}_fit.png"
        save_plot(X, y, y_pred, args.degree, x_col, y_col, plot_path)
 
    # ── Predict new values interactively ──────────────────────────────────────
    print("  Enter a value for prediction (or press Enter to skip):")
    while True:
        raw = input(f"    {x_col} = ").strip()
        if not raw:
            break
        try:
            val = float(raw)
            x_new = poly.transform([[val]])
            pred = model.predict(x_new)[0]
            print(f"    → Predicted {y_col} = {pred:.6f}\n")
        except ValueError:
            print("    [!] Please enter a numeric value.\n")
 
    print("Done.")
 
 
if __name__ == "__main__":
    main()