# SpaceGuard-AI — Machine Learning

## Overview

The ML part of **SpaceGuard-AI** is used to predict the collision risk between two space objects based on their orbital and close-approach information.

## Engine integration

ML input is now produced by the project itself, rather than entered manually:

```text
orbit_engine (TLE -> propagated TEME states)
    -> collision_engine (closest-approach event)
    -> ml.features.build_features(...)
    -> ml.predict.predict_features(...)
```

The end-to-end entry point is `ml.pipeline.analyze_tle_pair`. Its returned
dictionary contains the collision result, the exact ML feature vector, and the
ML prediction. The trained dataset must use these same columns:

* `miss_distance_km`
* `relative_velocity_km_s`
* `time_to_tca_hours`
* `object_a_altitude_km`
* `object_b_altitude_km`
* `altitude_difference_km`

`ml/train_model.py` expects those columns plus the binary `risk` label. This
keeps training and production inference on the same engine-derived schema.

The model scores engine-derived features and returns a risk probability, a
score out of 100, and a **LOW**, **MEDIUM**, or **HIGH** category.

## How It Works

The overall process is:

```text
Input Data
    ↓
Data Preprocessing
    ↓
Feature Selection
    ↓
Train-Test Split
    ↓
Random Forest Model
    ↓
Model Evaluation
    ↓
Risk Prediction
```

## Deprecated feature schema

The following list belongs to the old synthetic prototype and is retained
only for historical context. Do not use it for training or inference; use the
six engine-derived fields in **Engine integration** instead.

* `minimum_distance` — minimum distance between the two objects
* `relative_velocity` — relative velocity between the objects
* `time_to_closest_approach` — time until the objects reach their closest point
* `altitude` — orbital altitude
* `inclination_difference` — difference in orbital inclination
* `eccentricity` — orbital eccentricity

The target variable is `risk`, where:

```text
0 → SAFE
1 → RISK
```

## Model Used

For the classification task, I used a **Random Forest Classifier**.

Random Forest was chosen because it works well with multiple numerical features and can capture non-linear relationships between the input parameters. It also gives good performance without requiring the dataset to be extremely large.

The trained model is saved as:

```text
ml/models/risk_model.pkl
```

## Dataset

Training data must contain one row per historical or simulated conjunction,
using the current six feature columns plus `risk`. Generate those rows from
the same orbit/collision pipeline used at inference time. The repository does
not currently include a compatible training CSV or trained model artifact.

## Model Performance

No performance figure is claimed until a compatible dataset is supplied and
the model is trained. Evaluate recall carefully before using it to screen
potentially risky conjunctions.

## Project Structure

```text
ml/
├── data/
│   └── training_data.csv
├── models/
│   └── risk_model.pkl
├── train_model.py
├── predict.py
├── evaluate_model.py
├── requirements.txt
└── README.md
```

### `train_model.py`

Used to train the Random Forest model using the training dataset. The trained model is then saved so it can be used later without retraining every time.

### `predict.py`

Loads the saved model and uses it to predict the risk for new input data.

The output includes the risk probability, risk score, and risk level.

### `features.py` and `pipeline.py`

`features.py` converts orbit and collision outputs into the feature schema.
`pipeline.py` propagates both objects concurrently, performs collision
detection, and returns orbit, collision, feature, and prediction data together.

### `training_data.csv`

The dataset used for training and testing the model.

### `risk_model.pkl`

The saved trained Random Forest model.

## Running the ML Model

From the project root, install the required libraries:

```bash
python -m pip install -r requirements.txt
python -m pip install -r ml/requirements.txt
```

To train the model:

```bash
python -m ml.train_model
```

Use `ml.pipeline.analyze_tle_pair(...)` to run propagation, collision
detection, feature extraction, and ML scoring together. A trained model must
exist before the scoring step can run.

## Risk Score

The model produces a probability for the `RISK` class. This probability is converted into a score between 0 and 100.

```text
Risk Score = Risk Probability × 100
```

The score is then grouped into three levels:

| Score  | Risk Level |
| ------ | ---------- |
| 0–33   | LOW        |
| 34–66  | MEDIUM     |
| 67–100 | HIGH       |

This makes the model's output easier to understand instead of showing only a probability value.

## Technologies Used

* Python
* Pandas
* NumPy
* Scikit-learn
* Random Forest
* Pickle

## Future Improvements

There are several things that can be added to improve the ML part of the project:

* Use real satellite and orbital datasets instead of only synthetic data
* Increase the size of the training dataset
* Try other ML algorithms and compare their performance
* Tune the Random Forest hyperparameters
* Add cross-validation
* Improve feature engineering
* Use real-time orbital data for predictions
* Add explainability so users can understand why a particular encounter was classified as risky

## Note

This ML model is currently a prototype developed for the **SpaceGuard-AI** project. The predictions are meant for project and demonstration purposes and should not be treated as actual collision-avoidance decisions for spacecraft.
