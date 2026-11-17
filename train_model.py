"""
train_model.py - Membersihkan data, melatih dan mengevaluasi model deteksi
URL phishing, lalu menyimpan model, scaler, dan konfigurasi ke models/.
Cara menjalankan dan alur lengkap: lihat README.
"""

import argparse
import json
import os
import time

import joblib
import matplotlib

matplotlib.use("Agg")  # tanpa jendela GUI, hanya simpan gambar
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    fbeta_score,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import GroupKFold, GroupShuffleSplit, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from utils import FEATURE_NAMES, extract_url_features, get_registered_domain, normalize_url

RANDOM_STATE = 42
CLASS_NAMES = ["Legitimate (0)", "Phishing (1)"]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def banner(text):
    print("\n" + "=" * 62 + f"\n{text}\n" + "=" * 62)


def metrics_at(y_true, proba, threshold):
    pred = (proba >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, pred, labels=[0, 1]).ravel()
    return {
        "threshold": float(threshold),
        "accuracy": float(accuracy_score(y_true, pred)),
        "precision": float(precision_score(y_true, pred, zero_division=0)),
        "recall": float(recall_score(y_true, pred, zero_division=0)),
        "f1": float(f1_score(y_true, pred, zero_division=0)),
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
    }


def build_models():
    """Kandidat model. class_weight dipakai untuk penyeimbangan kelas (hanya di data latih)."""
    models = {
        "LogisticRegression": LogisticRegression(
            max_iter=1000, class_weight="balanced", random_state=RANDOM_STATE
        ),
        "RandomForest": RandomForestClassifier(
            n_estimators=100, max_depth=15, min_samples_leaf=2,
            class_weight="balanced_subsample", n_jobs=-1, random_state=RANDOM_STATE,
        ),
    }
    try:  # XGBoost opsional
        from xgboost import XGBClassifier

        models["XGBoost"] = XGBClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.1, subsample=0.8,
            eval_metric="logloss", n_jobs=-1, random_state=RANDOM_STATE,
        )
    except ImportError:
        print("(xgboost tidak terpasang - dilewati)")
    return models


# ---------------------------------------------------------------------------
# 1. Muat & bersihkan data
# ---------------------------------------------------------------------------
def load_and_clean(path, sample=None):
    banner("1. MEMUAT & MEMBERSIHKAN DATA")
    df = pd.read_json(path)
    url_col = "text" if "text" in df.columns else "url"
    df = df.rename(columns={url_col: "url"})[["url", "label"]]
    report = {"raw_rows": int(len(df))}
    print(f"Data mentah            : {len(df):,} baris")

    df = df.dropna(subset=["url", "label"])
    report["after_dropna"] = int(len(df))
    print(f"Setelah buang null     : {len(df):,}")

    df["url"] = df["url"].astype(str).str.strip()
    df = df[df["url"] != ""]
    df["label"] = df["label"].astype(int)
    df = df[df["label"].isin([0, 1])]

    # Duplikat dicek pada URL TERNORMALISASI (http://a.com/ dan a.com dianggap sama)
    df["norm"] = df["url"].map(normalize_url)
    n_before = len(df)
    conflict = df.groupby("norm")["label"].nunique()
    conflict_keys = conflict[conflict > 1].index
    df = df[~df["norm"].isin(conflict_keys)]
    report["conflicting_label_urls_removed"] = int(n_before - len(df))
    print(f"URL berlabel bertentangan dibuang: {n_before - len(df):,} baris")

    n_before = len(df)
    df = df.drop_duplicates(subset="norm")
    report["duplicates_removed"] = int(n_before - len(df))
    print(f"Duplikat (ternormalisasi) dibuang : {n_before - len(df):,} baris")

    if sample and sample < len(df):
        df = df.sample(sample, random_state=RANDOM_STATE)
        print(f"[--sample] memakai {sample:,} baris acak")

    df = df.reset_index(drop=True)
    report["clean_rows"] = int(len(df))
    report["class_counts"] = {str(k): int(v) for k, v in df["label"].value_counts().sort_index().items()}
    print(f"Data bersih            : {len(df):,} baris")
    print("Distribusi kelas       :", report["class_counts"])
    return df, report


# ---------------------------------------------------------------------------
# 2. EDA
# ---------------------------------------------------------------------------
def run_eda(df, X, outdir, report):
    banner("2. EDA RINGKAS")

    # Bias skema URL (pada URL asli sebelum normalisasi)
    has_scheme = df["url"].str.match(r"^https?://", case=False)
    is_https = df["url"].str.lower().str.startswith("https")
    scheme_tbl = pd.DataFrame(
        {"punya_skema": has_scheme.groupby(df["label"]).mean(),
         "https": is_https.groupby(df["label"]).mean()}
    ).round(3)
    print("Proporsi URL bersekema per kelas (bukti bias pencatatan data):")
    print(scheme_tbl)
    report["scheme_share_by_class"] = scheme_tbl.to_dict()

    # Statistik fitur per kelas
    stats = X.groupby(df["label"]).agg(["mean", "median"]).round(3).T
    stats.to_csv(os.path.join(outdir, "eda_feature_stats_by_class.csv"))

    # Distribusi kelas
    counts = df["label"].value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(4.5, 3.5))
    ax.bar(CLASS_NAMES, counts.values, color=["#4c72b0", "#c44e52"])
    for i, v in enumerate(counts.values):
        ax.text(i, v, f"{v:,}", ha="center", va="bottom", fontsize=9)
    ax.set_ylabel("Jumlah URL")
    ax.set_title("Distribusi kelas")
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "eda_class_distribution.png"), dpi=150)
    plt.close(fig)

    # Distribusi panjang URL & jumlah slash per kelas
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.5))
    for ax, col, hi in zip(axes, ["url_length", "count_slash"], [200, 12]):
        for lab, color in [(0, "#4c72b0"), (1, "#c44e52")]:
            ax.hist(X.loc[df["label"] == lab, col].clip(upper=hi), bins=40, alpha=0.55,
                    color=color, label=CLASS_NAMES[lab], density=True)
        ax.set_title(f"{col} (dipotong di {hi})")
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "eda_feature_distribution.png"), dpi=150)
    plt.close(fig)
    print(f"Gambar & tabel EDA disimpan di {outdir}/")


# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------
def plot_confusion_matrices(y_true, proba, threshold, path):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, t, title in zip(axes, [0.5, threshold], ["Threshold 0.50 (default)", f"Threshold {threshold:.2f} (dituning)"]):
        cm = confusion_matrix(y_true, (proba >= t).astype(int), labels=[0, 1])
        ax.imshow(cm, cmap="Blues")
        for (i, j), v in np.ndenumerate(cm):
            ax.text(j, i, f"{v:,}", ha="center", va="center",
                    color="white" if v > cm.max() / 2 else "black", fontsize=12)
        ax.set_xticks([0, 1], CLASS_NAMES)
        ax.set_yticks([0, 1], CLASS_NAMES)
        ax.set_xlabel("Prediksi model")
        ax.set_ylabel("Aktual")
        ax.set_title(title)
    fig.suptitle("Confusion Matrix pada Data Uji")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_importance(model, path):
    if hasattr(model, "feature_importances_"):
        imp = model.feature_importances_
    elif hasattr(model, "coef_"):
        imp = np.abs(model.coef_[0])
    else:
        return
    order = np.argsort(imp)
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.barh(np.array(FEATURE_NAMES)[order], imp[order], color="#4c72b0")
    ax.set_title("Kepentingan fitur")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="urls.json", help="path file urls.json")
    ap.add_argument("--sample", type=int, default=None, help="pakai N baris acak (uji cepat)")
    ap.add_argument("--folds", type=int, default=5, help="jumlah lipatan GroupKFold")
    ap.add_argument("--beta", type=float, default=1.5,
                    help="beta pada F-beta untuk memilih threshold (>1 = recall lebih penting)")
    ap.add_argument("--outdir", default="reports")
    ap.add_argument("--modeldir", default="models")
    args = ap.parse_args()

    t0 = time.time()
    os.makedirs(args.outdir, exist_ok=True)
    os.makedirs(args.modeldir, exist_ok=True)

    df, report = load_and_clean(args.data, args.sample)

    # --- fitur -------------------------------------------------------------
    banner("3. EKSTRAKSI FITUR")
    X = pd.DataFrame([extract_url_features(u) for u in df["url"]], columns=FEATURE_NAMES)
    y = df["label"].values
    groups = df["url"].map(get_registered_domain).values
    print(f"{X.shape[1]} fitur: {FEATURE_NAMES}")
    print(f"Domain unik: {len(set(groups)):,} dari {len(df):,} URL")
    report["unique_domains"] = int(len(set(groups)))
    report["features"] = FEATURE_NAMES

    run_eda(df, X, args.outdir, report)

    # --- split berdasarkan domain -------------------------------------------
    banner("4. SPLIT DATA (BERDASARKAN DOMAIN)")
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=RANDOM_STATE)
    tr_idx, te_idx = next(gss.split(X, y, groups))
    X_train, X_test = X.iloc[tr_idx], X.iloc[te_idx]
    y_train, y_test = y[tr_idx], y[te_idx]
    g_train = groups[tr_idx]
    overlap = set(groups[tr_idx]) & set(groups[te_idx])
    print(f"Data latih: {len(tr_idx):,} | Data uji: {len(te_idx):,}")
    print(f"Domain yang ada di latih & uji sekaligus: {len(overlap)}  (harus 0)")
    print(f"Proporsi phishing - latih: {y_train.mean():.3f} | uji: {y_test.mean():.3f}")
    assert len(overlap) == 0
    report["split"] = {"train": int(len(tr_idx)), "test": int(len(te_idx)),
                       "phishing_share_train": float(y_train.mean()),
                       "phishing_share_test": float(y_test.mean())}

    # --- validasi silang -------------------------------------------------------
    banner(f"5. VALIDASI SILANG GroupKFold({args.folds}) PADA DATA LATIH")
    cv = GroupKFold(n_splits=args.folds)
    oof = {}
    rows = []
    for name, est in build_models().items():
        ts = time.time()
        pipe = make_pipeline(StandardScaler(), est)  # scaler di-fit ulang per lipatan
        proba = cross_val_predict(pipe, X_train, y_train, cv=cv, groups=g_train,
                                  method="predict_proba", n_jobs=1)[:, 1]
        oof[name] = proba
        m = metrics_at(y_train, proba, 0.5)
        rows.append({"model": name, **{k: round(m[k], 4) for k in ["accuracy", "precision", "recall", "f1"]},
                     "detik": round(time.time() - ts, 1)})
        print(f"  {name:<20} selesai ({rows[-1]['detik']} dtk)")
    cv_table = pd.DataFrame(rows).sort_values("f1", ascending=False).reset_index(drop=True)
    print("\nHasil validasi silang (prediksi out-of-fold, threshold 0.5):")
    print(cv_table.to_string(index=False))
    cv_table.to_csv(os.path.join(args.outdir, "cv_model_comparison.csv"), index=False)
    best_name = cv_table.loc[0, "model"]
    print(f"\nModel terpilih (F1 validasi silang tertinggi): {best_name}")
    report["cv_comparison"] = cv_table.to_dict(orient="records")
    report["selected_model"] = best_name

    # --- threshold (dipilih pada data VALIDASI, bukan data uji) -----------------
    banner(f"THRESHOLD (maksimalkan F{args.beta:g} pada prediksi out-of-fold)")
    grid = np.arange(0.10, 0.91, 0.01)
    scores = [fbeta_score(y_train, (oof[best_name] >= t).astype(int), beta=args.beta) for t in grid]
    threshold = float(round(grid[int(np.argmax(scores))], 2))
    cv_def = metrics_at(y_train, oof[best_name], 0.5)
    cv_tun = metrics_at(y_train, oof[best_name], threshold)
    print(f"threshold 0.50 -> precision {cv_def['precision']:.4f} | recall {cv_def['recall']:.4f}")
    print(f"threshold {threshold:.2f} -> precision {cv_tun['precision']:.4f} | recall {cv_tun['recall']:.4f}")
    report["threshold"] = threshold
    report["beta"] = args.beta

    # --- model akhir -------------------------------------------------------------
    banner("6. MODEL AKHIR & EVALUASI PADA DATA UJI (SEKALI)")
    scaler = StandardScaler().fit(X_train)  # fit hanya pada data latih
    model = clone(build_models()[best_name]).fit(scaler.transform(X_train), y_train)
    proba_test = model.predict_proba(scaler.transform(X_test))[:, 1]

    res_default = metrics_at(y_test, proba_test, 0.5)
    res_tuned = metrics_at(y_test, proba_test, threshold)
    print(f"\n--- Threshold 0.50 ---")
    print(classification_report(y_test, (proba_test >= 0.5).astype(int),
                                target_names=CLASS_NAMES, digits=4))
    print(f"--- Threshold {threshold:.2f} (dipakai aplikasi) ---")
    print(classification_report(y_test, (proba_test >= threshold).astype(int),
                                target_names=CLASS_NAMES, digits=4))
    for tag, r in [("0.50", res_default), (f"{threshold:.2f}", res_tuned)]:
        print(f"Confusion matrix @ {tag}: TN={r['tn']:,} FP={r['fp']:,} FN={r['fn']:,} TP={r['tp']:,}")
    report["test_default_threshold"] = res_default
    report["test_tuned_threshold"] = res_tuned

    plot_confusion_matrices(y_test, proba_test, threshold, os.path.join(args.outdir, "confusion_matrix.png"))
    plot_importance(model, os.path.join(args.outdir, "feature_importance.png"))

    # --- analisis kesalahan -------------------------------------------------------
    banner("7. ANALISIS KESALAHAN (threshold aplikasi)")
    pred = (proba_test >= threshold).astype(int)
    err = pd.DataFrame({"url": df["url"].values[te_idx], "label_aktual": y_test,
                        "prediksi": pred, "skor_phishing": proba_test.round(4)})
    fn = err[(err.label_aktual == 1) & (err.prediksi == 0)].sort_values("skor_phishing")
    fp = err[(err.label_aktual == 0) & (err.prediksi == 1)].sort_values("skor_phishing", ascending=False)
    fn.head(200).assign(jenis="False Negative").pipe(
        lambda a: pd.concat([a, fp.head(200).assign(jenis="False Positive")])
    ).to_csv(os.path.join(args.outdir, "error_analysis.csv"), index=False)
    pd.set_option("display.max_colwidth", 80, "display.width", 140)
    print("\nFalse Negative (phishing lolos) - skor paling rendah:")
    print(fn.head(10)[["url", "skor_phishing"]].to_string(index=False))
    print("\nFalse Positive (URL aman ditandai phishing) - skor paling tinggi:")
    print(fp.head(10)[["url", "skor_phishing"]].to_string(index=False))

    # --- simpan --------------------------------------------------------------------
    banner("8. MENYIMPAN ARTEFAK")
    joblib.dump(model, os.path.join(args.modeldir, "phishing_model.pkl"))
    joblib.dump(scaler, os.path.join(args.modeldir, "scaler.pkl"))
    with open(os.path.join(args.modeldir, "config.json"), "w") as f:
        json.dump({"model_name": best_name, "threshold": threshold,
                   "feature_names": FEATURE_NAMES}, f, indent=2)
    with open(os.path.join(args.outdir, "metrics.json"), "w") as f:
        json.dump(report, f, indent=2)
    print(f"Model   : {args.modeldir}/phishing_model.pkl")
    print(f"Scaler  : {args.modeldir}/scaler.pkl")
    print(f"Config  : {args.modeldir}/config.json  (threshold = {threshold})")
    print(f"Laporan : {args.outdir}/  (confusion_matrix.png, metrics.json, error_analysis.csv, ...)")
    print(f"\nSelesai dalam {time.time() - t0:.0f} detik.")


if __name__ == "__main__":
    main()
