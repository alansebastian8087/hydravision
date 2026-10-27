def check_bis_and_wqs(test_result):
    score = 100
    issues = []

    parameter_rules = [
        {
            "name": "pH",
            "value": test_result.ph,
            "safe": 6.5 <= test_result.ph <= 8.5,
            "message": "pH is outside the acceptable range of 6.5 to 8.5",
            "deduction": 10,
        },
        {
            "name": "TDS",
            "value": test_result.tds,
            "safe": test_result.tds <= 500,
            "message": "TDS is above the acceptable limit of 500 mg/L",
            "deduction": 10,
        },
        {
            "name": "Turbidity",
            "value": test_result.turbidity,
            "safe": test_result.turbidity <= 1,
            "message": "Turbidity is above the acceptable limit of 1 NTU",
            "deduction": 10,
        },
        {
            "name": "Hardness",
            "value": test_result.hardness,
            "safe": test_result.hardness <= 200,
            "message": "Hardness is above the acceptable limit of 200 mg/L",
            "deduction": 10,
        },
        {
            "name": "Fluoride",
            "value": test_result.fluoride,
            "safe": test_result.fluoride <= 1.0,
            "message": "Fluoride is above the acceptable limit of 1.0 mg/L",
            "deduction": 10,
        },
        {
            "name": "Iron",
            "value": test_result.iron,
            "safe": test_result.iron <= 0.3,
            "message": "Iron is above the acceptable limit of 0.3 mg/L",
            "deduction": 10,
        },
        {
            "name": "Nitrate",
            "value": test_result.nitrate,
            "safe": test_result.nitrate <= 45,
            "message": "Nitrate is above the acceptable limit of 45 mg/L",
            "deduction": 10,
        },
        {
            "name": "Chloride",
            "value": test_result.chloride,
            "safe": test_result.chloride <= 250,
            "message": "Chloride is above the acceptable limit of 250 mg/L",
            "deduction": 10,
        },
        {
            "name": "Sulphate",
            "value": test_result.sulphate,
            "safe": test_result.sulphate <= 200,
            "message": "Sulphate is above the acceptable limit of 200 mg/L",
            "deduction": 10,
        },
        {
            "name": "Alkalinity",
            "value": test_result.alkalinity,
            "safe": test_result.alkalinity <= 200,
            "message": "Alkalinity is above the acceptable limit of 200 mg/L",
            "deduction": 10,
        },
    ]

    for rule in parameter_rules:
        if not rule["safe"]:
            score -= rule["deduction"]
            issues.append(rule["message"])

    score = max(score, 0)

    if not issues:
        bis_status = "Safe"
        recommendation = (
            "All tested parameters are within the configured acceptable limits. "
            "Water is suitable for normal use based on this laboratory test."
        )
    else:
        bis_status = "Unsafe"
        recommendation = (
            "Water needs treatment before use. "
            "Parameters needing attention: " + "; ".join(issues) + "."
        )

    return score, bis_status, recommendation