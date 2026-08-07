import pathlib

README = pathlib.Path(__file__).resolve().parents[1] / "README.md"
GRAPH = "https://github-readme-activity-graph.vercel.app/graph"
PROJETOS = ["ClaytOn-Rails", "news2kindle", "EstatisticoMais"]
SITES = ["https://tegece.com.br"]


def texto():
    return README.read_text(encoding="utf-8")


def test_tagline_aprovada_esta_presente():
    assert "Construo coisas porque quero que elas existam." in texto()


def test_grafico_tem_os_dois_temas_no_picture():
    conteudo = texto()
    assert '<source media="(prefers-color-scheme: dark)"' in conteudo
    assert '<source media="(prefers-color-scheme: light)"' in conteudo
    assert f"{GRAPH}?username=lfazzion&theme=tokyo-night" in conteudo
    assert f"{GRAPH}?username=lfazzion&theme=github-light" in conteudo


def test_titulo_do_grafico_em_portugues_percent_encoded():
    assert "custom_title=Atividade%20dos%20%C3%BAltimos%2031%20dias" in texto()


def test_img_de_fallback_tem_alt():
    assert 'alt="Atividade dos últimos 31 dias"' in texto()


def test_barra_de_linguagens_referenciada():
    assert "assets/langbar.svg" in texto()


def test_projetos_com_link():
    conteudo = texto()
    for nome in PROJETOS:
        assert f"[{nome}](https://github.com/lfazzion/{nome})" in conteudo


def test_clayton_em_destaque_abre_a_lista():
    linhas = [l for l in texto().splitlines() if l.startswith("- **[")]
    assert linhas[0].startswith("- **[ClaytOn-Rails]")


def test_sites_listados():
    conteudo = texto()
    assert "## Sites" in conteudo
    for url in SITES:
        assert url in conteudo


def test_site_em_construcao_nao_aparece():
    # só o tegece entra enquanto o outro estiver em obras
    assert texto().count("](https://") - texto().count("](https://github.com/") == 1


def test_rodape_tem_email_e_repositorios():
    conteudo = texto()
    assert "mailto:lowellfazzion@gmail.com" in conteudo
    assert "https://github.com/lfazzion?tab=repositories" in conteudo


def test_sem_elementos_descartados_na_spec():
    conteudo = texto().lower()
    for banido in ["streak", "trophy", "shields.io", "visitor-badge",
                   "snake", "capsule-render", "<div align"]:
        assert banido not in conteudo


def test_cabe_em_uma_tela():
    linhas = texto().splitlines()
    assert len(linhas) <= 40, f"README com {len(linhas)} linhas; a spec exige uma tela"
