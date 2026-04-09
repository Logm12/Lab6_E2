from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.vectorstore.ingest import ingest_vinfast_csvs_to_qdrant


def main() -> None:
    youtube_collection, facebook_collection = ingest_vinfast_csvs_to_qdrant()
    print(str(youtube_collection))
    print(str(facebook_collection))


if __name__ == "__main__":
    main()
