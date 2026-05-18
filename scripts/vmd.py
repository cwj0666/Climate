#!/usr/bin/env python3
"""
VMD-GARCH/LSTM-LSTM Ensemble (Huang 2021 + Extended)
- VMD: Variational Mode Decomposition into IMF sub-modes
- High-frequency IMFs -> GARCH (volatility-aware)
- Low-frequency IMFs -> LSTM-Attention (trend prediction)
- Mid-frequency -> TCN (or LSTM)
- LSTM Non-linear Ensemble: combine all IMF predictions
- External features: VIX, USD/KRW, Brent
"""
import sys
sys.stdout.reconfigure(line_buffering=True)

import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from datetime import datetime
import os
from pathlib import Path

import optuna
from optuna.samplers import TPESampler
from tqdm.auto import tqdm
from scipy.stats import spearmanr
from sklearn.metrics import balanced_accuracy_score, f1_score
import argparse, json, time

print("="*70)
print("VMD-GARCH/LSTM-LSTM Ensemble (Huang 2021 Extended)")
print("="*70)

# ============================================================================
# Data Loading (same as other models)
# ============================================================================
print("\nLoading selected125 data...")
ROOT = Path(os.environ.get('CLIMATE_ROOT', '/workspace/climate_vmd'))
DATA_DIR = ROOT / 'data' / 'model_inputs'
OUT_ROOT = ROOT / 'outputs' / 'team_vmd'
OUT_ROOT.mkdir(parents=True, exist_ok=True)

matrix_path = DATA_DIR / 'selected_feature_matrix.parquet'
manifest_path = DATA_DIR / 'selected_feature_manifest.csv'
features_df = pd.read_parquet(matrix_path)
manifest_df = pd.read_csv(manifest_path)
all_features = manifest_df['feature'].tolist()
TARGET = 'target_logret_60d'

df = features_df.copy().dropna(subset=[TARGET]).sort_values('trd_dd').reset_index(drop=True)
# Keep only selected feature contract. Median imputation matches teammate code style.
X_full = df[all_features].apply(pd.to_numeric, errors='coerce')
X_full = X_full.fillna(X_full.median(numeric_only=True)).fillna(0.0)
y_raw = df[TARGET].astype(float).copy()
dates_raw = pd.to_datetime(df['trd_dd']).copy()

print(f"Samples: {len(y_raw):,}, Feature dim: {X_full.shape[1]}")
print(f"Date range: {dates_raw.min()} ~ {dates_raw.max()}")
print("Fold contract: initial_train=365, test_size=60, expanding walk-forward")
# ============================================================================
# VMD Decomposition
# ============================================================================
try:
    from vmdpy import VMD
    HAS_VMD = True
    print("VMD library available")
except ImportError:
    HAS_VMD = False
    print("WARNING: vmdpy not installed - attempting pip install...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "vmdpy"],
                   capture_output=True)
    try:
        from vmdpy import VMD
        HAS_VMD = True
        print("VMD installed successfully")
    except ImportError:
        print("ERROR: Cannot install vmdpy - VMD decomposition disabled")

def vmd_decompose(signal, K=5, alpha=2000, tau=0, DC=0, init=1, tol=1e-7):
    """
    Variational Mode Decomposition.

    Parameters:
    - K: number of modes (typically 5-8 for financial series)
    - alpha: bandwidth constraint (2000-10000, higher = narrower bands)
    - tau: noise tolerance
    """
    if not HAS_VMD:
        print("VMD not available, returning single-mode")
        return [np.array(signal, dtype=np.float64)]

    signal_array = np.array(signal, dtype=np.float64)
    try:
        u, u_hat, omega = VMD(signal_array, alpha, tau, K, DC, init, tol)
        print(f"  VMD decomposed into {K} modes")
        return [u[i, :] for i in range(K)]
    except Exception as e:
        print(f"  VMD failed ({e}), returning single mode")
        return [signal_array]

# ============================================================================
# GARCH Model (for high-frequency IMFs)
# ============================================================================
from arch import arch_model

class GARCHForecaster:
    """GARCH forecaster for high-frequency IMF components."""
    def __init__(self, vol='GARCH', p=1, q=1):
        self.vol = vol
        self.p = p
        self.q = q

    def fit(self, series):
        self.model = arch_model(series.values, vol=self.vol, p=self.p, q=self.q,
                                rescale=False)
        try:
            self.result = self.model.fit(disp='off', show_warning=False, options={'maxiter': 100})
        except Exception:
            # If it fails completely, fallback to naive constant variance
            self.result = None
        return self

    def predict(self, n_steps=1):
        forecast = self.result.forecast(horizon=n_steps)
        mean = np.sqrt(forecast.variance.values[-1, 0])  # Volatility prediction
        return mean

# ============================================================================
# LSTM-Attention Model (for low-frequency IMFs)
# ============================================================================
class AttentionLayer(nn.Module):
    def __init__(self, hidden_dim):
        super().__init__()
        self.attention = nn.MultiheadAttention(hidden_dim, num_heads=4)
        self.layer_norm = nn.LayerNorm(hidden_dim)

    def forward(self, x):
        # x: (batch, seq_len, hidden)
        x_perm = x.permute(1, 0, 2)  # (seq, batch, hidden)
        attn_out, _ = self.attention(x_perm, x_perm, x_perm)
        attn_out = attn_out.permute(1, 0, 2)  # (batch, seq, hidden)
        return self.layer_norm(x + attn_out)

class LSTMAttention(nn.Module):
    def __init__(self, input_dim, hidden_dim, num_layers=2, dropout=0.2,
                 use_attention=True):
        super().__init__()
        self.use_attention = use_attention

        self.lstm = nn.LSTM(
            input_dim, hidden_dim, num_layers=num_layers,
            batch_first=True, dropout=dropout if num_layers > 1 else 0,
            bidirectional=True
        )

        lstm_out = hidden_dim * 2  # bidirectional
        if use_attention:
            self.attention = AttentionLayer(lstm_out)

        self.fc = nn.Sequential(
            nn.Linear(lstm_out, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1)
        )

    def forward(self, x):
        # x: (batch, seq_len, features)
        lstm_out, _ = self.lstm(x)
        if self.use_attention:
            lstm_out = self.attention(lstm_out)
        out = self.fc(lstm_out[:, -1, :])  # Last time step
        return out

# ============================================================================
# Non-linear LSTM Ensemble
# ============================================================================
class NonlinearEnsemble(nn.Module):
    """
    LSTM-based non-linear ensemble (Huang 2021 + Extended).
    Takes predictions from all IMF models + external features and combines them.
    When n_features > 0, acts as regime-aware combiner (VIX, rates, etc.).
    """
    def __init__(self, n_models, hidden_dim=32, n_features=0):
        super().__init__()
        self.n_features = n_features
        input_dim = n_models + n_features
        self.lstm = nn.LSTM(input_dim, hidden_dim, batch_first=True,
                            bidirectional=True)
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )

    def forward(self, preds, features=None):
        # preds: (batch, n_models) or (batch, seq, n_models)
        if preds.dim() == 2:
            preds = preds.unsqueeze(1)
        # Concatenate features if provided
        if features is not None and self.n_features > 0:
            if features.dim() == 2:
                features = features.unsqueeze(1)
            preds = torch.cat([preds, features], dim=-1)
        lstm_out, _ = self.lstm(preds)
        return self.fc(lstm_out[:, -1, :])

# ============================================================================
# Full VMD-GARCH/LSTM-LSTM Pipeline
# ============================================================================
class VMDGARCHLSTMEnsemble:
    """Complete VMD-GARCH/LSTM-LSTM ensemble pipeline."""

    def __init__(self, K=6, alpha=2000, lstm_hidden=64, lstm_layers=2,
                 lstm_dropout=0.2, use_attention=True,
                 ensemble_hidden=32, n_ext_features=0):
        self.K = K
        self.alpha = alpha
        self.lstm_hidden = lstm_hidden
        self.lstm_layers = lstm_layers
        self.lstm_dropout = lstm_dropout
        self.use_attention = use_attention
        self.ensemble_hidden = ensemble_hidden
        self.n_ext_features = n_ext_features

        self.imf_models = {}  # IMF index -> model
        self.ensemble = None
        self.scaler_y = StandardScaler()
        self.scaler_X = StandardScaler() if n_ext_features > 0 else None

    def fit(self, y_series, X_series=None, window_size=30, batch_size=32,
            epochs=30, lr=0.001, device='cpu'):
        """Train the complete ensemble pipeline.

        Parameters:
        - y_series: target price series
        - X_series: external features (VIX, 환율, Brent 등), shape (n_samples, n_features)
        """
        # Step 1: VMD decomposition
        print(f"  VMD decomposition: K={self.K}, alpha={self.alpha}")
        imfs = vmd_decompose(y_series, K=self.K, alpha=self.alpha)
        actual_K = len(imfs)
        print(f"  Decomposed into {actual_K} modes")

        # Step 2: Assign models to each IMF by frequency
        # Frequency estimation: count zero-crossings
        frequencies = []
        for imf in imfs:
            zero_crossings = np.sum(np.diff(np.signbit(imf)))
            frequencies.append(zero_crossings)

        # Sort IMFs by frequency (higher zero-crossings = higher frequency)
        sorted_idx = np.argsort(frequencies)[::-1]
        n_high = max(1, actual_K // 3)       # Top 1/3: high freq -> GARCH
        n_mid = max(1, actual_K // 3)        # Mid 1/3:  mid freq -> TCN/LSTM
        n_low = actual_K - n_high - n_mid     # Low 1/3:  low freq -> LSTM-Attention

        print(f"  Freq assignments: {n_high} GARCH + {n_mid} mid + {n_low} LSTM-Attn")

        # Guard: ensure all counts are valid
        if n_low < 0:
            n_low = 0
            n_mid = actual_K - n_high
        if n_mid < 0:
            n_mid = 0
            n_high = actual_K

        # Train models for each IMF
        imf_preds_train = []  # Store training predictions from each model

        for i, idx in enumerate(sorted_idx):
            imf = imfs[idx]
            scaler_imf = StandardScaler()
            imf_scaled = scaler_imf.fit_transform(imf.reshape(-1, 1)).flatten()

            # Create sequences
            X_seq, y_seq = [], []
            for t in range(len(imf_scaled) - window_size):
                X_seq.append(imf_scaled[t:t+window_size])
                y_seq.append(imf_scaled[t+window_size])

            if len(X_seq) < 5:
                # Not enough data, use naive persistence
                pred = np.zeros(len(y_seq)) if len(y_seq) > 0 else np.array([0])
                imf_preds_train.append(pred)
                self.imf_models[idx] = ('persistence', None)
                continue

            X_arr = np.array(X_seq)
            y_arr = np.array(y_seq)

            if i < n_high:
                # GARCH for high frequency
                try:
                    garch = GARCHForecaster(vol='GARCH', p=1, q=1)
                    garch.fit(pd.Series(imf))
                    # Back-test predictions
                    pred = np.zeros(len(y_arr))
                    for t in range(len(y_arr)):
                        if t >= window_size:
                            garch.fit(pd.Series(imf[:t]))
                        pred[t] = garch.predict(1)
                    imf_preds_train.append(pred)
                    self.imf_models[idx] = ('garch', garch)
                except:
                    pred = np.mean(y_arr) * np.ones(len(y_arr))
                    imf_preds_train.append(pred)
                    self.imf_models[idx] = ('mean', None)

            elif i < n_high + n_mid:
                # Mid frequency: simple LSTM (or TCN)
                lstm = LSTMAttention(1, self.lstm_hidden // 2,
                                     num_layers=1, dropout=self.lstm_dropout,
                                     use_attention=False).to(device)

                X_tensor = torch.FloatTensor(X_arr).reshape(-1, window_size, 1).to(device)
                y_tensor = torch.FloatTensor(y_arr).reshape(-1, 1).to(device)

                optimizer = torch.optim.Adam(lstm.parameters(), lr=lr)
                criterion = nn.HuberLoss()

                for _ in range(epochs):
                    lstm.train()
                    optimizer.zero_grad()
                    pred_t = lstm(X_tensor)
                    loss = criterion(pred_t, y_tensor)
                    loss.backward()
                    optimizer.step()

                lstm.eval()
                with torch.no_grad():
                    pred = lstm(X_tensor).cpu().numpy().flatten()
                imf_preds_train.append(pred)
                self.imf_models[idx] = ('lstm_simple', lstm)

            else:
                # Low frequency: LSTM-Attention
                lstm_attn = LSTMAttention(1, self.lstm_hidden,
                                          num_layers=self.lstm_layers,
                                          dropout=self.lstm_dropout,
                                          use_attention=self.use_attention).to(device)

                X_tensor = torch.FloatTensor(X_arr).reshape(-1, window_size, 1).to(device)
                y_tensor = torch.FloatTensor(y_arr).reshape(-1, 1).to(device)

                dataset = TensorDataset(X_tensor, y_tensor)
                loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

                optimizer = torch.optim.Adam(lstm_attn.parameters(), lr=lr)
                criterion = nn.HuberLoss()

                for _ in range(epochs):
                    for bx, by in loader:
                        bx, by = bx.to(device), by.to(device)
                        optimizer.zero_grad()
                        loss = criterion(lstm_attn(bx), by)
                        loss.backward()
                        optimizer.step()

                lstm_attn.eval()
                with torch.no_grad():
                    pred = lstm_attn(X_tensor).cpu().numpy().flatten()
                imf_preds_train.append(pred)
                self.imf_models[idx] = ('lstm_attn', lstm_attn)

        # Step 3: Train Non-linear Ensemble (with external features)
        min_len = min(len(p) for p in imf_preds_train)
        ensemble_X = np.column_stack([p[:min_len] for p in imf_preds_train])
        ensemble_y = y_series.values[window_size:window_size+min_len]

        # Scale external features if available
        if X_series is not None and self.n_ext_features > 0:
            X_aligned = X_series.values[window_size:window_size+min_len]
            X_scaled = self.scaler_X.fit_transform(X_aligned)
            feat_tensor = torch.FloatTensor(X_scaled).to(device)
        else:
            feat_tensor = None

        X_ens = torch.FloatTensor(ensemble_X).reshape(-1, 1, actual_K).to(device)
        y_ens = torch.FloatTensor(ensemble_y).reshape(-1, 1).to(device)

        self.ensemble = NonlinearEnsemble(
            actual_K, self.ensemble_hidden, self.n_ext_features).to(device)
        optimizer = torch.optim.Adam(self.ensemble.parameters(), lr=lr * 0.5)
        criterion = nn.HuberLoss()

        for _ in range(epochs):
            optimizer.zero_grad()
            loss = criterion(self.ensemble(X_ens, feat_tensor), y_ens)
            loss.backward()
            optimizer.step()

        self.ensemble.eval()

        return self

    def predict(self, y_series, X_last=None, n_steps=1):
        """Predict next n_steps values.

        Parameters:
        - y_series: target price series
        - X_last: latest external features (shape: (1, n_features))
        """
        # Re-run VMD on entire series
        imfs = vmd_decompose(y_series, K=self.K, alpha=self.alpha)

        imf_predictions = []
        for idx in sorted(self.imf_models.keys()):
            imf = imfs[idx]
            model_type, model = self.imf_models[idx]

            if model_type == 'garch' and model is not None:
                model.fit(pd.Series(imf))
                pred = model.predict(n_steps)
            elif model_type in ('lstm_simple', 'lstm_attn') and model is not None:
                # Use last window for prediction
                window_size = 30
                last_window = imf[-window_size:]
                X_pred = torch.FloatTensor(last_window).reshape(1, window_size, 1)
                # Move to same device as model
                device = next(model.parameters()).device
                X_pred = X_pred.to(device)
                model.eval()
                with torch.no_grad():
                    pred = model(X_pred).item()
            else:
                pred = imf[-1] if len(imf) > 0 else 0

            imf_predictions.append(pred)

        # Ensemble prediction with external features
        X_ens_pred = torch.FloatTensor(imf_predictions).reshape(1, 1, -1)
        if X_last is not None and self.n_ext_features > 0:
            X_last_scaled = self.scaler_X.transform(X_last.reshape(1, -1))
            feat_pred = torch.FloatTensor(X_last_scaled)
        else:
            feat_pred = None
        # Move to ensemble device
        ens_device = next(self.ensemble.parameters()).device
        X_ens_pred = X_ens_pred.to(ens_device)
        if feat_pred is not None:
            feat_pred = feat_pred.to(ens_device)
        with torch.no_grad():
            final_pred = self.ensemble(X_ens_pred, feat_pred).item()

        return final_pred

# ============================================================================
# Training function for one fold
# ============================================================================
def train_vmd_ensemble(y_train, y_test, X_train=None, X_test=None,
                       params=None, mlflow_run_name=None, fold_num=0):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"  Device: {device}")

    n_ext = X_train.shape[1] if X_train is not None else 0
    model = VMDGARCHLSTMEnsemble(
        K=params['vmd_K'],
        alpha=params['vmd_alpha'],
        lstm_hidden=params['lstm_hidden'],
        lstm_layers=params['lstm_layers'],
        lstm_dropout=params['dropout'],
        use_attention=params['use_attention'],
        ensemble_hidden=params['ensemble_hidden'],
        n_ext_features=n_ext
    )

    # Fit on training data
    model.fit(
        y_train,
        X_series=X_train,
        window_size=params['window_size'],
        batch_size=params['batch_size'],
        epochs=params['epochs'],
        lr=params.get('learning_rate', params.get('lr', 0.001)),
        device=device
    )

    # Predict on test data (point-by-point for walk-forward integrity)
    predictions = []
    for i in tqdm(range(len(y_test)), desc=f'fold {fold_num} predict', leave=False):
        history = pd.concat([y_train, y_test.iloc[:i]])
        X_last = X_test.iloc[i].values if X_test is not None else None
        pred = model.predict(history, X_last=X_last)
        predictions.append(pred)

    y_pred = np.array(predictions)
    y_test_arr = y_test.values[:len(y_pred)]

    rmse = np.sqrt(mean_squared_error(y_test_arr, y_pred))
    mae = mean_absolute_error(y_test_arr, y_pred)
    r2 = r2_score(y_test_arr, y_pred)
    wape = (np.sum(np.abs(y_test_arr - y_pred)) /
            np.sum(np.abs(y_test_arr))) * 100 if np.sum(np.abs(y_test_arr)) != 0 else 0.0
    hit_rate = float(np.mean(np.sign(y_pred) == np.sign(y_test_arr)) * 100)

    print(f"  Fold {fold_num}: RMSE={rmse:.4f}, MAE={mae:.4f}, R2={r2:.4f}, WAPE={wape:.1f}%  Hit={hit_rate:.1f}%")

    return {'rmse': rmse, 'mae': mae, 'r2': r2, 'wape': wape, 'hit_rate': hit_rate,
            'y_test': y_test_arr, 'y_pred': y_pred}, model

# ============================================================================
# Metrics and execution
# ============================================================================
OPTUNA_EPOCHS = 15
RUN_DIR = None
SHARD = 0


def extra_metrics(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    out = {}
    out['rmse'] = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    out['mae'] = float(mean_absolute_error(y_true, y_pred))
    out['r2'] = float(r2_score(y_true, y_pred))
    out['wape'] = float(np.sum(np.abs(y_true-y_pred))/np.sum(np.abs(y_true))*100) if np.sum(np.abs(y_true)) else np.nan
    out['hit_rate'] = float(np.mean(np.sign(y_pred)==np.sign(y_true)))
    out['balanced_accuracy'] = float(balanced_accuracy_score((y_true>0).astype(int),(y_pred>0).astype(int))) if len(np.unique(y_true>0))>1 else np.nan
    out['macro_f1'] = float(f1_score((y_true>0).astype(int),(y_pred>0).astype(int),average='macro',zero_division=0))
    out['correlation'] = float(np.corrcoef(y_true, y_pred)[0,1]) if len(y_true)>1 and np.std(y_pred)>0 and np.std(y_true)>0 else np.nan
    out['ic'] = float(spearmanr(y_true, y_pred, nan_policy='omit').statistic) if len(y_true)>1 else np.nan
    return out


def objective(trial):
    params = {
        'vmd_K': trial.suggest_int('vmd_K', 4, 8),
        'vmd_alpha': trial.suggest_categorical('vmd_alpha', [1000, 2000, 5000, 10000]),
        'window_size': trial.suggest_int('window_size', 20, 60, step=10),
        'lstm_hidden': trial.suggest_categorical('lstm_hidden', [32, 64, 128]),
        'lstm_layers': trial.suggest_int('lstm_layers', 1, 3),
        'dropout': trial.suggest_float('dropout', 0.1, 0.4),
        'use_attention': trial.suggest_categorical('use_attention', [True, False]),
        'ensemble_hidden': trial.suggest_categorical('ensemble_hidden', [16, 32, 64]),
        'learning_rate': trial.suggest_float('lr', 5e-4, 5e-3, log=True),
        'batch_size': trial.suggest_categorical('batch_size', [16, 32]),
        'epochs': OPTUNA_EPOCHS,
    }
    test_size = 60
    test_start = min(500, len(y_raw) - test_size - 50)
    test_end = test_start + test_size
    try:
        results, _ = train_vmd_ensemble(
            y_raw.iloc[:test_start], y_raw.iloc[test_start:test_end],
            X_train=X_full.iloc[:test_start], X_test=X_full.iloc[test_start:test_end],
            params=params, mlflow_run_name=None, fold_num=0)
        m = extra_metrics(results['y_test'], results['y_pred'])
        row = {'shard': SHARD, 'trial': trial.number, 'objective_wape': results['wape'], **m, 'params_json': json.dumps(params)}
        pd.DataFrame([row]).to_csv(RUN_DIR/'trial_partial.csv', mode='a', header=not (RUN_DIR/'trial_partial.csv').exists(), index=False)
        return results['wape']
    except Exception as e:
        print(f"  Trial {trial.number} failed: {str(e)[:120]}", flush=True)
        return float('inf')


def run_optuna(n_trials=20, shard=0):
    print("\n" + "="*70)
    print(f"VMD-GARCH-LSTM Optuna shard={shard}, trials={n_trials}")
    print("="*70)
    study = optuna.create_study(direction='minimize', sampler=TPESampler(seed=42+shard))
    study.optimize(objective, n_trials=n_trials, show_progress_bar=True)
    print(f"\nBest Trial #{study.best_trial.number}")
    print(f"Best WAPE: {study.best_value:.2f}%")
    return study


def run_folds(best_params):
    print("\n" + "="*70)
    print("Walk-Forward Dynamic-Fold Validation with Best Params")
    print("="*70)
    all_results = []
    test_size = 60
    initial_train = 365
    test_start = initial_train
    fold_idx = 0
    total_folds = sum(1 for s in range(initial_train, len(y_raw)-test_size+1, test_size))
    pbar = tqdm(total=total_folds, desc=f'shard {SHARD} final folds')
    while test_start + test_size <= len(y_raw):
        fold_idx += 1
        test_end = min(test_start + test_size, len(y_raw))
        print(f"\nFold {fold_idx}: Train [0:{test_start}], Test [{test_start}:{test_end}]", flush=True)
        results, _ = train_vmd_ensemble(
            y_raw.iloc[:test_start], y_raw.iloc[test_start:test_end],
            X_train=X_full.iloc[:test_start], X_test=X_full.iloc[test_start:test_end],
            params=best_params, mlflow_run_name=None, fold_num=fold_idx)
        m = extra_metrics(results['y_test'], results['y_pred'])
        m.update({'shard': SHARD, 'fold': fold_idx, 'train_rows': test_start, 'test_rows': test_end-test_start, 'params_json': json.dumps(best_params)})
        pd.DataFrame([m]).to_csv(RUN_DIR/'by_fold.csv', mode='a', header=not (RUN_DIR/'by_fold.csv').exists(), index=False)
        pred_df = pd.DataFrame({'shard': SHARD, 'fold': fold_idx, 'trd_dd': dates_raw.iloc[test_start:test_end].to_numpy(), 'actual': results['y_test'], 'prediction': results['y_pred']})
        pred_df.to_parquet(RUN_DIR/f'pred_fold_{fold_idx:02d}.parquet', index=False)
        all_results.append(results)
        test_start = test_end
        pbar.update(1)
    pbar.close()
    return all_results


def save_summary(all_results, best_params, study):
    all_y_test = np.concatenate([r['y_test'] for r in all_results])
    all_y_pred = np.concatenate([r['y_pred'] for r in all_results])
    m = extra_metrics(all_y_test, all_y_pred)
    m.update({'shard': SHARD, 'n_folds': len(all_results), 'best_trial': study.best_trial.number, 'best_value_wape': float(study.best_value), 'params_json': json.dumps(best_params)})
    pd.DataFrame([m]).to_csv(RUN_DIR/'summary.csv', index=False)
    (RUN_DIR/'DONE').write_text(json.dumps(m, indent=2))
    print(json.dumps(m, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--shard', type=int, required=True)
    parser.add_argument('--n-trials', type=int, default=20)
    parser.add_argument('--run-id', default=None)
    args = parser.parse_args()
    SHARD = args.shard
    run_id = args.run_id or f'vmd_shard{SHARD}'
    RUN_DIR = OUT_ROOT / run_id
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    print(f"RUN_DIR={RUN_DIR}")
    study = run_optuna(n_trials=args.n_trials, shard=SHARD)
    best_params = study.best_params
    best_params['epochs'] = 40
    all_results = run_folds(best_params)
    save_summary(all_results, best_params, study)
    print("Done! VMD-GARCH-LSTM shard complete.", flush=True)
