import pytest


def test_ordem_e_agregado_batem_com_a_spec(gen, totais_reais):
    fatias = gen.top_slices(totais_reais)
    assert [nome for nome, _, _ in fatias] == [
        "Ruby", "Python", "TypeScript", "JavaScript", "C++", "Outras"
    ]


def test_percentuais_batem_com_a_spec(gen, totais_reais):
    fatias = gen.top_slices(totais_reais)
    assert [round(pct, 1) for _, pct, _ in fatias] == [23.1, 20.1, 17.8, 13.1, 12.3, 13.6]


def test_percentuais_somam_cem(gen, totais_reais):
    fatias = gen.top_slices(totais_reais)
    assert sum(pct for _, pct, _ in fatias) == pytest.approx(100.0)


def test_outras_vem_dos_bytes_nao_da_soma_de_arredondados(gen, totais_reais):
    # somar os percentuais já arredondados daria 13,5; a partir dos bytes dá 13,6
    _, pct, _ = gen.top_slices(totais_reais)[-1]
    assert round(pct, 1) == 13.6


def test_ruby_usa_o_vermelho_da_marca(gen, totais_reais):
    cores = {nome: cor for nome, _, cor in gen.top_slices(totais_reais)}
    assert cores["Ruby"] == "#CC342D"
    assert cores["Outras"] == "#8b949e"


def test_sem_sobra_nao_gera_fatia_outras(gen):
    fatias = gen.top_slices({"Python": 100, "Ruby": 100})
    assert [nome for nome, _, _ in fatias] == ["Python", "Ruby"]


def test_empate_de_bytes_desempata_alfabeticamente(gen):
    fatias = gen.top_slices({"Zig": 10, "Ada": 10}, top_n=2)
    assert [nome for nome, _, _ in fatias] == ["Ada", "Zig"]


def test_total_zero_levanta_erro(gen):
    with pytest.raises(ValueError):
        gen.top_slices({})


def segmentos(gen, svg):
    """(x, largura) de cada fatia. O <rect> do clipPath não tem x/y; só os segmentos têm."""
    import re
    achados = re.findall(r'<rect x="([\d.]+)" y="0" width="([\d.]+)" height="12"', svg)
    return [(float(x), float(w)) for x, w in achados]


def test_segmentos_cobrem_a_largura_menos_os_vaos(gen, totais_reais):
    segs = segmentos(gen, gen.render_svg(gen.top_slices(totais_reais)))
    assert len(segs) == 6
    assert sum(w for _, w in segs) == pytest.approx(gen.WIDTH - gen.GAP * 5, abs=0.05)


def test_ultimo_segmento_termina_na_borda(gen, totais_reais):
    x, w = segmentos(gen, gen.render_svg(gen.top_slices(totais_reais)))[-1]
    assert x + w == pytest.approx(gen.WIDTH, abs=0.05)


def test_vao_entre_fatias_vizinhas(gen, totais_reais):
    segs = segmentos(gen, gen.render_svg(gen.top_slices(totais_reais)))
    for (x, w), (proximo_x, _) in zip(segs, segs[1:]):
        assert proximo_x - (x + w) == pytest.approx(gen.GAP, abs=0.01)


def test_vao_e_transparente_nao_pintado(gen, totais_reais):
    # o vão herda o fundo do perfil; se fosse pintado, precisaria escolher tema
    svg = gen.render_svg(gen.top_slices(totais_reais))
    assert "stroke" not in svg


def test_percentual_usa_virgula_decimal(gen, totais_reais):
    svg = gen.render_svg(gen.top_slices(totais_reais))
    assert "23,1%" in svg
    assert "23.1%" not in svg


def test_sem_fundo_proprio_e_sem_media_query(gen, totais_reais):
    svg = gen.render_svg(gen.top_slices(totais_reais))
    assert "prefers-color-scheme" not in svg
    assert "<style" not in svg
    assert '<rect x="0" y="0" width="850" height="44"' not in svg


def test_cores_neutras_na_legenda(gen, totais_reais):
    svg = gen.render_svg(gen.top_slices(totais_reais))
    assert gen.NAME_COLOR in svg
    assert gen.PCT_COLOR in svg


def test_saida_e_deterministica(gen, totais_reais):
    fatias = gen.top_slices(totais_reais)
    assert gen.render_svg(fatias) == gen.render_svg(fatias)


def test_barra_tem_pontas_arredondadas_por_clip(gen, totais_reais):
    svg = gen.render_svg(gen.top_slices(totais_reais))
    assert '<clipPath id="langbar-clip">' in svg
    assert 'clip-path="url(#langbar-clip)"' in svg


def test_svg_tem_titulo_acessivel(gen, totais_reais):
    svg = gen.render_svg(gen.top_slices(totais_reais))
    assert "<title>" in svg
    assert "Ruby 23,1%" in svg


def test_fetch_soma_bytes_de_repos_nao_fork(gen, monkeypatch):
    respostas = {
        "https://api.github.com/users/lfazzion/repos?per_page=100&type=owner&page=1": [
            {"name": "a", "fork": False},
            {"name": "b", "fork": True},
            {"name": "c", "fork": False},
        ],
        "https://api.github.com/users/lfazzion/repos?per_page=100&type=owner&page=2": [],
        "https://api.github.com/repos/lfazzion/a/languages": {"Ruby": 10, "Python": 5},
        "https://api.github.com/repos/lfazzion/b/languages": {"Ruby": 999},
        "https://api.github.com/repos/lfazzion/c/languages": {"Ruby": 1},
    }
    monkeypatch.setattr(gen, "api_get", lambda url, token=None: respostas[url])
    assert gen.fetch_language_bytes("lfazzion") == {"Ruby": 11, "Python": 5}


def test_main_escreve_o_arquivo(gen, monkeypatch, tmp_path, totais_reais):
    monkeypatch.setattr(gen, "fetch_language_bytes", lambda user, token=None: totais_reais)
    destino = tmp_path / "langbar.svg"
    assert gen.main(["--out", str(destino)]) == 0
    conteudo = destino.read_text(encoding="utf-8")
    assert conteudo.startswith("<svg")
    assert "23,1%" in conteudo


def test_main_nao_reescreve_quando_nada_muda(gen, monkeypatch, tmp_path, totais_reais):
    monkeypatch.setattr(gen, "fetch_language_bytes", lambda user, token=None: totais_reais)
    destino = tmp_path / "langbar.svg"
    gen.main(["--out", str(destino)])
    primeiro = destino.read_text(encoding="utf-8")
    gen.main(["--out", str(destino)])
    assert destino.read_text(encoding="utf-8") == primeiro
