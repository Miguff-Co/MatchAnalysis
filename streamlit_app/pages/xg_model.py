import streamlit as st
import pandas as pd
import numpy as np
import sys
import os
import matplotlib.pyplot as plt
import seaborn as sns
import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import brier_score_loss, confusion_matrix, classification_report, precision_score, recall_score, f1_score
from Models import XGmodel

st.set_page_config(page_title="xG Model", page_icon="⚽", layout="wide")

st.title("Expected Goals (xG) Model")

st.markdown("""
Az xG (expected goals) modell azt becsüli, hogy egy lövés mekkora valószínűséggel lesz gól a lövés jellemzői alapján.

**Használt jellemzők:**
- `x`, `y` — Játékos koordinátái
- `shot_angle_deg` — Lövés szöge
- `situation` — Hogyan kapta a labdát (pl. passz, szabálytalanság)
- `bodyPart` — Melyik testréssel lőtt
""")

# --- Data loading ---
st.subheader("Adatok betöltése")

# List files in Output folder
output_dir = "Output"
if os.path.exists(output_dir):
    available_files = [f for f in os.listdir(output_dir) if f.endswith('.xlsx')]
else:
    available_files = []
    st.warning(f"Output mappa nem található: {output_dir}")

col1, col2 = st.columns([2, 1])

with col1:
    if available_files:
        train_files = st.multiselect(
            "Tanító adatok (több fájl is választható)",
            available_files,
            default=[available_files[0]] if available_files else [],
            help="Válassz ki fájlokat a tanításhoz. Több fájl is választható."
        )
    else:
        train_files = []

with col2:
    if available_files:
        val_file = st.selectbox(
            "Validációs adatok",
            ["-- Válassz --"] + available_files,
            index=0,
            help="Egy fájl a validációhoz."
        )
    else:
        val_file = "-- Válassz --"

# Or upload custom files
with st.expander("Vagy tölts fel saját fájlokat"):
    uploaded_train = st.file_uploader("Tanító fájlok (több is)", type=["xlsx"], accept_multiple_files=True)
    uploaded_val = st.file_uploader("Validációs fájl", type=["xlsx"])

# Determine which files to use
if uploaded_train:
    train_data_files = uploaded_train
elif train_files:
    train_data_files = [os.path.join(output_dir, f) for f in train_files]
else:
    train_data_files = []

if uploaded_val:
    val_data_file = uploaded_val
elif val_file != "-- Válassz --":
    val_data_file = os.path.join(output_dir, val_file)
else:
    val_data_file = None

# Load training data
if train_data_files:
    try:
        train_dfs = []
        for f in train_data_files:
            if isinstance(f, str):
                df = pd.read_excel(f, index_col=0)
            else:
                df = pd.read_excel(f, index_col=0)
            train_dfs.append(df)
        shot_data_df = pd.concat(train_dfs, ignore_index=True)
        st.success(f"Tanító adatok betöltve: {len(shot_data_df)} lövés ({len(train_data_files)} fájlból)")
    except Exception as e:
        st.error(f"Hiba a tanító adatok betöltésekor: {e}")
        st.stop()
else:
    st.warning("Válassz ki tanító adatokat!")
    st.stop()

# Load validation data
if val_data_file:
    try:
        if isinstance(val_data_file, str):
            val_df = pd.read_excel(val_data_file, index_col=0)
        else:
            val_df = pd.read_excel(val_data_file, index_col=0)
        st.success(f"Validációs adatok betöltve: {len(val_df)} lövés")
    except Exception as e:
        st.error(f"Hiba a validációs adatok betöltésekor: {e}")
        val_df = None
else:
    val_df = None
    st.info("Nincs validációs adat kiválasztva (opcionális)")

st.dataframe(shot_data_df.head(), use_container_width=True)

# --- Check required columns ---
required_cols = ["x", "y", "shot_angle_deg", "situation", "bodyPart", "goal"]
missing_cols = [col for col in required_cols if col not in shot_data_df.columns]
if missing_cols:
    st.error(f"Hiányzó oszlopok: {missing_cols}")
    st.stop()

# --- Model configuration ---
st.divider()
st.subheader("Modell konfiguráció")

col1, col2 = st.columns(2)

with col1:
    model_type = st.selectbox(
        "Modell típusa",
        ["Deep Learning", "GradientDescent", "Logistic Regression"],
        index=0,
        help="A használt algoritmus típusa."
    )

with col2:
    num_iters = st.number_input("Iterációk száma", min_value=10, max_value=1000, value=30, step=10)

test_size = st.slider("Test set aránya (tanító adatokból)", min_value=0.1, max_value=0.5, value=0.3, step=0.05)

# --- Train button ---
if st.button("Modell tanítása", type="primary"):
    with st.spinner("Adatok előkészítése..."):
        # Encode categorical variables
        le_situation = LabelEncoder()
        le_body = LabelEncoder()

        goal_map = {"goal": 1, "no goal": 0}

        shot_data_df["situation_enc"] = le_situation.fit_transform(shot_data_df["situation"])
        shot_data_df["bodyPart_enc"] = le_body.fit_transform(shot_data_df["bodyPart"])
        shot_data_df["goal_enc"] = shot_data_df["goal"].map(goal_map)

        # Drop original categorical columns
        X = shot_data_df[["x", "y", "shot_angle_deg", "situation_enc", "bodyPart_enc"]]
        Y = shot_data_df["goal_enc"]

        # Train-test split from training data
        X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=test_size, random_state=42)

        X_train = X_train.to_numpy()
        y_train = y_train.to_numpy()
        X_test = X_test.to_numpy()
        y_test = y_test.to_numpy()

        # Prepare validation data if provided
        if val_df is not None:
            val_df["situation_enc"] = le_situation.transform(val_df["situation"])
            val_df["bodyPart_enc"] = le_body.transform(val_df["bodyPart"])
            val_df["goal_enc"] = val_df["goal"].map(goal_map)

            X_val = val_df[["x", "y", "shot_angle_deg", "situation_enc", "bodyPart_enc"]].to_numpy()
            y_val = val_df["goal_enc"].to_numpy()

    progress_bar = st.progress(0, text="Modell tanítása folyamatban...")
    
    model = XGmodel(model_type=model_type, num_iters=int(num_iters))
    
    # Use a wrapper to update progress during training
    if model_type == "GradientDescent":
        # Manually run gradient descent with progress updates
        from Models.GradiantDescentModel import GradianDescentModel
        gd_model = model.model
        
        # Preprocess data
        if gd_model.normalize_data:
            X_train_proc = (X_train - X_train.mean(axis=0)) / X_train.std(axis=0)
            gd_model.mean = X_train.mean(axis=0)
            gd_model.std = X_train.std(axis=0)
        else:
            X_train_proc = X_train
        
        X_train_proc = np.column_stack((np.ones(X_train_proc.shape[0]), X_train_proc))
        
        # Initialize weights
        if gd_model.random_init_weight:
            gd_model.w = np.random.rand(X_train_proc.shape[1], 1)
        else:
            gd_model.w = np.zeros((X_train_proc.shape[1], 1))
        
        # Training loop with progress updates
        for i in range(int(num_iters)):
            C, grad = gd_model.costFunction(gd_model.w, X_train_proc, y_train)
            gd_model.w = gd_model.w - gd_model.lr * grad
            
            if i % max(1, int(num_iters) // 10) == 0:
                progress = (i + 1) / int(num_iters)
                progress_bar.progress(progress, text=f"Modell tanítása: {int(progress * 100)}% (Loss: {C:.2f})")
        
        progress_bar.progress(1.0, text="Modell tanítása kész!")
        
    elif model_type == "Deep Learning":
        # For deep learning, manually run training with progress updates
        from Models.DeepLearningModel import DeepLearningModel
        dl_model = model.model
        
        # Convert to tensors
        X_train_tensor = torch.tensor(X_train, dtype=torch.float32)
        y_train_tensor = torch.tensor(y_train, dtype=torch.float32)
        
        from torch.utils.data import DataLoader, TensorDataset
        ds = TensorDataset(X_train_tensor, y_train_tensor)
        dl = DataLoader(ds, batch_size=32, shuffle=True)
        
        dl_model.train()
        for epoch in range(int(num_iters)):
            total_loss = 0.0
            for xb, yb in dl:
                logits = dl_model(xb)
                loss = dl_model.lossfn(logits, yb)
                
                dl_model.optimizer.zero_grad()
                loss.backward()
                dl_model.optimizer.step()
                
                total_loss += loss.item() * xb.size(0)
            avg_loss = total_loss / len(ds)
            
            if epoch % max(1, int(num_iters) // 10) == 0:
                progress = (epoch + 1) / int(num_iters)
                progress_bar.progress(progress, text=f"Modell tanítása: {int(progress * 100)}% (Loss: {avg_loss:.6f})")
        
        progress_bar.progress(1.0, text="Modell tanítása kész!")
    else:
        # Logistic Regression - sklearn
        model.fit(X_train, y_train)
        progress_bar.progress(1.0, text="Modell tanítása kész!")
    
    predictions, probabilities = model.predict(X_test)

    # Calculate metrics for test set
    brier_loss = round(brier_score_loss(y_test, probabilities), 4)
    accuracy = round((predictions == y_test).mean(), 4)

    st.success("Modell tanítása kész!")

    # Display results
    st.divider()
    st.subheader("Eredmények")

    # Test set metrics
    col1, col2 = st.columns(2)
    col1.metric("Test Brier Score Loss", brier_loss, help="Minél alacsonyabb, annál jobb a modell (0-1 skálán)")
    col2.metric("Test Pontosság", f"{accuracy:.1%}")

    # Validation metrics
    if val_df is not None:
        st.divider()
        st.subheader("Validációs eredmények")

        val_predictions, val_probabilities = model.predict(X_val)
        val_brier_loss = round(brier_score_loss(y_val, val_probabilities), 4)
        val_accuracy = round((val_predictions == y_val).mean(), 4)

        col3, col4 = st.columns(2)
        col3.metric("Validációs Brier Score Loss", val_brier_loss)
        col4.metric("Validációs Pontosság", f"{val_accuracy:.1%}")

        # Show validation predictions table
        st.markdown("**Validációs predikciók:**")
        
        # Create a copy of val_df with predictions
        val_results = val_df.copy()
        val_results["predicted_prob"] = val_probabilities.flatten()
        val_results["predicted_class"] = val_predictions
        val_results["actual_class"] = y_val
        val_results["correct"] = val_results["predicted_class"] == val_results["actual_class"]
        
        # Add readable columns
        val_results["actual_goal"] = val_results["actual_class"].map({1: "goal", 0: "no goal"})
        val_results["predicted_goal"] = val_results["predicted_class"].map({1: "goal", 0: "no goal"})
        val_results["result"] = val_results["correct"].map({True: "✓ Correct", False: "✗ Missed"})
        
        # Select columns to display
        display_cols = ["x", "y", "shot_angle_deg", "situation", "bodyPart", 
                      "actual_goal", "predicted_prob", "predicted_goal", "result"]
        
        st.dataframe(val_results[display_cols], use_container_width=True)
        
        # Show summary of correct/missed
        correct_count = val_results["correct"].sum()
        total_count = len(val_results)
        st.info(f"Összesen: {correct_count}/{total_count} helyes predikció ({val_accuracy:.1%})")
        
        # Confusion matrix
        st.markdown("**Confusion Matrix:**")
        cm = confusion_matrix(y_val, val_predictions)
        
        fig, ax = plt.subplots(figsize=(4, 3))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                   xticklabels=['No Goal', 'Goal'],
                   yticklabels=['No Goal', 'Goal'])
        ax.set_xlabel('Predicted')
        ax.set_ylabel('Actual')
        ax.set_title('Confusion Matrix')
        plt.tight_layout()
        st.pyplot(fig)
        
        # Classification metrics
        st.markdown("**Osztályozási metrikák:**")
        precision = precision_score(y_val, val_predictions)
        recall = recall_score(y_val, val_predictions)
        f1 = f1_score(y_val, val_predictions)
        
        col5, col6, col7 = st.columns(3)
        col5.metric("Precision", f"{precision:.3f}", help="True Positive / (True Positive + False Positive)")
        col6.metric("Recall", f"{recall:.3f}", help="True Positive / (True Positive + False Negative)")
        col7.metric("F1 Score", f"{f1:.3f}", help="Harmonic mean of precision and recall")
        
        # Detailed classification report
        st.markdown("**Részletes osztályozási jelentés:**")
        report = classification_report(y_val, val_predictions, target_names=['No Goal', 'Goal'], output_dict=True)
        report_df = pd.DataFrame(report).transpose()
        st.dataframe(report_df, use_container_width=True)

    # Feature distributions
    st.subheader("Jellemzők eloszlása gól és gól nélküli lövések szerint")
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    axes = axes.flatten()

    features = ["x", "y", "shot_angle_deg"]
    for idx, feat in enumerate(features):
        sns.histplot(data=shot_data_df, x=feat, hue="goal", kde=True, ax=axes[idx])
        axes[idx].set_title(f"{feat} eloszlása")

    # Remove empty subplot
    fig.delaxes(axes[3])
    plt.tight_layout()
    st.pyplot(fig)

    # Store model in session state
    st.session_state["xg_model"] = model
    st.session_state["xg_le_situation"] = le_situation
    st.session_state["xg_le_body"] = le_body
    st.session_state["xg_data"] = shot_data_df

