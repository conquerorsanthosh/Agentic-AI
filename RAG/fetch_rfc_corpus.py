"""
Download a curated RFC corpus for a RAG project.

Usage:
    pip install requests
    python fetch_rfc_corpus.py            # text + metadata for the curated set
    python fetch_rfc_corpus.py --xml      # also fetch RFCXML v3 (RFC 8650+ only)

Output layout:
    corpus/txt/rfc9293.txt
    corpus/xml/rfc9293.xml      (when --xml and available)
    corpus/meta/rfc9293.json    (title, status, obsoletes/obsoleted_by, etc.)
    corpus/manifest.json        (topic + role for every RFC)

For the full series instead, use rsync:
    rsync -avz --delete rsync.rfc-editor.org::rfcs-text-only my-rfc-mirror
"""

import argparse
import json
import time
from pathlib import Path

import requests

BASE = "https://www.rfc-editor.org/rfc"

# role: "current" = in-force spec, "legacy" = obsoleted predecessor kept on
# purpose so you can test version-aware retrieval (metadata filters, "what
# changed between X and Y" questions).
CORPUS = {
    "transport": [
        (9293, "current", "TCP"),
        (793, "legacy", "Original TCP (obsoleted by 9293)"),
        (768, "current", "UDP"),
        (5681, "current", "TCP congestion control"),
        (9438, "current", "CUBIC congestion control"),
        (6298, "current", "TCP retransmission timer"),
        (7323, "current", "TCP extensions: window scale, timestamps"),
        (2018, "current", "TCP selective acknowledgment (SACK)"),
        (3168, "current", "Explicit Congestion Notification (ECN)"),
    ],
    "ip_layer": [
        (791, "current", "IPv4"),
        (792, "current", "ICMP"),
        (8200, "current", "IPv6"),
        (4443, "current", "ICMPv6"),
        (1191, "current", "Path MTU discovery (IPv4)"),
        (8201, "current", "Path MTU discovery (IPv6)"),
    ],
    "http": [
        (9110, "current", "HTTP semantics"),
        (9111, "current", "HTTP caching"),
        (9112, "current", "HTTP/1.1"),
        (9113, "current", "HTTP/2"),
        (9114, "current", "HTTP/3"),
        (7230, "legacy", "HTTP/1.1 message syntax (obsoleted)"),
        (7231, "legacy", "HTTP/1.1 semantics (obsoleted)"),
        (6455, "current", "WebSocket"),
        (3986, "current", "URI syntax"),
    ],
    "quic": [
        (9000, "current", "QUIC transport"),
        (9001, "current", "Using TLS to secure QUIC"),
        (9002, "current", "QUIC loss detection and congestion control"),
    ],
    "security": [
        (8446, "current", "TLS 1.3"),
        (5246, "legacy", "TLS 1.2"),
        (6749, "current", "OAuth 2.0"),
        (7519, "current", "JSON Web Token (JWT)"),
        (7636, "current", "PKCE for OAuth"),
    ],
    "naming_and_infra": [
        (1034, "current", "DNS concepts"),
        (1035, "current", "DNS implementation"),
        (2131, "current", "DHCP"),
        (5905, "current", "NTPv4"),
        (8259, "current", "JSON"),
    ],
}


def fetch(url: str, dest: Path) -> bool:
    if dest.exists():
        return True
    r = requests.get(url, timeout=30)
    if r.status_code != 200:
        return False
    dest.write_bytes(r.content)
    return True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--xml", action="store_true", help="also fetch RFCXML v3")
    ap.add_argument("--out", default="corpus")
    args = ap.parse_args()

    out = Path(args.out)
    for sub in ("txt", "xml", "meta"):
        (out / sub).mkdir(parents=True, exist_ok=True)

    manifest = []
    for topic, items in CORPUS.items():
        for num, role, label in items:
            name = f"rfc{num}"
            ok_txt = fetch(f"{BASE}/{name}.txt", out / "txt" / f"{name}.txt")
            ok_meta = fetch(f"{BASE}/{name}.json", out / "meta" / f"{name}.json")
            ok_xml = False
            if args.xml and num >= 8650:  # v3 XML exists from RFC 8650 onward
                ok_xml = fetch(f"{BASE}/{name}.xml", out / "xml" / f"{name}.xml")
            print(f"{name:<9} txt={ok_txt} meta={ok_meta} xml={ok_xml}  {label}")
            manifest.append(
                {"rfc": num, "topic": topic, "role": role, "label": label}
            )
            time.sleep(0.5)  # be polite to rfc-editor.org

    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"\n{len(manifest)} RFCs -> {out.resolve()}")


if __name__ == "__main__":
    main()
