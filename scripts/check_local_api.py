#!/usr/bin/env python3
"""Check the local server's authentication, model listing and streamed generation."""
import argparse
import json
from pathlib import Path
import time
import urllib.error
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=10000)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    key = (project / "data/local-api-key").read_text().strip()
    root = f"http://127.0.0.1:{args.port}"
    report = {"time": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "port": args.port}
    try:
        urllib.request.urlopen(root + "/v1/models", timeout=15).close()
        report["unauthenticated_status"] = 200
    except urllib.error.HTTPError as error:
        report["unauthenticated_status"] = error.code
    headers = {"Authorization": "Bearer " + key, "Content-Type": "application/json"}
    request = urllib.request.Request(root + "/v1/models", headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        models = json.load(response)
    model = models["data"][0]["id"]
    report["model"] = model
    body = {"model": model, "messages": [{"role": "user", "content":
            "What is 2 + 2? Answer in one short sentence."}], "max_tokens": 256,
            "temperature": 0, "stream": True,
            "chat_template_kwargs": {"enable_thinking": False}}
    request = urllib.request.Request(root + "/v1/chat/completions", headers=headers,
                                     data=json.dumps(body).encode())
    start = time.monotonic()
    with urllib.request.urlopen(request, timeout=600) as response:
        stream = response.read().decode()
    report["elapsed_seconds"] = round(time.monotonic() - start, 3)
    report["stream_done"] = "data: [DONE]" in stream
    text = []
    for line in stream.splitlines():
        if line.startswith("data: ") and line != "data: [DONE]":
            event = json.loads(line[6:])
            for choice in event.get("choices", []):
                text.append(choice.get("delta", {}).get("content") or "")
    report["text"] = "".join(text)
    report["stream"] = stream
    report["passed"] = (report["unauthenticated_status"] in (401, 403)
                        and report["stream_done"] and bool(report["text"].strip()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != "stream"}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
