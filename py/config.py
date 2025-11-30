"""
Configuration management for SeqQuests project.
"""
from pathlib import Path
import os
from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / '.env')

# Data directory with fallback
DATA_DIR = Path(os.getenv('SEQQUESTS_DATA_DIR', '~/data/seqquests')).expanduser()

# Ensure it exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Specific data paths
FASTA_PATH = DATA_DIR / 'swissprot_trembl.fasta'
NCBI_TAXONOMY_DB = DATA_DIR / 'ncbi_taxonomy.db'
PDB_CACHE_DIR = DATA_DIR / 'pdb_cache'

# Create subdirectories
PDB_CACHE_DIR.mkdir(exist_ok=True)