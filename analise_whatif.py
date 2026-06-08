import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# -----------------------------------------------
# Carrega os dados
# -----------------------------------------------
df = pd.read_csv("produtos.csv")

# Calcula lucro base
df["lucro_unitario"] = df["preco_atual"] - df["custo_unitario"]
df["lucro_total"] = df["lucro_unitario"] * df["quantidade_vendida"]

lucro_base = df["lucro_total"].sum()

print("=" * 55)
print("       ANÁLISE WHAT-IF – LOJA DE VAREJO")
print("=" * 55)
print(f"\nLucro base (preços atuais): R$ {lucro_base:,.2f}\n")
print(df[["produto", "preco_atual", "custo_unitario", "quantidade_vendida", "lucro_total"]].to_string(index=False))

# -----------------------------------------------
# Cenários de variação de preço (what-if)
# Simula variações de -30% a +30% nos preços
# -----------------------------------------------
variacoes = list(range(-30, 35, 5))   # -30%, -25%, ... +30%
lucros_cenarios = []

for v in variacoes:
    fator = 1 + v / 100
    lucro_cenario = ((df["preco_atual"] * fator - df["custo_unitario"]) * df["quantidade_vendida"]).sum()
    lucros_cenarios.append(lucro_cenario)

resultados = pd.DataFrame({
    "variacao_pct": variacoes,
    "lucro_total": lucros_cenarios
})

print("\n" + "=" * 55)
print("  CENÁRIOS – VARIAÇÃO GERAL DE PREÇO")
print("=" * 55)
print(resultados.to_string(index=False))

# Melhor cenário
melhor = resultados.loc[resultados["lucro_total"].idxmax()]
print(f"\nMelhor cenário: {melhor['variacao_pct']:+.0f}% → Lucro R$ {melhor['lucro_total']:,.2f}")

# -----------------------------------------------
# Gráfico 1: Lucro por variação de preço
# -----------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle("Análise What-If – Loja de Varejo", fontsize=14, fontweight="bold")

cores = ["red" if l < lucro_base else "steelblue" for l in resultados["lucro_total"]]
axes[0].bar(resultados["variacao_pct"], resultados["lucro_total"], color=cores, width=4)
axes[0].axhline(lucro_base, color="black", linestyle="--", linewidth=1, label=f"Base: R$ {lucro_base:,.0f}")
axes[0].set_title("Lucro Total por Variação de Preço")
axes[0].set_xlabel("Variação de Preço (%)")
axes[0].set_ylabel("Lucro Total (R$)")
axes[0].legend()
axes[0].yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"R${x:,.0f}"))

# -----------------------------------------------
# Gráfico 2: Contribuição de cada produto no lucro base
# -----------------------------------------------
axes[1].barh(df["produto"], df["lucro_total"], color="steelblue")
axes[1].set_title("Lucro por Produto (Cenário Atual)")
axes[1].set_xlabel("Lucro Total (R$)")
axes[1].xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"R${x:,.0f}"))

plt.tight_layout()
plt.savefig("grafico_whatif.png", dpi=120)
plt.show()
print("\nGráfico salvo em: grafico_whatif.png")

# -----------------------------------------------
# Análise por produto: qual variação maximiza lucro?
# (considerando elasticidade simples: preço maior = qty cai)
# -----------------------------------------------
print("\n" + "=" * 55)
print("  RECOMENDAÇÃO FINAL")
print("=" * 55)

# Ponto de ruptura: preço mínimo para lucro positivo por produto
df["preco_minimo"] = df["custo_unitario"]
df["margem_pct"] = ((df["preco_atual"] - df["custo_unitario"]) / df["preco_atual"] * 100).round(1)

print(df[["produto", "preco_atual", "preco_minimo", "margem_pct", "lucro_total"]].to_string(index=False))

idx_maior = df["lucro_total"].idxmax()
print(f"\nProduto mais lucrativo: {df.loc[idx_maior, 'produto']} (R$ {df.loc[idx_maior, 'lucro_total']:,.2f})")

v_melhor = int(melhor["variacao_pct"])
print(f"Cenário recomendado: ajuste de {v_melhor:+d}% nos preços → Lucro estimado R$ {melhor['lucro_total']:,.2f}")
if v_melhor > 0:
    print("→ Aumentar preços eleva o lucro, desde que a demanda se mantenha.")
elif v_melhor < 0:
    print("→ Reduzir preços pode aumentar volume, mas comprime a margem.")
else:
    print("→ Os preços atuais já estão no ponto ótimo para este modelo.")