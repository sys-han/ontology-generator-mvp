from __future__ import annotations

from io import BytesIO
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd


MAX_SAMPLE_ROWS = 5
MAX_PROFILE_ROWS = 50_000


def _clean_scalar(value: Any) -> Any:
    if value is None:
        return None

    if hasattr(value, "item"):
        try:
            value = value.item()
        except Exception:
            pass

    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    return value


def _infer_type(series: pd.Series) -> str:
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_integer_dtype(series):
        return "integer"
    if pd.api.types.is_float_dtype(series):
        return "float"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    return "string"


def _read_dataframe(filename: str, raw: bytes) -> pd.DataFrame:
    suffix = Path(filename).suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(BytesIO(raw), nrows=MAX_PROFILE_ROWS)

    if suffix == ".json":
        text = raw.decode("utf-8")
        data = json.loads(text)

        if isinstance(data, list):
            return pd.DataFrame(data)

        if isinstance(data, dict):
            # Try common shapes: {"records": [...]}, or a single object.
            for key in ("records", "data", "items", "rows"):
                if isinstance(data.get(key), list):
                    return pd.DataFrame(data[key])
            return pd.DataFrame([data])

        raise ValueError("JSON must contain an object or array of objects.")

    raise ValueError(f"Unsupported file type for {filename}. Use CSV or JSON.")


def profile_file(filename: str, raw: bytes) -> tuple[dict, pd.DataFrame]:
    df = _read_dataframe(filename, raw)

    columns: dict[str, dict] = {}

    for column in df.columns:
        series = df[column]
        non_null = series.dropna()
        examples = [_clean_scalar(v) for v in non_null.head(MAX_SAMPLE_ROWS).tolist()]
        unique_count = int(non_null.nunique(dropna=True))
        denom = max(int(non_null.shape[0]), 1)

        info = {
            "type": _infer_type(series),
            "nullable": bool(series.isna().any()),
            "unique_ratio": round(unique_count / denom, 4),
            "examples": examples,
        }

        if pd.api.types.is_numeric_dtype(series) and not non_null.empty:
            info["min"] = _clean_scalar(non_null.min())
            info["max"] = _clean_scalar(non_null.max())

        columns[str(column)] = info

    profile = {
        "source": filename,
        "row_count_profiled": int(len(df)),
        "columns": columns,
    }

    return profile, df
