import pandas as pd
import numpy as np
from typing import Any, Dict, List, Tuple
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import train_test_split

# Data Preprocessing Functions
def drop_columns(data: pd.DataFrame, columns_to_drop: List[str]) -> pd.DataFrame:
    return data.drop(columns=columns_to_drop)

def handle_missing_values(data: pd.DataFrame, numeric_strategy: str = "mean", categorical_strategy: str = "most_frequent") -> pd.DataFrame:
    numeric_cols = data.select_dtypes(include=["number"]).columns
    categorical_cols = data.select_dtypes(exclude=["number"]).columns

    if not numeric_cols.empty:
        numeric_imputer = SimpleImputer(strategy=numeric_strategy)
        data[numeric_cols] = numeric_imputer.fit_transform(data[numeric_cols])

    if not categorical_cols.empty:
        categorical_imputer = SimpleImputer(strategy=categorical_strategy)
        data[categorical_cols] = categorical_imputer.fit_transform(data[categorical_cols])

    return data

def encode_categorical_features(data: pd.DataFrame, categorical_columns: List[str]) -> pd.DataFrame:
    encoder = OneHotEncoder(sparse=False, drop="first")
    encoded_data = encoder.fit_transform(data[categorical_columns])
    encoded_df = pd.DataFrame(encoded_data, columns=encoder.get_feature_names_out(categorical_columns))
    return data.drop(columns=categorical_columns).join(encoded_df)

def combine_columns(data: pd.DataFrame, combined_columns: Dict[str, Any]) -> pd.DataFrame:
    data[combined_columns["new_column_name"]] = data[combined_columns["columns_to_combine"]].sum(axis=1)
    return data.drop(columns=combined_columns["columns_to_combine"])

def handle_outliers(data: pd.DataFrame, columns: List[str], multiplier: float = 1.5) -> pd.DataFrame:
    for column in columns:
        Q1 = data[column].quantile(0.25)
        Q3 = data[column].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - multiplier * IQR
        upper_bound = Q3 + multiplier * IQR
        data[column] = np.clip(data[column], lower_bound, upper_bound)
    return data

def log_transform(data: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    for column in columns:
        data[column] = np.log1p(data[column])
    return data

def split_data(data: pd.DataFrame, parameters: Dict[str, Any]) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    X = data.drop(columns=parameters["target_column"])
    y = data[parameters["target_column"]]
    return train_test_split(X, y, test_size=1 - parameters["train_fraction"], random_state=parameters["random_state"])
