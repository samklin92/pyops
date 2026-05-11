def check_cpu(usage, threshold=75):
    if usage > threshold:
        return f"ALERT: CPU at {usage}% — exceeds {threshold}%"
    return f"OK: CPU at {usage}%"

print(check_cpu(85))
print(check_cpu(60))
print(check_cpu(85, threshold=90))