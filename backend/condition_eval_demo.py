from main import _evaluate_condition

sample_row = {
    "CLOSE": "25010",
    "VOLUME": "1,200,000",
    "SYMBOL": "NIFTY",
}

sample_spec = {
    "field": "CLOSE",
    "operator": ">",
    "value": "25000",
    "value_type": "number",
}

print("Condition met:", _evaluate_condition(sample_row, sample_spec))
