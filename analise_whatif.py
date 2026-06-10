import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
import os

CSV_PATH      = "produtos.csv"
ALERTA_MARGEM = 30.0
LINHA         = "─" * 70


#  DADOS
def carregar():
    if not os.path.exists(CSV_PATH):
        print(f"\n[ERRO] '{CSV_PATH}' não encontrado na mesma pasta.")
        sys.exit(1)
    df = pd.read_csv(CSV_PATH)
    df["lucro_base"]  = (df["preco_atual"] - df["custo_unitario"]) * df["quantidade_vendida"]
    df["margem_base"] = ((df["preco_atual"] - df["custo_unitario"]) / df["preco_atual"] * 100).round(1)
    return df

def calcular_cenario(df, variacoes):
    r = df.copy()
    r["variacao"]    = r["produto"].map(lambda p: variacoes.get(p, 0.0))
    r["preco_novo"]  = r["preco_atual"] * (1 + r["variacao"] / 100)
    r["lucro_novo"]  = (r["preco_novo"] - r["custo_unitario"]) * r["quantidade_vendida"]
    r["delta"]       = r["lucro_novo"] - r["lucro_base"]
    r["margem_nova"] = ((r["preco_novo"] - r["custo_unitario"]) / r["preco_novo"] * 100).round(1)
    return r

#  IMPRESSÃO
def imprimir_base(df):
    total = df["lucro_base"].sum()
    print(f"\n{'SITUAÇÃO ATUAL – PREÇOS BASE':^70}")
    print(LINHA)
    print(f"  {'Produto':<22} {'Categoria':<12} {'Preço':>8} {'Custo':>8} {'Qtd':>6} {'Margem':>8} {'Lucro':>12}")
    print(LINHA)
    for _, r in df.iterrows():
        print(f"  {r['produto']:<22} {r['categoria']:<12} {r['preco_atual']:>8.2f} "
              f"{r['custo_unitario']:>8.2f} {r['quantidade_vendida']:>6.0f} "
              f"{r['margem_base']:>7.1f}% {r['lucro_base']:>12.2f}")
    print(LINHA)
    print(f"  {'LUCRO TOTAL BASE':>57}  R$ {total:>10,.2f}")

def imprimir_cenario(res, titulo):
    base  = res["lucro_base"].sum()
    novo  = res["lucro_novo"].sum()
    delta = novo - base
    pct   = delta / base * 100
    print(f"\n{titulo:^70}")
    print(LINHA)
    print(f"  {'Produto':<22} {'Var%':>6} {'Preço Novo':>10} {'Margem':>8} {'Lucro Novo':>12} {'Δ Lucro':>12}")
    print(LINHA)
    for _, r in res.iterrows():
        sinal = f"{r['variacao']:+.1f}%" if r["variacao"] != 0 else "  —   "
        ind   = "▲" if r["delta"] > 0 else ("▼" if r["delta"] < 0 else " ")
        print(f"  {r['produto']:<22} {sinal:>6} {r['preco_novo']:>10.2f} "
              f"{r['margem_nova']:>7.1f}% {r['lucro_novo']:>12.2f} {ind}{r['delta']:>+11.2f}")
    print(LINHA)
    ind_tot = "▲" if delta > 0 else "▼"
    print(f"  {'LUCRO TOTAL NOVO':>57}  R$ {novo:>10,.2f}")
    print(f"  {'VARIAÇÃO VS BASE':>57}  {ind_tot} R$ {delta:>+10,.2f}  ({pct:+.1f}%)")

#  RECOMENDAÇÃO FINAL
def recomendar_melhor(df, historico):
    base = df["lucro_base"].sum()

    print(f"\n{'═'*70}")
    print(f"{'  COMPARATIVO DE CENÁRIOS SIMULADOS':^70}")
    print(f"{'═'*70}")
    print(f"\n  {'#':<3} {'Cenário':<30} {'Lucro Total':>14} {'Δ vs Base':>12} {'Δ%':>8}")
    print(f"  {LINHA}")

    melhor_idx   = 0
    melhor_lucro = -np.inf
    for i, c in enumerate(historico):
        d   = c["lucro"] - base
        dp  = d / base * 100
        ind = "★" if c["lucro"] == max(h["lucro"] for h in historico) else " "
        print(f"  {i+1:<3} {c['label']:<30} {c['lucro']:>14,.2f} {d:>+12,.2f} {dp:>+7.1f}%  {ind}")
        if c["lucro"] > melhor_lucro:
            melhor_lucro = c["lucro"]
            melhor_idx   = i

    melhor = historico[melhor_idx]
    res_m  = melhor["res"]
    delta  = melhor_lucro - base
    pct    = delta / base * 100

    print(f"\n{'═'*70}")
    print(f"{'  RECOMENDAÇÃO DO CENÁRIO MAIS VANTAJOSO':^70}")
    print(f"{'═'*70}")

    print(f"\n  ★  Cenário recomendado: {melhor['label']}")
    if delta > 0:
        print(f"  ✔  Lucro aumenta R$ {delta:,.2f} ({pct:+.1f}%) vs base.")
    elif delta < 0:
        print(f"  ✘  Todos os cenários reduzem o lucro. O menos prejudicial é este.")
        print(f"     Redução de R$ {abs(delta):,.2f} ({pct:+.1f}%) vs base.")
    else:
        print(f"  ●  Este cenário mantém o lucro igual à base.")

    ganhador = res_m.loc[res_m["delta"].idxmax()]
    perdedor = res_m.loc[res_m["delta"].idxmin()]
    print(f"\n  Produto com maior ganho : {ganhador['produto']:<22}  Δ R$ {ganhador['delta']:>+10,.2f}")
    print(f"  Produto com maior perda : {perdedor['produto']:<22}  Δ R$ {perdedor['delta']:>+10,.2f}")

    baixa = res_m[res_m["margem_nova"] < ALERTA_MARGEM]
    if not baixa.empty:
        nomes = ", ".join(baixa["produto"].tolist())
        print(f"\n  ⚠  Margem abaixo de {ALERTA_MARGEM:.0f}% no cenário recomendado: {nomes}")

    print(f"\n{'═'*70}\n")
    return melhor

#  GRÁFICOS
def plotar(df, historico):
    melhor_res  = max(historico, key=lambda h: h["lucro"])["res"]
    melhor_nome = max(historico, key=lambda h: h["lucro"])["label"]
    base        = df["lucro_base"].sum()

    COR = {"pos": "#2ecc71", "neg": "#e74c3c", "base": "#3498db",
           "dest": "#f39c12", "text": "#eeeeee", "panel": "#1a1a2e"}

    def estilo(ax):
        ax.set_facecolor(COR["panel"])
        ax.tick_params(colors=COR["text"], labelsize=8)
        ax.xaxis.label.set_color(COR["text"])
        ax.yaxis.label.set_color(COR["text"])
        ax.title.set_color(COR["text"])
        for sp in ax.spines.values():
            sp.set_edgecolor("#333")
        ax.grid(color="#2a2a3e", linestyle="--", alpha=0.5)

    fmt_r = plt.FuncFormatter(lambda v, _: f"R${v:,.0f}")

    #  GRÁFICO 1: Lucro por Produto: Base vs Melhor Cenário
    fig1, ax1 = plt.subplots(figsize=(12, 6), facecolor="#0f0f1a")
    fig1.suptitle("Lucro por Produto: Base vs Melhor Cenário",
                  fontsize=12, fontweight="bold", color="white", y=0.98)
    res = melhor_res
    x   = np.arange(len(res))
    w   = 0.38
    ax1.bar(x - w/2, res["lucro_base"], w, label="Base",   color=COR["base"], alpha=0.75)
    ax1.bar(x + w/2, res["lucro_novo"], w, label=f"Melhor ({melhor_nome})",
            color=[COR["pos"] if d >= 0 else COR["neg"] for d in res["delta"]], alpha=0.9)
    ax1.set_xticks(x)
    ax1.set_xticklabels(res["produto"], rotation=28, ha="right", fontsize=7.5)
    ax1.set_ylabel("Lucro (R$)")
    ax1.yaxis.set_major_formatter(fmt_r)
    ax1.legend(fontsize=8, facecolor="#1a1a2e", labelcolor=COR["text"])
    novo_t = res["lucro_novo"].sum()
    cor_t  = COR["pos"] if novo_t >= base else COR["neg"]
    ax1.text(0.01, 0.95, f"Base: R${base:,.0f}", transform=ax1.transAxes,
             fontsize=8.5, color=COR["base"], va="top")
    ax1.text(0.14, 0.95, f"Melhor cenário: R${novo_t:,.0f}  ({(novo_t-base)/base*100:+.1f}%)",
             transform=ax1.transAxes, fontsize=8.5, color=cor_t, va="top")
    estilo(ax1)
    nome1 = "lucro_base_vs_melhor_cenario.png"
    fig1.savefig(nome1, dpi=120, bbox_inches="tight", facecolor="#0f0f1a")
    plt.close(fig1)

    #  GRÁFICO 2: Variação do Lucro por Produto (Melhor Cenário vs Base)
    fig2, ax2 = plt.subplots(figsize=(10, 6), facecolor="#0f0f1a")
    fig2.suptitle("Variação do Lucro por Produto (Melhor Cenário vs Base)",
                  fontsize=12, fontweight="bold", color="white", y=0.98)
    cors = [COR["pos"] if d >= 0 else COR["neg"] for d in res["delta"]]
    ax2.barh(res["produto"], res["delta"], color=cors, alpha=0.9)
    ax2.axvline(0, color=COR["text"], linewidth=0.7)
    ax2.set_xlabel("Variação de Lucro (R$)")
    ax2.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"R${v:+,.0f}"))
    ax2.tick_params(axis="y", labelsize=7.5)
    estilo(ax2)
    nome2 = "variacao_lucro_por_produto.png"
    fig2.savefig(nome2, dpi=120, bbox_inches="tight", facecolor="#0f0f1a")
    plt.close(fig2)

    #  GRÁFICO 3: Comparativo de todos os cenários
    fig3, ax3 = plt.subplots(figsize=(10, 6), facecolor="#0f0f1a")
    fig3.suptitle("Comparativo: Lucro por Cenário Simulado",
                  fontsize=12, fontweight="bold", color="white", y=0.98)
    nomes  = [h["label"][:25] for h in historico]
    lucros = [h["lucro"] for h in historico]
    cors3  = [COR["dest"] if l == max(lucros) else
              (COR["pos"] if l >= base else COR["neg"]) for l in lucros]
    bars = ax3.bar(range(len(historico)), lucros, color=cors3, alpha=0.9)
    ax3.axhline(base, color=COR["base"], linestyle="--", linewidth=1.2,
                label=f"Base: R${base:,.0f}")
    ax3.set_xticks(range(len(historico)))
    ax3.set_xticklabels(nomes, rotation=20, ha="right", fontsize=7.5)
    ax3.set_ylabel("Lucro Total (R$)")
    ax3.yaxis.set_major_formatter(fmt_r)
    ax3.legend(fontsize=8, facecolor="#1a1a2e", labelcolor=COR["text"])
    for bar, val in zip(bars, lucros):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.005,
                 f"R${val:,.0f}", ha="center", va="bottom", fontsize=6.5, color=COR["text"])
    estilo(ax3)
    nome3 = "comparativo_cenarios.png"
    fig3.savefig(nome3, dpi=120, bbox_inches="tight", facecolor="#0f0f1a")
    plt.close(fig3)

    #  GRÁFICO COMBINADO
    import matplotlib.gridspec as gridspec
    fig_all = plt.figure(figsize=(16, 9), facecolor="#0f0f1a")
    fig_all.suptitle("ANÁLISE WHAT-IF — SIMULAÇÃO DE LUCRO | LOJA DE VAREJO",
                     fontsize=13, fontweight="bold", color="white", y=0.98)
    gs = gridspec.GridSpec(2, 2, figure=fig_all, hspace=0.52, wspace=0.35)

    axc1 = fig_all.add_subplot(gs[0, :])
    axc1.bar(x - w/2, res["lucro_base"], w, label="Base", color=COR["base"], alpha=0.75)
    axc1.bar(x + w/2, res["lucro_novo"], w, label=f"Melhor ({melhor_nome})",
             color=[COR["pos"] if d >= 0 else COR["neg"] for d in res["delta"]], alpha=0.9)
    axc1.set_xticks(x)
    axc1.set_xticklabels(res["produto"], rotation=28, ha="right", fontsize=7.5)
    axc1.set_title("Lucro por Produto: Base vs Melhor Cenário", fontsize=10)
    axc1.set_ylabel("Lucro (R$)")
    axc1.yaxis.set_major_formatter(fmt_r)
    axc1.legend(fontsize=8, facecolor="#1a1a2e", labelcolor=COR["text"])
    axc1.text(0.01, 0.95, f"Base: R${base:,.0f}", transform=axc1.transAxes,
              fontsize=8.5, color=COR["base"], va="top")
    axc1.text(0.14, 0.95, f"Melhor cenário: R${novo_t:,.0f}  ({(novo_t-base)/base*100:+.1f}%)",
              transform=axc1.transAxes, fontsize=8.5, color=cor_t, va="top")
    estilo(axc1)

    axc2 = fig_all.add_subplot(gs[1, 0])
    axc2.barh(res["produto"], res["delta"], color=cors, alpha=0.9)
    axc2.axvline(0, color=COR["text"], linewidth=0.7)
    axc2.set_title("Δ Lucro por Produto (Melhor Cenário vs Base)", fontsize=9)
    axc2.set_xlabel("Variação de Lucro (R$)")
    axc2.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"R${v:+,.0f}"))
    axc2.tick_params(axis="y", labelsize=7.5)
    estilo(axc2)

    axc3 = fig_all.add_subplot(gs[1, 1])
    bars_c = axc3.bar(range(len(historico)), lucros, color=cors3, alpha=0.9)
    axc3.axhline(base, color=COR["base"], linestyle="--", linewidth=1.2,
                 label=f"Base: R${base:,.0f}")
    axc3.set_xticks(range(len(historico)))
    axc3.set_xticklabels(nomes, rotation=20, ha="right", fontsize=7.5)
    axc3.set_title("Comparativo: Lucro por Cenário Simulado", fontsize=9)
    axc3.set_ylabel("Lucro Total (R$)")
    axc3.yaxis.set_major_formatter(fmt_r)
    axc3.legend(fontsize=8, facecolor="#1a1a2e", labelcolor=COR["text"])
    for bar, val in zip(bars_c, lucros):
        axc3.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.005,
                  f"R${val:,.0f}", ha="center", va="bottom", fontsize=6.5, color=COR["text"])
    estilo(axc3)

    nome_combinado = "painel_geral.png"
    fig_all.savefig(nome_combinado, dpi=120, bbox_inches="tight", facecolor="#0f0f1a")
    plt.close(fig_all)

#  CENÁRIOS AUTOMÁTICOS PRÉ-DEFINIDOS
def cenarios_automaticos(df):
    """
    Retorna uma lista de cenários pré-configurados baseados em regras
    de negócio sobre os dados atuais.
    """
    cenarios = []

    # auxiliares
    df_sorted_qtd = df.sort_values("quantidade_vendida", ascending=False)
    top5_volume   = df_sorted_qtd.head(5)["produto"].tolist()
    bot5_volume   = df_sorted_qtd.tail(5)["produto"].tolist()
    media_margem  = df["margem_base"].mean()

    # ── 1. Otimista: sobe preço em margens altas, leve ajuste nas baixas ──
    vm_otimista = {}
    for _, r in df.iterrows():
        if r["margem_base"] >= media_margem:
            vm_otimista[r["produto"]] = +10.0
        else:
            vm_otimista[r["produto"]] = +5.0
    cenarios.append({"label": "Otimista (+10% marg alta, +5% demais)",
                     "variacoes": vm_otimista})

    # 2. Pessimista: redução generalizada (crise/recessão)
    vm_pessimista = {p: -15.0 for p in df["produto"]}
    cenarios.append({"label": "Pessimista (-15% global)",
                     "variacoes": vm_pessimista})

    # 3. Foco em Volume: desconto nos campeões de venda, compensa no resto
    vm_volume = {}
    for _, r in df.iterrows():
        if r["produto"] in top5_volume:
            vm_volume[r["produto"]] = -10.0
        else:
            vm_volume[r["produto"]] = +8.0
    cenarios.append({"label": "Foco Volume (-10% Top5, +8% demais)",
                     "variacoes": vm_volume})

    # 4. Premium: sobe preço nos itens de nicho (baixo volume, margem alta)
    vm_premium = {p: 0.0 for p in df["produto"]}
    for p in bot5_volume:
        vm_premium[p] = +20.0
    cenarios.append({"label": "Premium (+20% nos 5 de menor volume)",
                     "variacoes": vm_premium})

    return cenarios


#  MODO INTERATIVO
def modo_interativo(df):
    plt.ion()
    historico = []

    while True:
        imprimir_base(df)
        n = len(historico)
        print(f"\n{'MENU PRINCIPAL':^70}")
        print(LINHA)
        print("  1  Aplicar variação % global em todos os produtos")
        print("  2  Aplicar variação % individual por produto")
        print("  3  Executar cenários automáticos pré-definidos")
        if n > 0:
            print(f"  R  Ver recomendação ({n} cenário{'s' if n>1 else ''} simulado{'s' if n>1 else ''})")
        print("  0  Sair")
        print()

        opcao = input("  Opção: ").strip().upper()

        if opcao == "0":
            if historico:
                recomendar_melhor(df, historico)
                plotar(df, historico)
                plt.ioff()
                plt.show()
            print("\n  Encerrando.\n")
            break

        elif opcao == "1":
            try:
                v = float(input("  Variação % para todos (ex: 10 ou -15): "))
            except ValueError:
                print("  [ERRO] Digite um número válido."); continue
            vm    = {p: v for p in df["produto"]}
            res   = calcular_cenario(df, vm)
            label = f"Global {v:+.0f}%"
            imprimir_cenario(res, f"CENÁRIO: {v:+.1f}% EM TODOS OS PRODUTOS")
            historico.append({"label": label, "variacoes": vm,
                               "lucro": res["lucro_novo"].sum(), "res": res})
            print(f"\n  Cenário '{label}' registrado. Total acumulado: {len(historico)} cenário(s).")

        elif opcao == "2":
            print(f"\n  Digite a variação % por produto (Enter = 0%, sem alteração):")
            vm = {}
            for p in df["produto"]:
                raw = input(f"    {p:<25}: ").strip()
                vm[p] = float(raw) if raw else 0.0
            res   = calcular_cenario(df, vm)
            label = f"Individual #{len(historico)+1}"
            imprimir_cenario(res, "CENÁRIO: VARIAÇÕES INDIVIDUAIS")
            historico.append({"label": label, "variacoes": vm,
                               "lucro": res["lucro_novo"].sum(), "res": res})
            print(f"\n  Cenário '{label}' registrado. Total acumulado: {len(historico)} cenário(s).")

        elif opcao == "3":
            auto = cenarios_automaticos(df)
            for i, c in enumerate(auto):
                print(f"  {i+1}  {c['label']}")
            print(f"  A  Executar TODOS de uma vez")
            print(f"  0  Voltar")
            print()
            sub = input("  Escolha o cenário (1-4, A ou 0): ").strip().upper()

            if sub == "0":
                print("  Voltando ao menu principal.")
            elif sub == "A":
                for c in auto:
                    res   = calcular_cenario(df, c["variacoes"])
                    label = c["label"]
                    c["lucro"] = res["lucro_novo"].sum()
                    c["res"]   = res
                    imprimir_cenario(res, f"CENÁRIO: {label}")
                    historico.append({"label": label, "variacoes": c["variacoes"],
                                       "lucro": c["lucro"], "res": res})
                print(f"\n  {len(auto)} cenários automáticos registrados. "
                      f"Total acumulado: {len(historico)} cenário(s).")
            elif sub in ("1", "2", "3", "4"):
                idx  = int(sub) - 1
                c    = auto[idx]
                res  = calcular_cenario(df, c["variacoes"])
                c["lucro"] = res["lucro_novo"].sum()
                c["res"]   = res
                imprimir_cenario(res, f"CENÁRIO: {c['label']}")
                historico.append({"label": c["label"], "variacoes": c["variacoes"],
                                   "lucro": c["lucro"], "res": res})
                print(f"\n  Cenário '{c['label']}' registrado. "
                      f"Total acumulado: {len(historico)} cenário(s).")
            else:
                print("  [ERRO] Escolha inválida. Voltando ao menu.")

        elif opcao == "R" and historico:
            recomendar_melhor(df, historico)
            plotar(df, historico)

        else:
            print("  [ERRO] Opção inválida.")

        input("\n  [Enter para continuar...]\n")


#  MAIN
def main():
    args = sys.argv[1:]
    df   = carregar()

    if not args:
        modo_interativo(df)
        return

    if "--lista" in args:
        print("\nProdutos disponíveis:")
        for p in df["produto"]:
            print(f"  {p}")
        return

    if "--global" in args:
        idx = args.index("--global")
        if idx + 1 >= len(args):
            print("[ERRO] --global requer um valor percentual. Ex: --global 10")
            return
        v   = float(args[idx + 1])
        vm  = {p: v for p in df["produto"]}
        res = calcular_cenario(df, vm)
        imprimir_cenario(res, f"CENÁRIO: {v:+.1f}% EM TODOS OS PRODUTOS")
        historico = [{"label": f"Global {v:+.0f}%", "variacoes": vm,
                      "lucro": res["lucro_novo"].sum(), "res": res}]
        recomendar_melhor(df, historico)
        plotar(df, historico)
        plt.show()
        return

    if "--auto" in args:
        auto = cenarios_automaticos(df)
        historico = []
        for c in auto:
            res = calcular_cenario(df, c["variacoes"])
            c["lucro"] = res["lucro_novo"].sum()
            c["res"]   = res
            imprimir_cenario(res, f"CENÁRIO: {c['label']}")
            historico.append({"label": c["label"], "variacoes": c["variacoes"],
                               "lucro": c["lucro"], "res": res})
        recomendar_melhor(df, historico)
        plotar(df, historico)
        plt.show()
        return

    print(__doc__)

if __name__ == "__main__":
    main()