#!/usr/bin/env python3
"""Gera assets/langbar.svg a partir dos bytes por linguagem dos repositórios públicos."""
from __future__ import annotations

import argparse
import collections
import json
import os
import pathlib
import sys
import urllib.request
from xml.sax.saxutils import escape

USER = "lfazzion"
API = "https://api.github.com"

PALETTE = {
    "Ruby": "#CC342D",        # vermelho da marca; o #701516 do GitHub some no escuro
    "Python": "#3572A5",
    "TypeScript": "#3178c6",
    "JavaScript": "#f1e05a",
    "C++": "#f34b7d",
}
OTHER_COLOR = "#8b949e"
OTHER_LABEL = "Outras"
TOP_N = 5

NAME_COLOR = "#6e7681"    # cinza neutro: legível no tema claro e no escuro
PCT_COLOR = "#8b949e"
WIDTH = 850
BAR_H = 12
GAP = 3            # vão transparente entre fatias; herda o fundo do perfil
HEIGHT = 44
LEGEND_Y = 34
FONT = '-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif'


def top_slices(totals: dict[str, int], top_n: int = TOP_N) -> list[tuple[str, float, str]]:
    """Top N linguagens por bytes, mais uma fatia agregada com o resto."""
    total = sum(totals.values())
    if total <= 0:
        raise ValueError("nenhum byte de linguagem encontrado")

    ordenado = sorted(totals.items(), key=lambda item: (-item[1], item[0]))
    fatias = [
        (nome, bytes_ / total * 100, PALETTE.get(nome, OTHER_COLOR))
        for nome, bytes_ in ordenado[:top_n]
    ]
    resto = sum(bytes_ for _, bytes_ in ordenado[top_n:])
    if resto:
        fatias.append((OTHER_LABEL, resto / total * 100, OTHER_COLOR))
    return fatias


def format_pct(pct: float) -> str:
    return f"{pct:.1f}".replace(".", ",") + "%"


def render_svg(slices: list[tuple[str, float, str]]) -> str:
    segmentos = []
    x = 0.0
    ultimo = len(slices) - 1
    for i, (_, pct, cor) in enumerate(slices):
        largura = WIDTH * pct / 100
        # o vão sai da própria fatia, menos na última: a barra termina rente à borda
        desenhada = largura if i == ultimo else largura - GAP
        segmentos.append(
            f'<rect x="{x:.2f}" y="0" width="{desenhada:.2f}" height="{BAR_H}" fill="{cor}"/>'
        )
        x += largura

    legenda = []
    slot = WIDTH / len(slices)
    for i, (nome, pct, cor) in enumerate(slices):
        lx = i * slot
        legenda.append(
            f'<circle cx="{lx + 4:.2f}" cy="{LEGEND_Y - 4}" r="4" fill="{cor}"/>'
            f'<text x="{lx + 14:.2f}" y="{LEGEND_Y}" fill="{NAME_COLOR}">{escape(nome)}'
            f'<tspan fill="{PCT_COLOR}"> {format_pct(pct)}</tspan></text>'
        )

    resumo = ", ".join(f"{escape(nome)} {format_pct(pct)}" for nome, pct, _ in slices)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" role="img" font-family=\'{FONT}\' font-size="12">\n'
        f"  <title>{resumo}</title>\n"
        f'  <clipPath id="langbar-clip"><rect width="{WIDTH}" height="{BAR_H}" rx="6"/></clipPath>\n'
        f'  <g clip-path="url(#langbar-clip)">\n    ' + "\n    ".join(segmentos) + "\n  </g>\n"
        "  " + "\n  ".join(legenda) + "\n</svg>\n"
    )


def api_get(url: str, token: str | None = None):
    requisicao = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "gen-langbar",
    })
    if token:
        requisicao.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(requisicao, timeout=30) as resposta:
        return json.load(resposta)


def fetch_language_bytes(user: str = USER, token: str | None = None) -> dict[str, int]:
    """Soma os bytes por linguagem dos repositórios próprios não-fork."""
    repos = []
    pagina = 1
    while True:
        lote = api_get(
            f"{API}/users/{user}/repos?per_page=100&type=owner&page={pagina}", token
        )
        if not lote:
            break
        repos.extend(repo["name"] for repo in lote if not repo["fork"])
        pagina += 1

    totais = collections.Counter()
    for repo in repos:
        totais.update(api_get(f"{API}/repos/{user}/{repo}/languages", token))
    return dict(totais)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gera a barra de linguagens do perfil.")
    parser.add_argument("--out", default="assets/langbar.svg")
    parser.add_argument("--user", default=USER)
    args = parser.parse_args(argv)

    token = os.environ.get("GITHUB_TOKEN")
    fatias = top_slices(fetch_language_bytes(args.user, token))
    svg = render_svg(fatias)

    destino = pathlib.Path(args.out)
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.exists() and destino.read_text(encoding="utf-8") == svg:
        print(f"{destino}: sem mudança")
        return 0
    destino.write_text(svg, encoding="utf-8")
    print(f"{destino}: atualizado — " + ", ".join(f"{n} {format_pct(p)}" for n, p, _ in fatias))
    return 0


if __name__ == "__main__":
    sys.exit(main())
