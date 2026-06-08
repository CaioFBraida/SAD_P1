"""
=============================================================
  ANÁLISE WHAT-IF – SIMULADOR DE LUCRO EM LOJA DE VAREJO
=============================================================

USO:
  python analise_whatif.py                         → modo interativo
  python analise_whatif.py --variacao 15           → +15% em todos os produtos
  python analise_whatif.py --variacao -10          → -10% em todos os produtos
  python analise_whatif.py --produto "Bone" --variacao 20
  python analise_whatif.py --faixa -30 30 5        → simula de -30% a +30% em steps de 5%
  python analise_whatif.py --elasticidade          → ativa ajuste de demanda por elasticidade
  python analise_whatif.py --otimizar              → encontra a variação ótima por produto
  python analise_whatif.py --ajuda                 → mostra esta mensagem
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import sys
import os

CSV_PATH = "produtos.csv"

# ──────────────────────────────────────────────
# CORES E ESTILO
# ──────────────────────────────────────────────
COR_POSITIVO  = "#2ecc71"
COR_NEGATIVO  = "#e74c3c"
COR_NEUTRO    = "#3498db"
COR_DESTAQUE  = "#f39c12"
COR_FUNDO     = "#1a1a2e"
COR_PAINEL    = "#16213e"
COR_TEXTO     = "#eaeaea"

def aplicar_estilo():
    plt.rcParams.update({
        "figure.facecolor":  COR_FUNDO,
        "axes.facecolor":    COR_PAINEL,
        "axes.edgecolor":    "#444",
        "axes.labelcolor":   COR_TEXTO,
        "xtick.color":       COR_TEXTO,
        "ytick.color":       COR_TEXTO,
        "text.color":        COR_TEXTO,
        "grid.color":        "#2a2a4a",
        "grid.linestyle":    "--",
        "grid.alpha":        0.5,
        "font.family":       "monospace",
    })

# ──────────────────────────────────────────────
# LEITURA E CÁLCULO BASE
# ──────────────────────────────────────────────
def carregar_dados():
    if not os.path.exists(CSV_PATH):
        print(f"[ERRO] Arquivo '{CSV_PATH}' não encontrado. Coloque-o na mesma pasta.")
        sys.exit(1)
    df = pd.read_csv(CSV_PATH)
    df["lucro_unitario_base"] = df["preco_atual"] - df["custo_unitario"]
    df["lucro_total_base"]    = df["lucro_unitario_base"] * df["quantidade_vendida"]
    df["margem_base_pct"]     = (df["lucro_unitario_base"] / df["preco_atual"] * 100).round(1)
    return df

def calcular_lucro(df, variacoes_por_produto, usar_elasticidade=False):
    """
    variacoes_por_produto: dict {nome_produto: pct_variacao}
    Retorna o DataFrame com colunas calculadas para o cenário.
    """
    resultado = df.copy()
    resultado["variacao_aplicada"] = 0.0
    resultado["preco_novo"]        = resultado["preco_atual"]
    resultado["qty_nova"]          = resultado["quantidade_vendida"].astype(float)

    for _, row in resultado.iterrows():
        nome = row["produto"]
        v    = variacoes_por_produto.get(nome, 0.0)
        idx  = resultado[resultado["produto"] == nome].index[0]
        fator_preco = 1 + v / 100
        preco_novo  = row["preco_atual"] * fator_preco
        resultado.at[idx, "variacao_aplicada"] = v
        resultado.at[idx, "preco_novo"]        = preco_novo

        if usar_elasticidade and "elasticidade" in df.columns:
            e = row["elasticidade"]  # ex: -1.2
            # qty_nova = qty_base * (1 + e * v/100)
            qty_nova = max(0, row["quantidade_vendida"] * (1 + e * (v / 100)))
            resultado.at[idx, "qty_nova"] = qty_nova

    resultado["lucro_unitario_novo"] = resultado["preco_novo"] - resultado["custo_unitario"]
    resultado["lucro_total_novo"]    = resultado["lucro_unitario_novo"] * resultado["qty_nova"]
    resultado["delta_lucro"]         = resultado["lucro_total_novo"] - resultado["lucro_total_base"]
    resultado["margem_nova_pct"]     = (
        resultado["lucro_unitario_novo"] / resultado["preco_novo"] * 100
    ).round(1)
    return resultado

# ──────────────────────────────────────────────
# SIMULAÇÃO EM FAIXA (tabela de cenários)
# ──────────────────────────────────────────────
def simular_faixa(df, inicio, fim, passo, produto=None, usar_elasticidade=False):
    variacoes = list(range(int(inicio), int(fim) + 1, int(passo)))
    registros = []
    for v in variacoes:
        if produto:
            var_map = {p: (v if p == produto else 0) for p in df["produto"]}
        else:
            var_map = {p: v for p in df["produto"]}
        res = calcular_lucro(df, var_map, usar_elasticidade)
        lucro_total = res["lucro_total_novo"].sum()
        lucro_base  = res["lucro_total_base"].sum()
        registros.append({
            "variacao_pct": v,
            "lucro_total":  lucro_total,
            "delta":        lucro_total - lucro_base,
            "delta_pct":    ((lucro_total - lucro_base) / lucro_base * 100)
        })
    return pd.DataFrame(registros)

# ──────────────────────────────────────────────
# MODO OTIMIZAR: melhor variação por produto
# ──────────────────────────────────────────────
def otimizar(df, usar_elasticidade=True):
    print("\n[OTIMIZADOR] Buscando variação ótima por produto (de -50% a +50%)...")
    resultados = []
    for _, row in df.iterrows():
        nome = row["produto"]
        melhor_lucro = -np.inf
        melhor_v     = 0
        for v in range(-50, 51):
            var_map = {p: (v if p == nome else 0) for p in df["produto"]}
            res     = calcular_lucro(df, var_map, usar_elasticidade)
            lucro_produto = res[res["produto"] == nome]["lucro_total_novo"].values[0]
            if lucro_produto > melhor_lucro:
                melhor_lucro = lucro_produto
                melhor_v     = v
        resultados.append({
            "produto":         nome,
            "variacao_otima":  melhor_v,
            "lucro_otimo":     melhor_lucro,
            "lucro_atual":     row["lucro_total_base"]
        })
    return pd.DataFrame(resultados)

# ──────────────────────────────────────────────
# IMPRESSÃO NO TERMINAL
# ──────────────────────────────────────────────
LINHA = "─" * 65

def cabecalho():
    print("\n" + "═" * 65)
    print("   SIMULADOR DE LUCRO – ANÁLISE WHAT-IF | LOJA DE VAREJO")
    print("═" * 65)

def imprimir_base(df):
    lucro_base = df["lucro_total_base"].sum()
    print(f"\n{'SITUAÇÃO ATUAL':^65}")
    print(LINHA)
    print(f"{'Produto':<22} {'Preço':>8} {'Custo':>8} {'Qtd':>6} {'Margem%':>8} {'Lucro':>12}")
    print(LINHA)
    for _, r in df.iterrows():
        print(f"{r['produto']:<22} {r['preco_atual']:>8.2f} {r['custo_unitario']:>8.2f} "
              f"{r['quantidade_vendida']:>6.0f} {r['margem_base_pct']:>7.1f}% {r['lucro_total_base']:>12.2f}")
    print(LINHA)
    print(f"{'LUCRO BASE TOTAL':>46}  R$ {lucro_base:>12,.2f}")

def imprimir_cenario(res, label="CENÁRIO SIMULADO", usar_elasticidade=False):
    lucro_base  = res["lucro_total_base"].sum()
    lucro_novo  = res["lucro_total_novo"].sum()
    delta       = lucro_novo - lucro_base
    delta_pct   = delta / lucro_base * 100

    print(f"\n{label:^65}")
    print(LINHA)
    header = f"{'Produto':<22} {'Var%':>5} {'Preço Novo':>10} {'Margem%':>8}"
    if usar_elasticidade:
        header += f" {'Qtd Nova':>8}"
    header += f" {'Lucro Novo':>12} {'Δ Lucro':>12}"
    print(header)
    print(LINHA)
    for _, r in res.iterrows():
        sinal  = "+" if r["variacao_aplicada"] >= 0 else ""
        cor_d  = "▲" if r["delta_lucro"] >= 0 else "▼"
        linha  = (f"{r['produto']:<22} {sinal}{r['variacao_aplicada']:>4.1f}% "
                  f"{r['preco_novo']:>10.2f} {r['margem_nova_pct']:>7.1f}%")
        if usar_elasticidade:
            linha += f" {r['qty_nova']:>8.0f}"
        linha += f" {r['lucro_total_novo']:>12.2f} {cor_d}{r['delta_lucro']:>+11.2f}"
        print(linha)
    print(LINHA)
    sinal_tot = "▲" if delta >= 0 else "▼"
    print(f"{'LUCRO NOVO TOTAL':>46}  R$ {lucro_novo:>12,.2f}")
    print(f"{'VARIAÇÃO vs BASE':>46}  {sinal_tot} R$ {delta:>+12,.2f}  ({delta_pct:+.1f}%)")

def imprimir_tabela_faixa(tab):
    print(f"\n{'TABELA DE CENÁRIOS':^65}")
    print(LINHA)
    print(f"{'Variação%':>10} {'Lucro Total':>15} {'Δ vs Base':>14} {'Δ%':>8}  Indicador")
    print(LINHA)
    lucro_max = tab["lucro_total"].max()
    lucro_min = tab["lucro_total"].min()
    for _, r in tab.iterrows():
        bar_len = int((r["lucro_total"] - lucro_min) / max(lucro_max - lucro_min, 1) * 20)
        barra   = "█" * bar_len + "░" * (20 - bar_len)
        sinal   = "★" if r["lucro_total"] == lucro_max else " "
        print(f"{r['variacao_pct']:>+9.0f}% {r['lucro_total']:>15,.2f} "
              f"{r['delta']:>+14,.2f} {r['delta_pct']:>+7.1f}%  {barra} {sinal}")
    print(LINHA)
    melhor = tab.loc[tab["lucro_total"].idxmax()]
    print(f"\n★  MELHOR CENÁRIO: variação de {melhor['variacao_pct']:+.0f}%")
    print(f"   Lucro estimado: R$ {melhor['lucro_total']:,.2f}  "
          f"({melhor['delta_pct']:+.1f}% vs base)")

def imprimir_recomendacao(df, res_cenario, tab_faixa=None, otim=None, usar_elasticidade=False):
    lucro_base = df["lucro_total_base"].sum()
    lucro_novo = res_cenario["lucro_total_novo"].sum()
    delta      = lucro_novo - lucro_base
    delta_pct  = delta / lucro_base * 100

    print("\n" + "═" * 65)
    print("   RECOMENDAÇÕES E ANÁLISE DO CENÁRIO")
    print("═" * 65)

    # 1. Avaliação do cenário atual simulado
    if delta > 0:
        print(f"\n✔  O cenário simulado AUMENTA o lucro em R$ {delta:,.2f} ({delta_pct:+.1f}%).")
        print("   Recomenda-se avaliar a viabilidade competitiva antes de aplicar.")
    elif delta < 0:
        print(f"\n✘  O cenário simulado REDUZ o lucro em R$ {abs(delta):,.2f} ({delta_pct:+.1f}%).")
        print("   Considere ajustes menores ou foque nos produtos de maior margem.")
    else:
        print("\n●  O cenário não altera o lucro total.")

    # 2. Produtos com maior e menor margem
    melhor_prod = res_cenario.loc[res_cenario["lucro_total_novo"].idxmax()]
    pior_prod   = res_cenario.loc[res_cenario["lucro_total_novo"].idxmin()]
    print(f"\n   Produto mais lucrativo no cenário : {melhor_prod['produto']}"
          f"  (R$ {melhor_prod['lucro_total_novo']:,.2f})")
    print(f"   Produto menos lucrativo no cenário: {pior_prod['produto']}"
          f"  (R$ {pior_prod['lucro_total_novo']:,.2f})")

    # 3. Produtos com margem abaixo de 30% → alerta
    baixa_margem = res_cenario[res_cenario["margem_nova_pct"] < 30]
    if not baixa_margem.empty:
        nomes = ", ".join(baixa_margem["produto"].tolist())
        print(f"\n⚠  Produtos com margem abaixo de 30%: {nomes}")
        print("   Revise o custo ou reajuste o preço destes itens.")

    # 4. Se foi feita a tabela de faixa, indica o ponto ótimo
    if tab_faixa is not None:
        melhor = tab_faixa.loc[tab_faixa["lucro_total"].idxmax()]
        print(f"\n★  Variação ótima (faixa simulada): {melhor['variacao_pct']:+.0f}%")
        print(f"   Lucro máximo estimado: R$ {melhor['lucro_total']:,.2f}")
        if usar_elasticidade:
            print("   (com ajuste de demanda via elasticidade-preço)")

    # 5. Se otimizador rodou
    if otim is not None:
        print(f"\n{'─'*65}")
        print("  VARIAÇÃO ÓTIMA POR PRODUTO (otimizador):")
        print(f"{'─'*65}")
        print(f"  {'Produto':<22} {'Var. Ótima':>10} {'Lucro Ótimo':>13} {'Ganho':>12}")
        print(f"  {'─'*58}")
        for _, r in otim.iterrows():
            ganho = r["lucro_otimo"] - r["lucro_atual"]
            print(f"  {r['produto']:<22} {r['variacao_otima']:>+9.0f}%"
                  f" {r['lucro_otimo']:>13,.2f} {ganho:>+12,.2f}")
        lucro_otim_total = otim["lucro_otimo"].sum()
        print(f"\n  Lucro total se todas as otimizações forem aplicadas: R$ {lucro_otim_total:,.2f}")
        print(f"  Ganho potencial vs base: R$ {lucro_otim_total - lucro_base:+,.2f}")

    print("\n" + "═" * 65)

# ──────────────────────────────────────────────
# GRÁFICOS
# ──────────────────────────────────────────────
def plotar(df, res_cenario, tab_faixa=None, otim=None, usar_elasticidade=False, produto_foco=None):
    aplicar_estilo()
    n_graficos = 2 + (tab_faixa is not None) + (otim is not None)
    fig = plt.figure(figsize=(16, 10), facecolor=COR_FUNDO)
    fig.suptitle("ANÁLISE WHAT-IF – SIMULADOR DE LUCRO | LOJA DE VAREJO",
                 fontsize=14, fontweight="bold", color=COR_TEXTO, y=0.98)

    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.45, wspace=0.35)

    # ── Gráfico 1: Lucro antes x depois por produto ──
    ax1 = fig.add_subplot(gs[0, 0])
    x   = np.arange(len(res_cenario))
    w   = 0.35
    b1  = ax1.bar(x - w/2, res_cenario["lucro_total_base"], w,
                  label="Base", color=COR_NEUTRO, alpha=0.8)
    b2  = ax1.bar(x + w/2, res_cenario["lucro_total_novo"],  w,
                  label="Cenário",
                  color=[COR_POSITIVO if d >= 0 else COR_NEGATIVO
                         for d in res_cenario["delta_lucro"]], alpha=0.9)
    ax1.set_xticks(x)
    ax1.set_xticklabels(res_cenario["produto"], rotation=30, ha="right", fontsize=7)
    ax1.set_title("Lucro por Produto: Base vs Cenário", fontsize=10, color=COR_TEXTO)
    ax1.set_ylabel("Lucro (R$)", fontsize=8)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"R${v:,.0f}"))
    ax1.legend(fontsize=8)
    ax1.grid(axis="y")

    # ── Gráfico 2: Δ Lucro por produto ──
    ax2  = fig.add_subplot(gs[0, 1])
    cors = [COR_POSITIVO if d >= 0 else COR_NEGATIVO for d in res_cenario["delta_lucro"]]
    bars = ax2.barh(res_cenario["produto"], res_cenario["delta_lucro"], color=cors, alpha=0.9)
    ax2.axvline(0, color=COR_TEXTO, linewidth=0.8)
    ax2.set_title("Δ Lucro por Produto (vs Base)", fontsize=10, color=COR_TEXTO)
    ax2.set_xlabel("Variação de Lucro (R$)", fontsize=8)
    ax2.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"R${v:+,.0f}"))
    for bar, val in zip(bars, res_cenario["delta_lucro"]):
        ax2.text(bar.get_width() + (max(res_cenario["delta_lucro"]) * 0.02),
                 bar.get_y() + bar.get_height() / 2,
                 f"R${val:+,.0f}", va="center", fontsize=7, color=COR_TEXTO)
    ax2.grid(axis="x")

    # ── Gráfico 3: Curva de lucro por variação (tabela de faixa) ──
    if tab_faixa is not None:
        ax3 = fig.add_subplot(gs[1, 0])
        lucro_base_val = df["lucro_total_base"].sum()
        cors_linha = [COR_POSITIVO if l >= lucro_base_val else COR_NEGATIVO
                      for l in tab_faixa["lucro_total"]]
        for i in range(len(tab_faixa) - 1):
            ax3.plot(tab_faixa["variacao_pct"].iloc[i:i+2],
                     tab_faixa["lucro_total"].iloc[i:i+2],
                     color=cors_linha[i], linewidth=2)
        ax3.scatter(tab_faixa["variacao_pct"], tab_faixa["lucro_total"],
                    color=cors_linha, s=40, zorder=5)
        ax3.axhline(lucro_base_val, color=COR_DESTAQUE, linestyle="--",
                    linewidth=1.2, label=f"Base R${lucro_base_val:,.0f}")
        melhor = tab_faixa.loc[tab_faixa["lucro_total"].idxmax()]
        ax3.scatter(melhor["variacao_pct"], melhor["lucro_total"],
                    color=COR_DESTAQUE, s=120, zorder=6, marker="★", label="Melhor cenário")
        titulo = f"Lucro por Variação{'– ' + produto_foco if produto_foco else ' (Todos os Produtos)'}"
        ax3.set_title(titulo, fontsize=9, color=COR_TEXTO)
        ax3.set_xlabel("Variação de Preço (%)", fontsize=8)
        ax3.set_ylabel("Lucro Total (R$)", fontsize=8)
        ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"R${v:,.0f}"))
        ax3.legend(fontsize=8)
        ax3.grid()

    # ── Gráfico 4: Otimizador ──
    if otim is not None:
        ax4 = fig.add_subplot(gs[1, 1])
        cors_o = [COR_POSITIVO if v >= 0 else COR_NEGATIVO for v in otim["variacao_otima"]]
        bars4 = ax4.bar(otim["produto"], otim["variacao_otima"], color=cors_o, alpha=0.9)
        ax4.axhline(0, color=COR_TEXTO, linewidth=0.8)
        ax4.set_xticks(range(len(otim)))
        ax4.set_xticklabels(otim["produto"], rotation=30, ha="right", fontsize=7)
        ax4.set_title("Variação Ótima por Produto (Otimizador)", fontsize=9, color=COR_TEXTO)
        ax4.set_ylabel("Variação de Preço (%)", fontsize=8)
        for bar, val in zip(bars4, otim["variacao_otima"]):
            ax4.text(bar.get_x() + bar.get_width() / 2,
                     bar.get_height() + (0.5 if val >= 0 else -1.5),
                     f"{val:+.0f}%", ha="center", fontsize=7, color=COR_TEXTO)
        ax4.grid(axis="y")

    plt.savefig("grafico_whatif.png", dpi=130, bbox_inches="tight", facecolor=COR_FUNDO)
    plt.show()
    print("\n[INFO] Gráfico salvo em: grafico_whatif.png")

# ──────────────────────────────────────────────
# MODO INTERATIVO
# ──────────────────────────────────────────────
def modo_interativo(df):
    cabecalho()
    imprimir_base(df)
    print("\nMODO INTERATIVO")
    print(LINHA)
    print("Opções:")
    print("  1 – Aplicar variação global de preço")
    print("  2 – Aplicar variação por produto individualmente")
    print("  3 – Simular faixa de variação (tabela de cenários)")
    print("  4 – Encontrar variação ótima (otimizador)")
    print("  0 – Sair")
    print()

    opcao = input("Escolha uma opção: ").strip()

    usar_el = input("Usar elasticidade-preço na demanda? (s/N): ").strip().lower() == "s"

    tab_faixa = None
    otim      = None
    produto_foco = None

    if opcao == "1":
        v = float(input("Variação global (%): "))
        var_map = {p: v for p in df["produto"]}
        res = calcular_lucro(df, var_map, usar_el)
        imprimir_cenario(res, f"CENÁRIO: {v:+.1f}% EM TODOS OS PRODUTOS", usar_el)
        imprimir_recomendacao(df, res, usar_elasticidade=usar_el)
        plotar(df, res, usar_elasticidade=usar_el)

    elif opcao == "2":
        print("\nDigite a variação (%) para cada produto. Enter = 0%")
        var_map = {}
        for p in df["produto"]:
            raw = input(f"  {p}: ").strip()
            var_map[p] = float(raw) if raw else 0.0
        res = calcular_lucro(df, var_map, usar_el)
        imprimir_cenario(res, "CENÁRIO: VARIAÇÕES INDIVIDUAIS", usar_el)
        # faixa automática para o produto de maior variação
        prod_destaque = max(var_map, key=lambda p: abs(var_map[p]))
        tab_faixa = simular_faixa(df, -50, 50, 5, produto=prod_destaque, usar_elasticidade=usar_el)
        produto_foco = prod_destaque
        imprimir_tabela_faixa(tab_faixa)
        imprimir_recomendacao(df, res, tab_faixa, usar_elasticidade=usar_el)
        plotar(df, res, tab_faixa, usar_elasticidade=usar_el, produto_foco=produto_foco)

    elif opcao == "3":
        prod_input = input("Produto específico (Enter = todos): ").strip() or None
        if prod_input and prod_input not in df["produto"].values:
            print(f"[AVISO] Produto '{prod_input}' não encontrado. Usando todos.")
            prod_input = None
        inicio = float(input("Variação mínima (%): ") or -50)
        fim    = float(input("Variação máxima (%): ") or  50)
        passo  = float(input("Passo (%): ")           or   5)
        tab_faixa = simular_faixa(df, inicio, fim, passo, produto=prod_input, usar_elasticidade=usar_el)
        var_map   = {p: 0.0 for p in df["produto"]}
        res       = calcular_lucro(df, var_map, usar_el)
        imprimir_tabela_faixa(tab_faixa)
        imprimir_recomendacao(df, res, tab_faixa, usar_elasticidade=usar_el)
        plotar(df, res, tab_faixa, usar_elasticidade=usar_el, produto_foco=prod_input)

    elif opcao == "4":
        otim    = otimizar(df, usar_el)
        var_map = {r["produto"]: r["variacao_otima"] for _, r in otim.iterrows()}
        res     = calcular_lucro(df, var_map, usar_el)
        imprimir_cenario(res, "CENÁRIO: VARIAÇÕES ÓTIMAS (OTIMIZADOR)", usar_el)
        imprimir_recomendacao(df, res, otim=otim, usar_elasticidade=usar_el)
        plotar(df, res, otim=otim, usar_elasticidade=usar_el)

    elif opcao == "0":
        print("Saindo.")
        sys.exit(0)
    else:
        print("[ERRO] Opção inválida.")

# ──────────────────────────────────────────────
# PARSING DE ARGUMENTOS DE LINHA DE COMANDO
# ──────────────────────────────────────────────
def parse_args():
    args = sys.argv[1:]
    if not args:
        return None

    config = {
        "variacao":        None,
        "produto":         None,
        "faixa":           None,   # (inicio, fim, passo)
        "elasticidade":    False,
        "otimizar":        False,
        "ajuda":           False,
    }

    i = 0
    while i < len(args):
        a = args[i]
        if a in ("--ajuda", "-h", "--help"):
            config["ajuda"] = True
        elif a == "--variacao" and i + 1 < len(args):
            config["variacao"] = float(args[i + 1]); i += 1
        elif a == "--produto" and i + 1 < len(args):
            config["produto"] = args[i + 1]; i += 1
        elif a == "--faixa" and i + 3 < len(args):
            config["faixa"] = (float(args[i+1]), float(args[i+2]), float(args[i+3])); i += 3
        elif a == "--elasticidade":
            config["elasticidade"] = True
        elif a == "--otimizar":
            config["otimizar"] = True
        i += 1
    return config

# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
def main():
    config = parse_args()
    df     = carregar_dados()
    cabecalho()

    if config is None:
        modo_interativo(df)
        return

    if config["ajuda"]:
        print(__doc__)
        return

    usar_el   = config["elasticidade"]
    tab_faixa = None
    otim      = None
    produto_foco = config["produto"]
    imprimir_base(df)

    # ── Modo otimizar ──
    if config["otimizar"]:
        otim    = otimizar(df, usar_el)
        var_map = {r["produto"]: r["variacao_otima"] for _, r in otim.iterrows()}
        res     = calcular_lucro(df, var_map, usar_el)
        imprimir_cenario(res, "CENÁRIO: VARIAÇÕES ÓTIMAS (OTIMIZADOR)", usar_el)
        imprimir_recomendacao(df, res, otim=otim, usar_elasticidade=usar_el)
        plotar(df, res, otim=otim, usar_elasticidade=usar_el)
        return

    # ── Modo faixa ──
    if config["faixa"]:
        inicio, fim, passo = config["faixa"]
        tab_faixa = simular_faixa(df, inicio, fim, passo,
                                  produto=config["produto"], usar_elasticidade=usar_el)
        var_map   = {p: 0.0 for p in df["produto"]}
        res       = calcular_lucro(df, var_map, usar_el)
        imprimir_tabela_faixa(tab_faixa)
        imprimir_recomendacao(df, res, tab_faixa, usar_elasticidade=usar_el)
        plotar(df, res, tab_faixa, usar_elasticidade=usar_el, produto_foco=config["produto"])
        return

    # ── Modo variação simples ──
    if config["variacao"] is not None:
        v = config["variacao"]
        if config["produto"]:
            if config["produto"] not in df["produto"].values:
                print(f"[ERRO] Produto '{config['produto']}' não encontrado no CSV.")
                print("Produtos disponíveis:", list(df["produto"]))
                sys.exit(1)
            var_map = {p: (v if p == config["produto"] else 0.0) for p in df["produto"]}
            label   = f"CENÁRIO: {v:+.1f}% EM '{config['produto']}'"
        else:
            var_map = {p: v for p in df["produto"]}
            label   = f"CENÁRIO: {v:+.1f}% EM TODOS OS PRODUTOS"
        res = calcular_lucro(df, var_map, usar_el)
        tab_faixa = simular_faixa(df, -50, 50, 5, produto=config["produto"], usar_elasticidade=usar_el)
        imprimir_cenario(res, label, usar_el)
        imprimir_tabela_faixa(tab_faixa)
        imprimir_recomendacao(df, res, tab_faixa, usar_elasticidade=usar_el)
        plotar(df, res, tab_faixa, usar_elasticidade=usar_el, produto_foco=config["produto"])
        return

    # Se nenhum argumento útil, cai no interativo
    modo_interativo(df)

if __name__ == "__main__":
    main()