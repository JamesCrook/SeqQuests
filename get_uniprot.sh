#!/usr/bin/env bash
#
# get_uniprot.sh - Download UniProt Swiss-Prot protein database
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_URL="https://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/complete"

# --- Subroutines ---

die() { echo "❌ Error: $1" >&2; exit 1; }

load_env() {
    [[ -f "$SCRIPT_DIR/.env" ]] && source "$SCRIPT_DIR/.env"
    [[ -z "${SEQQUESTS_DATA_DIR:-}" ]] && die "SEQQUESTS_DATA_DIR is not set in .env"
    DATA_DIR="${SEQQUESTS_DATA_DIR/#\~/$HOME}"
    mkdir -p "$DATA_DIR"
    echo "📁 Data directory: $DATA_DIR"
}

find_downloader() {
    if command -v curl &> /dev/null; then
        DOWNLOADER="curl"
    elif command -v wget &> /dev/null; then
        DOWNLOADER="wget"
    else
        die "Neither curl nor wget found"
    fi
}

download() {
    local url="$1" output="$2"
    echo "⬇️  Downloading $(basename "$output")..."
    if [[ "$DOWNLOADER" == "curl" ]]; then
        curl -L --progress-bar -o "$output" "$url"
    else
        wget --show-progress -O "$output" "$url"
    fi
    [[ -f "$output" ]] || die "Download failed: $output"
}

fetch_and_extract() {
    local name="$1"
    local output="$DATA_DIR/$name"
    local output_gz="$output.gz"

    if [[ -f "$output" ]]; then
        echo "✅ $name already exists ($(du -h "$output" | cut -f1))"
        return 0
    fi

    download "$BASE_URL/$name.gz" "$output_gz"
    echo "📦 Extracting $name..."
    gunzip -f "$output_gz"
    echo "   $(du -h "$output" | cut -f1)"
}

# --- Main ---

load_env
find_downloader
echo ""

fetch_and_extract "uniprot_sprot.fasta"
fetch_and_extract "uniprot_sprot.dat"

echo ""
echo "✅ Done!"