import pathlib

import yaml

WORKFLOW = pathlib.Path(__file__).resolve().parents[1] / ".github" / "workflows" / "langbar.yml"


def carregar():
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def gatilhos(wf):
    # PyYAML interpreta a chave `on:` como o booleano True (YAML 1.1)
    return wf["on"] if "on" in wf else wf[True]


def test_roda_semanalmente_e_sob_demanda():
    gat = gatilhos(carregar())
    assert "workflow_dispatch" in gat
    assert gat["schedule"][0]["cron"]


def test_tem_permissao_de_escrita():
    assert carregar()["permissions"]["contents"] == "write"


def test_usa_python_312():
    passos = carregar()["jobs"]["langbar"]["steps"]
    setup = [p for p in passos if "setup-python" in p.get("uses", "")]
    assert setup[0]["with"]["python-version"] == "3.12"


def test_chama_o_script_com_o_destino_certo():
    passos = carregar()["jobs"]["langbar"]["steps"]
    comandos = " ".join(p.get("run", "") for p in passos)
    assert "scripts/gen-langbar.py --out assets/langbar.svg" in comandos


def test_so_commita_quando_ha_mudanca():
    passos = carregar()["jobs"]["langbar"]["steps"]
    comandos = " ".join(p.get("run", "") for p in passos)
    assert "git diff --quiet" in comandos
    assert "git push" in comandos


def test_nao_exige_segredo_adicional():
    bruto = WORKFLOW.read_text(encoding="utf-8")
    assert "secrets.GITHUB_TOKEN" in bruto
    assert bruto.count("secrets.") == 1
