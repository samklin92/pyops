from infra import S3Reporter

reporter = S3Reporter(bucket_name="devops-monitor-109804294707")
reports = reporter.list_reports()

if reports:
    # Sort by last_modified and get the latest
    latest = sorted(reports, key=lambda x: x["last_modified"])[-1]
    content = reporter.download(latest["key"])
    print(content)