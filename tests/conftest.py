import importlib.util
import pathlib

import pytest

CAMINHO = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "gen-langbar.py"


@pytest.fixture(scope="session")
def gen():
    """Carrega scripts/gen-langbar.py como módulo (o hífen impede import direto)."""
    spec = importlib.util.spec_from_file_location("gen_langbar", CAMINHO)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture
def totais_reais():
    """Bytes por linguagem medidos em 2026-08-06 (total 1.403.935)."""
    return {
        "Ruby": 324359, "Python": 282458, "TypeScript": 250350,
        "JavaScript": 184299, "C++": 172160, "HTML": 96889,
        "CSS": 32657, "Shell": 25816, "PHP": 14225, "Java": 13882,
        "C": 4628, "Dockerfile": 2212,
    }
