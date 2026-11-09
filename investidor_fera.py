# ════════════════════════════════════════════════════════════════════════
# INVESTIDOR FERA — aprenda a investir e acompanhe sua carteira (arquivo único)
# MeusAgentesIA.com.br
#
# Aprender → Montar a carteira → Acompanhar → Pente fino → Evoluir até "Fera"
#
# COMO PUBLICAR
#   Coloque SÓ este arquivo num repositório do GitHub e publique no
#   Streamlit Cloud (share.streamlit.io). Não precisa de requirements.txt:
#   usa só o que já vem com o Streamlit (requests, pandas, altair).
#   Cada pessoa entra com o próprio nome e a própria chave Groq (grátis).
#
# REGRAS DO SISTEMA
#   • Números, cálculos, rentabilidades e percentuais são feitos pelo APP.
#     A IA só explica, interpreta e orienta — nunca inventa resultados.
#   • O app é EDUCATIVO: ensina, mostra riscos e acompanha. Não recomenda
#     comprar ou vender um ativo específico (isso exige registro na CVM).
# ════════════════════════════════════════════════════════════════════════
import json
import os
import re
import uuid
from datetime import date, datetime, timedelta

import altair as alt
import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="Investidor Fera", page_icon="📈", layout="wide")

SITE = "https://meusagentesia.com.br"
GROQ_URL = os.environ.get("IF_GROQ_URL", "https://api.groq.com/openai/v1/chat/completions")
YAHOO = os.environ.get("IF_YAHOO", "https://{host}.finance.yahoo.com")
BCB = os.environ.get("IF_BCB", "https://api.bcb.gov.br")
MODELOS = ["openai/gpt-oss-120b", "llama-3.3-70b-versatile"]
HOJE = date.today()
S = st.session_state

# ══════════════════════════════════════════════════════════════════════════
# VISUAL
# ══════════════════════════════════════════════════════════════════════════
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] {font-family:'Inter',sans-serif;}
.stApp {background:#F7F9F8;}
.stApp, .stApp p, .stApp li, .stApp label, .stApp span, .stMarkdown {color:#14231C;}
h1,h2,h3 {color:#0E2A1F !important;}
.stTabs [data-baseweb="tab-list"] {gap:2px; overflow-x:auto;}
.stTabs [data-baseweb="tab"] {background:#EAF2EE; border-radius:10px 10px 0 0; padding:8px 14px; color:#1D3B2E;}
.stTabs [aria-selected="true"] {background:#0F5132 !important; color:#fff !important;}
.stTabs [aria-selected="true"] p {color:#fff !important;}
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
  background:#0F5132; color:#fff !important; border:none; border-radius:10px; font-weight:600; min-height:2.8em;}
.stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover {background:#0B3D26; color:#fff !important;}
.stButton > button p, .stDownloadButton > button p, .stFormSubmitButton > button p {color:#fff !important;}
.stTextInput input, .stNumberInput input, .stTextArea textarea, .stDateInput input {background:#fff !important; color:#14231C !important;}
div[data-baseweb="select"] > div {background:#fff !important; color:#14231C !important;}
.card {background:#fff; border:1px solid #D5E3DC; border-radius:14px; padding:16px 18px; margin-bottom:10px;}
.cab {background:linear-gradient(135deg,#0F5132,#13734A); border-radius:16px; padding:20px 24px; margin-bottom:12px;}
.cab h1, .stApp .cab h1, .stApp .cab h1 span {color:#fff !important; margin:0; font-size:1.9em;}
.cab p {color:#D7F0E3 !important; margin:4px 0 0 0;}
.kpi {background:#fff; border:1px solid #D5E3DC; border-radius:14px; padding:14px; text-align:center;}
.kpi .v {font-size:1.55em; font-weight:800; color:#0E2A1F; font-variant-numeric:tabular-nums;}
.kpi .l {font-size:.8em; color:#4B6358; text-transform:uppercase; letter-spacing:.04em;}
.pos {color:#0F7A43 !important; font-weight:700;} .neg {color:#B42318 !important; font-weight:700;}
.achado {border-left:6px solid #9AA8A1; background:#fff; border-radius:10px; padding:10px 14px; margin-bottom:8px; border-top:1px solid #E3ECE7; border-right:1px solid #E3ECE7; border-bottom:1px solid #E3ECE7;}
.achado.critico {border-left-color:#B42318;} .achado.alerta {border-left-color:#D97706;} .achado.ok {border-left-color:#0F7A43;} .achado.info {border-left-color:#2563EB;}
.nivel {display:inline-block; background:#0F5132; color:#fff !important; border-radius:20px; padding:4px 12px; font-weight:700; font-size:.85em;}
.aviso-cvm {font-size:.8em; color:#4B6358 !important;}
</style>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# CONTEÚDO EDUCATIVO
# ══════════════════════════════════════════════════════════════════════════
NIVEIS_TRILHA = {
    1: "🌱 Fundamentos",
    2: "🏦 Renda fixa",
    3: "📊 Renda variável",
    4: "🧠 Estratégia",
}

# (id, nível, título, pontos-chave, perguntas de reserva [pergunta, opções, índice correto, explicação])
MODULOS = [
    ("m1", 1, "Reserva de emergência e orçamento", [
        "Antes de investir em bolsa, monte uma **reserva de emergência**: de 6 a 12 meses dos seus gastos mensais.",
        "A reserva fica em algo **seguro e com liquidez diária**: Tesouro Selic ou CDB que pague 100% do CDI ou mais, com resgate no mesmo dia.",
        "Use a regra simples: anote quanto entra e quanto sai por mês. O que sobra é a sua capacidade de investir.",
        "Dívida cara (cartão, cheque especial) quase sempre custa mais do que qualquer investimento rende: quite antes.",
    ], [
        ("Onde faz mais sentido deixar a reserva de emergência?", ["Ações de uma empresa sólida", "Tesouro Selic ou CDB com liquidez diária", "Fundo imobiliário", "Criptomoedas"], 1, "A reserva precisa ser segura e estar disponível a qualquer momento."),
        ("Quantos meses de gastos é o tamanho recomendado da reserva?", ["1 mês", "De 6 a 12 meses", "24 meses no mínimo", "Não precisa de reserva"], 1, "De 6 a 12 meses cobre a maioria dos imprevistos (desemprego, saúde)."),
        ("Você tem R$ 3.000 no cartão a 12% ao mês. O que fazer primeiro?", ["Investir em ações", "Quitar a dívida", "Comprar FIIs", "Deixar na poupança"], 1, "Nenhum investimento seguro paga 12% ao mês: quitar a dívida é o melhor 'rendimento'."),
    ]),
    ("m2", 1, "Juros compostos e inflação", [
        "**Juros compostos** são juros sobre juros: o rendimento de hoje também passa a render amanhã. O tempo é o maior aliado.",
        "**Inflação (IPCA)** é a perda do poder de compra. O que importa é o **ganho real**: quanto você ganhou acima da inflação.",
        "Exemplo: render 10% num ano com inflação de 4% é um ganho real de cerca de 5,8% (1,10 ÷ 1,04 − 1).",
        "Começar cedo e aportar todo mês costuma valer mais do que tentar acertar o 'melhor momento'.",
    ], [
        ("O que são juros compostos?", ["Juros cobrados só no início", "Juros sobre juros", "Juros que não mudam nunca", "Imposto sobre o rendimento"], 1, "O rendimento é reinvestido e passa a render também."),
        ("Seu investimento rendeu 8% e a inflação foi 8%. Seu ganho real foi:", ["8%", "16%", "Praticamente zero", "4%"], 2, "Rendeu o mesmo que a inflação: o poder de compra ficou igual."),
        ("Qual fator mais aumenta o resultado dos juros compostos?", ["Tempo investido", "Trocar de banco", "Olhar a carteira todo dia", "Sorte"], 0, "Quanto mais tempo, mais os juros se acumulam."),
    ]),
    ("m3", 1, "Risco, retorno e liquidez", [
        "Todo investimento equilibra três coisas: **segurança**, **rentabilidade** e **liquidez** (rapidez para virar dinheiro). Nenhum entrega as três no máximo.",
        "Quanto **maior o retorno esperado, maior o risco**. Promessa de ganho alto e garantido é sinal de golpe.",
        "**Volatilidade** é o quanto o preço sobe e desce. Ações oscilam muito no curto prazo; por isso são para objetivos de longo prazo.",
        "Defina o **prazo** de cada objetivo: dinheiro que você vai usar em menos de 2 anos não deve ficar em renda variável.",
    ], [
        ("Alguém promete 5% ao mês garantido. Isso é:", ["Ótima oportunidade", "Sinal forte de golpe", "Normal na bolsa", "Igual ao Tesouro"], 1, "Retorno alto e garantido não existe; quanto maior o retorno, maior o risco."),
        ("Liquidez é:", ["O quanto um investimento rende", "A rapidez para transformar o investimento em dinheiro", "O imposto cobrado", "A taxa da corretora"], 1, "Liquidez é a facilidade de resgatar sem perder valor."),
        ("Dinheiro para dar entrada num apartamento daqui a 1 ano deve ficar em:", ["Ações", "Criptomoedas", "Renda fixa com vencimento ou liquidez adequada", "Opções"], 2, "Prazo curto pede investimentos previsíveis."),
    ]),
    ("m4", 2, "Tesouro Direto", [
        "São títulos do governo federal, considerados o investimento **mais seguro do país**.",
        "**Tesouro Selic**: acompanha a Selic, quase não oscila — ótimo para reserva. **Tesouro Prefixado**: taxa fixa definida na compra. **Tesouro IPCA+**: inflação + uma taxa fixa — protege o poder de compra no longo prazo.",
        "Prefixado e IPCA+ sofrem **marcação a mercado**: se vender antes do vencimento, pode ganhar ou perder. Levando até o vencimento, recebe a taxa combinada.",
        "Há taxa de custódia da B3 (0,20% ao ano), com isenção no Tesouro Selic para até R$ 10 mil.",
    ], [
        ("Qual título do Tesouro é mais indicado para reserva de emergência?", ["Tesouro IPCA+ 2045", "Tesouro Prefixado 2031", "Tesouro Selic", "Nenhum"], 2, "O Tesouro Selic quase não oscila e tem liquidez diária."),
        ("O que é marcação a mercado?", ["Taxa da corretora", "Variação do preço do título antes do vencimento", "Imposto sobre o lucro", "Depósito mínimo"], 1, "O preço do título muda com os juros do mercado até o vencimento."),
        ("O Tesouro IPCA+ paga:", ["Só a inflação", "Inflação mais uma taxa fixa", "Uma taxa fixa sem inflação", "A Selic"], 1, "Ele protege o poder de compra e ainda paga um ganho real."),
    ]),
    ("m5", 2, "CDB, LCI, LCA e o FGC", [
        "**CDB** é um empréstimo que você faz ao banco. Pode ser pós-fixado (% do CDI), prefixado ou atrelado ao IPCA.",
        "**LCI e LCA** são parecidas, mas **isentas de IR** para pessoa física — compare sempre a rentabilidade líquida.",
        "O **FGC** garante até **R$ 250 mil por CPF por instituição** (limite global de R$ 1 milhão a cada 4 anos) em CDB, LCI, LCA e poupança.",
        "Bancos menores pagam mais porque têm mais risco. Respeite o limite do FGC e veja a carência (prazo em que o dinheiro fica preso).",
    ], [
        ("Um CDB de 100% do CDI e uma LCI de 90% do CDI, ambos por 2 anos: qual a maior diferença?", ["A LCI é isenta de IR", "O CDB é garantido e a LCI não", "A LCI tem marcação a mercado", "Não há diferença"], 0, "A LCI não paga IR; compare a rentabilidade líquida."),
        ("Quanto o FGC garante por CPF em cada instituição?", ["R$ 50 mil", "R$ 100 mil", "R$ 250 mil", "Sem limite"], 2, "Até R$ 250 mil por CPF por instituição, com teto global."),
        ("Por que um banco pequeno paga 120% do CDI?", ["Por bondade", "Porque tem mais risco e precisa atrair investidores", "Porque é do governo", "Porque é isento"], 1, "Mais risco precisa de mais retorno para atrair dinheiro."),
    ]),
    ("m6", 2, "Impostos na renda fixa", [
        "A renda fixa tributada segue a **tabela regressiva de IR** sobre o rendimento: **22,5%** até 180 dias, **20%** de 181 a 360, **17,5%** de 361 a 720 e **15%** acima de 720 dias.",
        "O **IOF** só existe em resgates com menos de 30 dias e vai de 96% do rendimento no 1º dia até zero no 30º.",
        "**LCI, LCA, CRI, CRA e debêntures incentivadas** continuam isentas de IR para pessoa física em 2026.",
        "O imposto é **retido na fonte** pelo banco ou corretora: você não precisa emitir guia, só declarar no IR anual.",
    ], [
        ("Qual a alíquota de IR de um CDB resgatado após 3 anos?", ["22,5%", "20%", "17,5%", "15%"], 3, "Acima de 720 dias a alíquota é 15%."),
        ("Quando há cobrança de IOF?", ["Sempre", "Em resgates com menos de 30 dias", "Só em ações", "Nunca"], 1, "O IOF zera a partir do 30º dia."),
        ("Quem recolhe o IR do CDB?", ["Você, por DARF", "O banco/corretora, na fonte", "Ninguém", "A Receita no fim do ano"], 1, "Na renda fixa o IR é retido na fonte."),
    ]),
    ("m7", 3, "Como funciona a bolsa", [
        "A **B3** é a bolsa do Brasil. Você compra e vende ações, FIIs e ETFs por meio de uma **corretora**, no home broker ou no aplicativo.",
        "Cada ativo tem um **código (ticker)**: final 3 = ação ordinária (ex.: VALE3), 4 = preferencial (PETR4), 11 = units, FIIs e ETFs (MXRF11, BOVA11), 34/35 = BDRs.",
        "Ações são negociadas em **lotes de 100** ou no **mercado fracionário** (código com F no fim, ex.: PETR4F), a partir de 1 unidade.",
        "A liquidação acontece em **D+2** (dois dias úteis). O pregão regular vai das 10h às 17h (horário de Brasília) — horários podem mudar no horário de verão dos EUA.",
    ], [
        ("O que significa o final 11 em um código como MXRF11?", ["Sempre ação ordinária", "Normalmente FII, ETF ou unit", "Ação preferencial", "Título público"], 1, "O final 11 aparece em FIIs, ETFs e units."),
        ("Para comprar menos de 100 ações, você usa:", ["O mercado fracionário", "O Tesouro Direto", "Um CDB", "Não é possível"], 0, "No fracionário compra-se a partir de 1 ação."),
        ("Quem intermedeia sua compra na bolsa?", ["O Banco Central", "A corretora", "O FGC", "A Receita Federal"], 1, "A corretora leva sua ordem até a B3."),
    ]),
    ("m8", 3, "Ações: o que analisar", [
        "Comprar uma ação é virar **sócio** de uma empresa. O preço no longo prazo tende a acompanhar o **lucro** da empresa.",
        "Indicadores básicos: **P/L** (preço ÷ lucro por ação), **P/VP** (preço ÷ patrimônio), **ROE** (lucro ÷ patrimônio — eficiência), **Dividend Yield** (dividendos ÷ preço) e **Dívida líquida/EBITDA** (endividamento).",
        "Nenhum indicador sozinho decide. Compare com empresas do **mesmo setor** e veja o histórico de vários anos.",
        "Desconfie de dividend yield muito alto: pode ser um lucro que não vai se repetir ou uma ação caindo muito.",
    ], [
        ("O que mede o ROE?", ["O tamanho da dívida", "A eficiência da empresa em gerar lucro com o patrimônio", "O preço da ação", "O dividendo"], 1, "ROE = lucro líquido ÷ patrimônio líquido."),
        ("Uma ação com dividend yield de 25% num ano deve:", ["Ser comprada sem pensar", "Ser investigada: pode ser lucro não recorrente ou preço despencando", "Ser ignorada", "Ser vendida a descoberto"], 1, "Yield muito alto costuma ter explicação."),
        ("Comparar o P/L de um banco com o de uma empresa de tecnologia é:", ["Ideal", "Pouco útil: compare com o mesmo setor", "Obrigatório", "Proibido"], 1, "Setores diferentes têm padrões diferentes."),
    ]),
    ("m9", 3, "Fundos imobiliários (FIIs)", [
        "FIIs juntam dinheiro de muitos investidores para ter imóveis (**fundos de tijolo**: lajes, galpões, shoppings) ou títulos do setor (**fundos de papel**: CRIs).",
        "Pagam **rendimentos mensais**, que hoje são **isentos de IR** para pessoa física (fundo com 100+ cotistas, negociado em bolsa e você com menos de 10% das cotas).",
        "Olhe: **P/VP**, vacância (imóveis vazios), qualidade dos inquilinos e dos imóveis, liquidez diária e diversificação.",
        "O **lucro na venda** das cotas paga **20% de IR**, sem a isenção de R$ 20 mil das ações.",
    ], [
        ("Como são tributados os rendimentos mensais de FIIs para pessoa física (regra geral)?", ["15%", "20%", "Isentos", "22,5%"], 2, "Os rendimentos são isentos, se o fundo cumpre as condições."),
        ("Lucro na venda de cotas de FII paga:", ["Isento até R$ 20 mil", "20% de IR", "15% de IR", "Nada"], 1, "Ganho de capital em FII paga 20%, sem isenção."),
        ("Vacância alta em um FII de tijolo indica:", ["Muitos imóveis vazios, renda menor", "Fundo muito lucrativo", "Fundo de papel", "Nada importante"], 0, "Imóvel vazio não gera aluguel."),
    ]),
    ("m10", 3, "ETFs e BDRs", [
        "**ETFs** são fundos negociados em bolsa que copiam um índice: BOVA11 (Ibovespa), IVVB11 (S&P 500), entre outros. Diversificação com uma compra só.",
        "**BDRs** (final 34/35) são recibos de empresas estrangeiras negociados na B3, como uma porta de entrada para o exterior.",
        "Investir no exterior diversifica o risco do Brasil e a moeda. Mas o dólar também oscila.",
        "ETFs de renda variável **não têm a isenção** de R$ 20 mil mensais: o lucro na venda paga 15%.",
    ], [
        ("O que faz um ETF como BOVA11?", ["Paga juros fixos", "Replica o Ibovespa", "É um título público", "Garante lucro"], 1, "Ele copia a carteira do índice."),
        ("Vender R$ 10 mil de ETF com lucro gera IR?", ["Não, isento até R$ 20 mil", "Sim, 15% sobre o lucro", "Só se for day trade", "Não, ETFs nunca pagam"], 1, "ETFs não têm a isenção de R$ 20 mil."),
        ("Um BDR com final 34 representa:", ["Uma empresa estrangeira", "Um FII", "Um título do Tesouro", "Uma criptomoeda"], 0, "BDRs são recibos de ativos estrangeiros."),
    ]),
    ("m11", 4, "Diversificação e alocação de ativos", [
        "**Alocação de ativos** é decidir quanto do patrimônio vai para cada classe (renda fixa, ações, FIIs, exterior). Ela explica a maior parte do resultado no longo prazo.",
        "Diversificar é não depender de uma empresa, um setor ou um país. Uma referência comum é **nenhum ativo passar de 10% a 20%** da carteira.",
        "A alocação depende do **perfil**, do **prazo** e dos **objetivos** — não da notícia do dia.",
        "Ter 30 ativos parecidos não é diversificar: o importante é que se comportem de formas diferentes.",
    ], [
        ("O que mais explica o resultado de uma carteira no longo prazo?", ["A alocação entre classes de ativos", "A hora do dia em que você compra", "O nome da corretora", "A cor do gráfico"], 0, "A divisão entre classes pesa mais do que escolhas pontuais."),
        ("Ter 15 ações de bancos é uma carteira diversificada?", ["Sim", "Não, todas dependem do mesmo setor", "Depende do dia", "Só se forem estatais"], 1, "Mesmo setor = riscos parecidos."),
        ("Um único ativo com 50% da carteira representa:", ["Boa diversificação", "Concentração de risco alta", "Carteira conservadora", "Proteção contra inflação"], 1, "Se esse ativo cair, metade do patrimônio sofre."),
    ]),
    ("m12", 4, "Aportes e rebalanceamento", [
        "**Aporte regular** (todo mês) é o motor da carteira: compra em vários preços e cria o hábito.",
        "**Rebalancear** é voltar à alocação-alvo: quando uma classe sobe muito e passa do alvo, os novos aportes vão para as que ficaram abaixo.",
        "Rebalancear com aportes evita vender e pagar imposto. Revise a carteira de 3 em 3 ou de 6 em 6 meses.",
        "Isso força o comportamento certo: comprar mais do que está barato em relação ao seu plano.",
    ], [
        ("Suas ações subiram e passaram do alvo (30% → 40%). Um jeito simples de rebalancear é:", ["Vender tudo", "Direcionar os próximos aportes para as classes abaixo do alvo", "Comprar mais ações", "Não fazer nada nunca"], 1, "Aportes nas classes abaixo do alvo rebalanceiam sem vender."),
        ("Com que frequência faz sentido revisar a alocação?", ["Todo minuto", "A cada 3 a 6 meses", "Nunca", "Só quando a bolsa cai 50%"], 1, "Revisões periódicas evitam decisões por impulso."),
        ("Por que o aporte mensal é importante?", ["Porque garante lucro", "Porque cria hábito e compra em preços diferentes ao longo do tempo", "Porque evita impostos", "Porque o banco exige"], 1, "Aportar sempre reduz o risco de comprar tudo num preço ruim."),
    ]),
    ("m13", 4, "Dividendos e renda passiva", [
        "**Dividendos** e **JCP** são parte do lucro distribuída aos acionistas. FIIs distribuem **rendimentos** mensais.",
        "**JCP** tem 15% de IR retido na fonte. Dividendos: a partir de 2026 (Lei 15.270), há retenção de **10%** quando uma mesma empresa paga **mais de R$ 50 mil no mês** à mesma pessoa — para a maioria dos investidores pessoa física nada muda.",
        "**Reinvestir** os proventos acelera os juros compostos. Uma carteira de renda passiva leva anos para ser construída.",
        "Para estimar a **renda passiva**, use: patrimônio × yield médio ÷ 12. A regra dos 4% ao ano é uma referência comum para retiradas.",
    ], [
        ("O que é JCP?", ["Juros sobre capital próprio, com 15% de IR na fonte", "Um tipo de FII", "Um título público", "Uma taxa da corretora"], 0, "JCP é uma forma de distribuir lucro, com IR retido."),
        ("Reinvestir os dividendos ajuda porque:", ["Aumenta os juros compostos", "Evita a bolsa", "Zera o risco", "Paga menos taxa"], 0, "Os proventos compram mais cotas, que geram mais proventos."),
        ("Com R$ 600 mil e yield de 8% ao ano, a renda passiva mensal estimada é de:", ["R$ 2.000", "R$ 4.000", "R$ 8.000", "R$ 48.000"], 1, "600.000 × 8% ÷ 12 = R$ 4.000."),
    ]),
    ("m14", 4, "Psicologia do investidor", [
        "Os maiores erros vêm do **comportamento**: vender no pânico, comprar na euforia, seguir dica de grupo, trocar de estratégia toda semana.",
        "**Viés de confirmação**: buscar só o que concorda com você. **Aversão à perda**: a dor de perder pesa mais do que o prazer de ganhar.",
        "Tenha um **plano escrito** (objetivos, alocação, regras de aporte) e siga o plano, não as manchetes.",
        "Olhar a carteira todo dia aumenta a ansiedade. Acompanhe com método e no ritmo do seu objetivo.",
    ], [
        ("A bolsa caiu 15% em um mês. Atitude mais coerente com um plano de longo prazo:", ["Vender tudo", "Seguir o plano e os aportes", "Pegar empréstimo e comprar tudo", "Apagar o aplicativo"], 1, "Quedas fazem parte; o plano existe para esses momentos."),
        ("Comprar uma ação porque 'todo mundo do grupo está comprando' é:", ["Análise fundamentalista", "Efeito manada", "Rebalanceamento", "Diversificação"], 1, "Seguir a multidão sem análise é efeito manada."),
        ("Ter um plano escrito ajuda a:", ["Garantir lucro", "Evitar decisões por emoção", "Pagar menos imposto", "Escolher a melhor ação"], 1, "Regras definidas antes reduzem o impulso."),
    ]),
    ("m15", 4, "Imposto de renda na bolsa", [
        "**Ações (swing trade)**: 15% sobre o lucro, mas **isento** se o total de **vendas** de ações no mês for de até **R$ 20 mil**.",
        "**Day trade**: 20% sobre o lucro, sem isenção. **FIIs**: 20% sobre o lucro na venda. **ETFs**: 15%, sem isenção.",
        "O imposto é pago por você com **DARF** até o último dia útil do mês seguinte à venda (código 6015). Prejuízos podem ser compensados com lucros futuros do mesmo tipo.",
        "Todo ano, declare posições, lucros isentos e proventos na **declaração de IR**. Guarde as notas de corretagem.",
    ], [
        ("Você vendeu R$ 15 mil em ações no mês com lucro de R$ 3 mil (swing trade). Paga IR?", ["Sim, 15%", "Não, vendas até R$ 20 mil no mês são isentas", "Sim, 20%", "Sim, 22,5%"], 1, "Vendas totais de ações até R$ 20 mil no mês são isentas."),
        ("Como se paga o IR do lucro em ações acima da isenção?", ["Retido pelo banco", "DARF até o último dia útil do mês seguinte", "No fim do ano, sem guia", "Não paga"], 1, "Na bolsa, o próprio investidor emite o DARF."),
        ("Prejuízo em ações pode:", ["Ser compensado com lucros futuros", "Ser descontado do salário", "Ser ignorado", "Ser transferido a outra pessoa"], 0, "Prejuízos ficam acumulados para compensar lucros."),
    ]),
]
MOD = {m[0]: m for m in MODULOS}

PERGUNTAS_PERFIL = [
    ("Por quanto tempo você pretende deixar o dinheiro investido?",
     [("Menos de 1 ano", 0), ("De 1 a 3 anos", 1), ("De 3 a 5 anos", 2), ("Mais de 5 anos", 3)]),
    ("Seus investimentos caíram 20% em um mês. O que você faria?",
     [("Venderia tudo para não perder mais", 0), ("Venderia uma parte", 1), ("Manteria e esperaria", 2), ("Aproveitaria para comprar mais", 3)]),
    ("Qual frase combina mais com você?",
     [("Não aceito perder dinheiro", 0), ("Aceito pequenas oscilações", 1), ("Aceito oscilações por mais retorno", 2), ("Busco o maior retorno, mesmo com risco alto", 3)]),
    ("Quanto você já sabe de investimentos?",
     [("Nada, só poupança", 0), ("Já investi em renda fixa", 1), ("Já investi em ações ou FIIs", 2), ("Invisto há anos em várias classes", 3)]),
    ("Que parte da sua renda está comprometida com gastos fixos?",
     [("Mais de 80%", 0), ("De 60% a 80%", 1), ("De 40% a 60%", 2), ("Menos de 40%", 3)]),
    ("Qual o principal objetivo desse dinheiro?",
     [("Segurança e reserva", 0), ("Um objetivo em poucos anos (carro, viagem)", 1), ("Aposentadoria / independência financeira", 3), ("Fazer o patrimônio crescer o máximo possível", 3)]),
]

CLASSES = ["Renda fixa", "Ações", "FIIs", "ETFs e BDRs", "Cripto"]
ALVOS = {
    "Conservador": {"Renda fixa": 80, "Ações": 5, "FIIs": 10, "ETFs e BDRs": 5, "Cripto": 0},
    "Moderado":    {"Renda fixa": 55, "Ações": 20, "FIIs": 15, "ETFs e BDRs": 10, "Cripto": 0},
    "Arrojado":    {"Renda fixa": 30, "Ações": 35, "FIIs": 15, "ETFs e BDRs": 15, "Cripto": 5},
}
TAXA_REAL_PADRAO = {"Conservador": 4.0, "Moderado": 5.0, "Arrojado": 6.0}

NIVEIS_INV = [  # (nome, xp mínimo, requisito de módulos do nível)
    ("🌱 Iniciante", 0, 0),
    ("📘 Aprendiz", 300, 1),
    ("💼 Investidor", 800, 2),
    ("🧭 Estrategista", 1600, 3),
    ("🦁 Fera", 2600, 4),
]

TIPOS_RF = ["Pós-fixado (% do CDI)", "Prefixado (% ao ano)", "IPCA + taxa (% ao ano)", "Poupança"]
INDEXADO_ISENTO = ["LCI", "LCA", "CRI", "CRA", "Debênture incentivada"]
PRODUTOS_RF = ["Tesouro Selic", "Tesouro Prefixado", "Tesouro IPCA+", "CDB", "LCI", "LCA", "CRI", "CRA",
               "Debênture", "Debênture incentivada", "Poupança", "Fundo de renda fixa", "Outro"]

REGRA_IA = (
    "Você é o MENTOR INVESTIDOR FERA, um educador financeiro brasileiro, paciente, claro e honesto. Escreva em português "
    "do Brasil, com linguagem simples, exemplos práticos e sem jargão sem explicação. REGRAS OBRIGATÓRIAS: "
    "1) Você é EDUCATIVO: explique conceitos, riscos, prós e contras e como a pessoa pode analisar por conta própria. "
    "NUNCA diga para comprar ou vender um ativo específico, nunca dê preço-alvo e nunca prometa retorno. Se pedirem "
    "'qual ação comprar', explique como analisar e quais critérios usar, e lembre que recomendação individual exige "
    "um profissional certificado (analista CNPI ou consultor CVM). "
    "2) Use SOMENTE os números fornecidos pelo aplicativo; não invente rentabilidades, preços, cotações ou dados de "
    "empresas. Se faltar informação, diga o que a pessoa precisa registrar ou pesquisar (ex.: no site de RI da empresa, "
    "na B3, no Tesouro Direto). 3) Regras de IR atuais no Brasil (2026): renda fixa tabela regressiva 22,5/20/17,5/15%; "
    "LCI, LCA, CRI, CRA e debêntures incentivadas isentas para pessoa física; ações swing trade 15% com isenção para "
    "vendas até R$ 20 mil/mês; day trade 20%; FIIs: rendimentos isentos (regra geral) e lucro na venda 20%; ETFs 15% "
    "sem isenção; dividendos: retenção de 10% quando uma mesma empresa paga mais de R$ 50 mil no mês à mesma pessoa "
    "(Lei 15.270/2025). Se houver dúvida sobre regra recente, diga para confirmar na Receita Federal. "
    "4) Reforce sempre reserva de emergência, diversificação, prazo e perfil. 5) Seja direto: use títulos curtos e "
    "listas quando ajudar. Não use tabelas muito largas."
)


# ══════════════════════════════════════════════════════════════════════════
# ESTADO
# ══════════════════════════════════════════════════════════════════════════
CHAVES_MEMORIA = ["i_nome", "perfil", "respostas_perfil", "financas", "ops", "rf", "proventos", "metas", "modulos",
                  "revisoes", "xp", "xp_log", "chat", "precos", "premissas", "aulas", "aportes"]
PADRAO = {
    "i_nome": "", "i_chave": "", "perfil": "", "respostas_perfil": {}, "ver": 0,
    "financas": {"renda": 0.0, "gastos": 0.0, "reserva": 0.0, "aporte_plano": 0.0, "dividas_caras": False},
    "ops": [], "rf": [], "proventos": [], "metas": [], "modulos": {}, "revisoes": [], "xp": 0, "xp_log": [],
    "chat": [], "precos": {}, "aulas": {}, "aportes": [], "quiz": None, "indicadores": None,
    "mercado": {}, "ultima_atualizacao": None, "auto_min": 5, "noticias": "",
    "premissas": {"cdi": 13.65, "selic": 13.75, "ipca": 4.5, "tr": 0.10, "taxa_real": None, "brapi_token": ""},
}
for k, v in PADRAO.items():
    if k not in S:
        S[k] = json.loads(json.dumps(v)) if isinstance(v, (dict, list)) else v


def ganhar_xp(qtd, motivo, unico=None):
    """Soma XP. 'unico' evita pontuar a mesma conquista duas vezes."""
    if unico and any(x.get("id") == unico for x in S.xp_log):
        return
    S.xp += qtd
    S.xp_log.append({"id": unico or str(uuid.uuid4())[:8], "data": HOJE.isoformat(), "xp": qtd, "motivo": motivo})


# ══════════════════════════════════════════════════════════════════════════
# UTILITÁRIOS
# ══════════════════════════════════════════════════════════════════════════
def brl(v):
    try:
        s = f"{float(v):,.2f}"
    except Exception:
        return "R$ —"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


def pct(v, casas=1):
    try:
        return f"{float(v):+.{casas}f}%".replace(".", ",")
    except Exception:
        return "—"


def num(v, casas=2):
    try:
        return f"{float(v):,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "—"


def br_data(iso):
    try:
        return datetime.fromisoformat(str(iso)[:10]).strftime("%d/%m/%Y")
    except Exception:
        return str(iso)


def limpar_md(t):
    t = re.sub(r"\*\*(.+?)\*\*", r"\1", str(t or ""))
    return re.sub(r"(?m)^\s{0,3}#{1,6}\s+", "", t).strip()


def ticker_ok(t):
    return re.sub(r"[^A-Z0-9]", "", str(t).upper().strip())


def classe_sugerida(t):
    t = ticker_ok(t)
    if re.search(r"(34|35|39)$", t):
        return "ETFs e BDRs"
    if t.endswith("11"):
        return "FIIs"
    if re.search(r"[3-8]$", t):
        return "Ações"
    if t in ("BTC", "ETH", "SOL", "USDT"):
        return "Cripto"
    return "Ações"


# ══════════════════════════════════════════════════════════════════════════
# IA (GROQ)
# ══════════════════════════════════════════════════════════════════════════
def ia(mensagens, max_tokens=1800, temperatura=0.5, json_mode=False):
    ultimo = "Não consegui falar com a IA."
    for modelo in MODELOS:
        corpo = {"model": modelo, "messages": mensagens, "temperature": temperatura, "max_tokens": max_tokens}
        if json_mode:
            corpo["response_format"] = {"type": "json_object"}
        try:
            r = requests.post(GROQ_URL, headers={"Authorization": f"Bearer {S.i_chave}", "Content-Type": "application/json"},
                              json=corpo, timeout=90)
        except requests.RequestException:
            ultimo = "Sem conexão com a IA agora. Tente de novo em instantes."
            continue
        if r.status_code == 200:
            try:
                return r.json()["choices"][0]["message"]["content"].strip()
            except Exception:
                ultimo = "A IA respondeu num formato inesperado."
                continue
        if r.status_code in (401, 403):
            raise RuntimeError("A Groq recusou a sua chave. Clique em Sair e entre com a chave certa (começa com gsk_).")
        if r.status_code == 429:
            raise RuntimeError("Você atingiu o limite de uso grátis da Groq por agora. Espere alguns minutos e tente de novo.")
        ultimo = f"A IA respondeu com erro ({r.status_code})."
    raise RuntimeError(ultimo)


MODELOS_WEB = ["groq/compound", "groq/compound-mini"]


def ia_web(pergunta, max_tokens=1800):
    """Pergunta com pesquisa na internet em tempo real (modelos Compound da Groq)."""
    msgs = [{"role": "system", "content": REGRA_IA + " Pesquise na internet informações RECENTES antes de responder, "
             "cite a data e a fonte (nome do site) de cada notícia, e separe fatos de opiniões."},
            {"role": "system", "content": "DADOS DO ALUNO (calculados pelo app):\n" + contexto_aluno()},
            {"role": "user", "content": pergunta}]
    ultimo = "A pesquisa na internet não está disponível agora."
    for modelo in MODELOS_WEB:
        try:
            r = requests.post(GROQ_URL, headers={"Authorization": f"Bearer {S.i_chave}", "Content-Type": "application/json"},
                              json={"model": modelo, "messages": msgs, "max_tokens": max_tokens}, timeout=120)
        except requests.RequestException:
            continue
        if r.status_code == 200:
            try:
                return r.json()["choices"][0]["message"]["content"].strip()
            except Exception:
                continue
        if r.status_code in (401, 403):
            raise RuntimeError("A Groq recusou a sua chave. Clique em Sair e entre com a chave certa (começa com gsk_).")
        if r.status_code == 429:
            raise RuntimeError("Você atingiu o limite de uso grátis da Groq por agora. Espere alguns minutos e tente de novo.")
        ultimo = f"A pesquisa na internet respondeu com erro ({r.status_code})."
    raise RuntimeError(ultimo)


def ia_texto(pedido, contexto=True, max_tokens=1800):
    msgs = [{"role": "system", "content": REGRA_IA}]
    if contexto:
        msgs.append({"role": "system", "content": "DADOS DO ALUNO (calculados pelo app):\n" + contexto_aluno()})
    msgs.append({"role": "user", "content": pedido})
    return ia(msgs, max_tokens=max_tokens)


def ia_json(pedido, max_tokens=1800):
    msgs = [{"role": "system", "content": REGRA_IA + " Responda SOMENTE com um objeto JSON válido."},
            {"role": "user", "content": pedido}]
    try:
        txt = ia(msgs, max_tokens=max_tokens, temperatura=0.4, json_mode=True)
    except RuntimeError as e:
        if "chave" in str(e) or "limite" in str(e):
            raise
        txt = ia(msgs, max_tokens=max_tokens, temperatura=0.4)
    m = re.search(r"\{.*\}", txt, re.S)
    if not m:
        raise RuntimeError("A IA não devolveu o formato esperado. Tente de novo.")
    return json.loads(m.group(0))


# ══════════════════════════════════════════════════════════════════════════
# DADOS DE MERCADO (cotações e indicadores)
# ══════════════════════════════════════════════════════════════════════════
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}


def risco_historico(fechamentos):
    """Volatilidade anualizada (30 pregões) e maior queda do topo (3 meses), calculadas pelo app."""
    f = [float(x) for x in fechamentos if x]
    if len(f) < 10:
        return None, None
    ret = [f[k] / f[k - 1] - 1 for k in range(1, len(f))][-30:]
    media = sum(ret) / len(ret)
    dp = (sum((x - media) ** 2 for x in ret) / max(len(ret) - 1, 1)) ** 0.5
    topo, dd = f[0], 0.0
    for x in f:
        topo = max(topo, x)
        dd = min(dd, x / topo - 1)
    return dp * (252 ** 0.5) * 100, dd * 100


def cotacao_yahoo(t, simbolo=None):
    simbolo = simbolo or (t if t.startswith("^") or "-" in t or "=" in t else f"{t}.SA")
    for host in ("query1", "query2"):
        try:
            r = requests.get(YAHOO.format(host=host) + f"/v8/finance/chart/{simbolo}",
                             params={"range": "3mo", "interval": "1d"}, headers=UA, timeout=12)
            if r.status_code != 200:
                continue
            res = r.json()["chart"]["result"][0]
            meta = res["meta"]
            preco = meta.get("regularMarketPrice") or meta.get("previousClose")
            if not preco:
                continue
            fech = (res.get("indicators", {}).get("quote") or [{}])[0].get("close") or []
            ant = meta.get("chartPreviousClose")
            limpos = [x for x in fech if x]
            if len(limpos) >= 2:
                ant = limpos[-2] if abs(limpos[-1] - float(preco)) < 1e-6 else limpos[-1]
            vol, dd = risco_historico(limpos)
            hora = meta.get("regularMarketTime")
            return {"preco": float(preco), "fonte": "Yahoo Finance",
                    "var_dia": ((float(preco) / float(ant) - 1) * 100) if ant else None, "vol": vol, "dd": dd,
                    "pregao": datetime.fromtimestamp(hora).strftime("%d/%m %H:%M") if hora else ""}
        except Exception:
            continue
    return None


def cotacao_brapi(t):
    params = {}
    if S.premissas.get("brapi_token"):
        params["token"] = S.premissas["brapi_token"]
    try:
        r = requests.get(f"https://brapi.dev/api/quote/{t}", params=params, headers=UA, timeout=12)
        if r.status_code == 200:
            res = r.json().get("results") or []
            if res and res[0].get("regularMarketPrice"):
                return {"preco": float(res[0]["regularMarketPrice"]), "fonte": "brapi",
                        "var_dia": res[0].get("regularMarketChangePercent"), "vol": None, "dd": None, "pregao": ""}
    except Exception:
        pass
    return None


def cotacao_cripto(t):
    return cotacao_yahoo(t, f"{t}-BRL")


def buscar_cotacao(t, classe):
    t = ticker_ok(t)
    achou = cotacao_cripto(t) if classe == "Cripto" else (cotacao_yahoo(t) or cotacao_brapi(t))
    if achou:
        S.precos[t] = {**achou, "quando": datetime.now().strftime("%d/%m %H:%M"), "ts": datetime.now().timestamp(), "manual": False}
        return True
    return False


MERCADO = {"Ibovespa": "^BVSP", "Dólar": "USDBRL=X", "S&P 500": "^GSPC"}


def atualizar_tudo():
    """Atualiza mercado e todos os ativos da carteira (exceto preços manuais)."""
    S.mercado = {}
    for nome, simb in MERCADO.items():
        q = cotacao_yahoo(nome, simb)
        if q:
            S.mercado[nome] = q
    falha = []
    for p in [x for x in posicoes_rv() if x["qtd"] > 1e-9]:
        if S.precos.get(p["ticker"], {}).get("manual"):
            continue
        if not buscar_cotacao(p["ticker"], p["classe"]):
            falha.append(p["ticker"])
    S.ultima_atualizacao = datetime.now()
    return falha


def risco_agora(r):
    """Risco da carteira com as cotações do momento (cálculo do app)."""
    rv = [p for p in r["rv"] if p["tem_cotacao"]]
    tot = r["total"] or 1
    var_cart = sum((S.precos[p["ticker"]].get("var_dia") or 0) * p["atual"] for p in rv) / tot
    vol_cart = sum((S.precos[p["ticker"]].get("vol") or 0) * p["atual"] for p in rv) / tot  # sem correlação: limite superior
    perda_dia = 1.65 * vol_cart / (252 ** 0.5) / 100 * tot
    quedas = [(p["ticker"], S.precos[p["ticker"]]["var_dia"]) for p in rv if (S.precos[p["ticker"]].get("var_dia") or 0) <= -3]
    volateis = [(p["ticker"], S.precos[p["ticker"]]["vol"]) for p in rv if (S.precos[p["ticker"]].get("vol") or 0) >= 50]
    return {"var_dia": var_cart, "vol": vol_cart, "perda_dia": perda_dia, "quedas": quedas, "volateis": volateis,
            "ganho_dia": var_cart / 100 * tot}


def bcb_ultimo(serie):
    try:
        r = requests.get(f"{BCB}/dados/serie/bcdata.sgs.{serie}/dados/ultimos/1",
                         params={"formato": "json"}, headers=UA, timeout=12)
        if r.status_code == 200:
            return float(str(r.json()[-1]["valor"]).replace(",", "."))
    except Exception:
        pass
    return None


def atualizar_indicadores():
    """CDI e Selic ao ano e IPCA em 12 meses, direto do Banco Central (com valores de reserva)."""
    cdi, selic, ipca = bcb_ultimo(4389), bcb_ultimo(432), bcb_ultimo(13522)
    ok = []
    if cdi:
        S.premissas["cdi"] = round(cdi, 2); ok.append("CDI")
    if selic:
        S.premissas["selic"] = round(selic, 2); ok.append("Selic")
    if ipca:
        S.premissas["ipca"] = round(ipca, 2); ok.append("IPCA")
    S.indicadores = {"quando": datetime.now().strftime("%d/%m/%Y %H:%M"), "ok": ok}
    return ok


def cdi_acumulado(inicio_iso):
    """Fator do CDI entre a data e hoje. Tenta a série diária do BC; senão usa a taxa anual atual."""
    try:
        ini = datetime.fromisoformat(inicio_iso[:10]).date()
    except Exception:
        return 1.0
    if ini >= HOJE:
        return 1.0
    chave = f"_cdi_{ini.isoformat()}"
    if chave in S:
        return S[chave]
    fator = None
    try:
        r = requests.get(f"{BCB}/dados/serie/bcdata.sgs.12/dados",
                         params={"formato": "json", "dataInicial": ini.strftime("%d/%m/%Y"), "dataFinal": HOJE.strftime("%d/%m/%Y")},
                         headers=UA, timeout=15)
        if r.status_code == 200:
            vals = [float(str(x["valor"]).replace(",", ".")) for x in r.json()]
            if vals:
                fator = 1.0
                for v in vals:
                    fator *= 1 + v / 100
    except Exception:
        fator = None
    if fator is None:
        du = (HOJE - ini).days * 252 / 365
        fator = (1 + S.premissas["cdi"] / 100) ** (du / 252)
    S[chave] = fator
    return fator


# ══════════════════════════════════════════════════════════════════════════
# CÁLCULOS DA CARTEIRA (feitos pelo app)
# ══════════════════════════════════════════════════════════════════════════
def aliquota_rf(dias):
    if dias <= 180:
        return 22.5
    if dias <= 360:
        return 20.0
    if dias <= 720:
        return 17.5
    return 15.0


def valor_rf(item):
    """Valor bruto estimado hoje, rendimento e IR estimado de um título de renda fixa."""
    if item.get("valor_manual"):
        bruto = float(item["valor_manual"])
    else:
        aplic = float(item["valor"])
        try:
            ini = datetime.fromisoformat(item["data"]).date()
        except Exception:
            ini = HOJE
        dias = max((HOJE - ini).days, 0)
        anos = dias / 365
        tipo, taxa = item["tipo"], float(item.get("taxa") or 0)
        if tipo.startswith("Pós"):
            f_cdi = cdi_acumulado(item["data"])
            bruto = aplic * (1 + (f_cdi - 1) * taxa / 100)
        elif tipo.startswith("Pré"):
            bruto = aplic * (1 + taxa / 100) ** (dias * 252 / 365 / 252)
        elif tipo.startswith("IPCA"):
            bruto = aplic * (1 + S.premissas["ipca"] / 100) ** anos * (1 + taxa / 100) ** anos
        else:  # poupança
            selic = S.premissas["selic"]
            mensal = 0.005 + S.premissas["tr"] / 100 if selic > 8.5 else (1 + selic * 0.7 / 100) ** (1 / 12) - 1
            bruto = aplic * (1 + mensal) ** (dias / 30.4)
    rend = bruto - float(item["valor"])
    isento = item["produto"] in INDEXADO_ISENTO or item["produto"] == "Poupança"
    try:
        dias = (HOJE - datetime.fromisoformat(item["data"]).date()).days
    except Exception:
        dias = 0
    ir = 0.0 if isento or rend <= 0 else rend * aliquota_rf(dias) / 100
    return bruto, rend, ir


def posicoes_rv():
    """Consolida as operações: quantidade, preço médio, lucro realizado (por ativo)."""
    pos = {}
    for op in sorted(S.ops, key=lambda o: (o["data"], o.get("criado", ""))):
        t = op["ticker"]
        p = pos.setdefault(t, {"ticker": t, "classe": op["classe"], "qtd": 0.0, "custo": 0.0, "realizado": 0.0})
        q, preco, taxas = float(op["qtd"]), float(op["preco"]), float(op.get("taxas") or 0)
        if op["tipo"] == "Compra":
            p["custo"] += q * preco + taxas
            p["qtd"] += q
        else:
            pm = p["custo"] / p["qtd"] if p["qtd"] else 0
            vend = min(q, p["qtd"])
            p["realizado"] += vend * preco - taxas - vend * pm
            p["custo"] -= vend * pm
            p["qtd"] -= vend
        p["classe"] = op["classe"]
    linhas = []
    for t, p in pos.items():
        if p["qtd"] <= 1e-9 and abs(p["realizado"]) < 1e-9:
            continue
        pm = p["custo"] / p["qtd"] if p["qtd"] > 1e-9 else 0
        info = S.precos.get(t)
        preco = info["preco"] if info else pm
        atual = p["qtd"] * preco
        linhas.append({**p, "pm": pm, "preco": preco, "tem_cotacao": bool(info), "atual": atual,
                       "lucro": atual - p["custo"], "rent": ((preco / pm - 1) * 100) if pm else 0.0})
    return linhas


def resumo_carteira():
    rv = [p for p in posicoes_rv() if p["qtd"] > 1e-9]
    rf_lin = []
    for it in S.rf:
        bruto, rend, ir = valor_rf(it)
        rf_lin.append({**it, "bruto": bruto, "rend": rend, "ir": ir, "liquido": bruto - ir})
    por_classe = {c: 0.0 for c in CLASSES}
    for p in rv:
        por_classe[p["classe"]] = por_classe.get(p["classe"], 0) + p["atual"]
    por_classe["Renda fixa"] += sum(x["bruto"] for x in rf_lin)
    total = sum(por_classe.values())
    investido = sum(p["custo"] for p in rv) + sum(float(x["valor"]) for x in rf_lin)
    proventos = sum(float(x["valor"]) for x in S.proventos)
    realizado = sum(p["realizado"] for p in posicoes_rv())
    lucro = total - investido + proventos + realizado
    datas = [o["data"] for o in S.ops] + [x["data"] for x in S.rf]
    inicio = min(datas) if datas else None
    rent = (lucro / investido * 100) if investido else 0.0
    cdi_periodo = (cdi_acumulado(inicio) - 1) * 100 if inicio else 0.0
    dias = (HOJE - datetime.fromisoformat(inicio).date()).days if inicio else 0
    return {"rv": rv, "rf": rf_lin, "por_classe": por_classe, "total": total, "investido": investido,
            "proventos": proventos, "realizado": realizado, "lucro": lucro, "rent": rent,
            "cdi_periodo": cdi_periodo, "inicio": inicio, "dias": dias}


def alocacao_pct(r):
    tot = r["total"] or 1
    return {c: r["por_classe"].get(c, 0) / tot * 100 for c in CLASSES}


def taxa_real_usada():
    if S.premissas.get("taxa_real"):
        return float(S.premissas["taxa_real"])
    return TAXA_REAL_PADRAO.get(S.perfil or "Moderado", 5.0)


def aporte_necessario(alvo, atual, anos, taxa_aa):
    """Aporte mensal para sair de 'atual' e chegar em 'alvo' em 'anos', com taxa anual real."""
    n = max(int(round(anos * 12)), 1)
    i = (1 + taxa_aa / 100) ** (1 / 12) - 1
    fv_atual = atual * (1 + i) ** n
    falta = alvo - fv_atual
    if falta <= 0:
        return 0.0
    return falta * i / ((1 + i) ** n - 1) if i > 0 else falta / n


def meses_ate(alvo, atual, aporte, taxa_aa, limite=1200):
    i = (1 + taxa_aa / 100) ** (1 / 12) - 1
    v, m = atual, 0
    while v < alvo and m < limite:
        v = v * (1 + i) + aporte
        m += 1
    return m if v >= alvo else None


def rent_anual_real(r):
    """Rentabilidade anualizada observada, descontada a inflação (estimativa do app)."""
    if not r["investido"] or r["dias"] < 60:
        return None
    anos = r["dias"] / 365
    nominal = (1 + r["rent"] / 100) ** (1 / anos) - 1
    return ((1 + nominal) / (1 + S.premissas["ipca"] / 100) - 1) * 100


# ══════════════════════════════════════════════════════════════════════════
# PENTE FINO (regras do app)
# ══════════════════════════════════════════════════════════════════════════
def pente_fino():
    r = resumo_carteira()
    achados, pontos = [], 100
    fin = S.financas
    gastos = float(fin.get("gastos") or 0)
    reserva = float(fin.get("reserva") or 0)

    def add(nivel, titulo, texto, peso=0):
        nonlocal pontos
        achados.append({"nivel": nivel, "titulo": titulo, "texto": texto})
        pontos -= peso

    if fin.get("dividas_caras"):
        add("critico", "Dívida cara em aberto", "Você marcou que tem dívida de cartão ou cheque especial. Quitar essa dívida rende mais do que qualquer investimento seguro.", 20)
    if gastos > 0:
        meses = reserva / gastos
        if meses < 3:
            add("critico", "Reserva de emergência baixa", f"Sua reserva cobre {num(meses,1)} meses de gastos. O recomendado é de 6 a 12 meses antes de aumentar a renda variável.", 20)
        elif meses < 6:
            add("alerta", "Reserva de emergência incompleta", f"A reserva cobre {num(meses,1)} meses. Falta pouco para chegar a 6 meses ({brl(6*gastos - reserva)}).", 10)
        else:
            add("ok", "Reserva de emergência em dia", f"A reserva cobre {num(meses,1)} meses de gastos.")
    else:
        add("info", "Complete seus dados financeiros", "Informe gastos mensais e reserva em 🧭 Meu Perfil para o app avaliar sua reserva.", 5)

    if r["total"] <= 0:
        add("info", "Carteira vazia", "Registre seus investimentos em 💼 Carteira para o pente fino analisar a alocação.", 0)
        return {"pontos": max(pontos, 0), "achados": achados, "resumo": r}

    aloc = alocacao_pct(r)
    alvo = ALVOS.get(S.perfil or "Moderado")
    for c in CLASSES:
        dif = aloc[c] - alvo[c]
        if abs(dif) > 15:
            add("alerta", f"{c} longe do alvo", f"{c}: {num(aloc[c],1)}% da carteira, alvo do perfil {S.perfil or 'Moderado'} é {alvo[c]}%. Use os próximos aportes para se aproximar do alvo.", 8)
        elif abs(dif) > 8:
            add("info", f"{c} um pouco fora do alvo", f"{c}: {num(aloc[c],1)}% (alvo {alvo[c]}%).", 3)

    for p in r["rv"]:
        part = p["atual"] / r["total"] * 100
        if part > 35:
            add("critico", f"Concentração alta em {p['ticker']}", f"{p['ticker']} é {num(part,1)}% de toda a carteira. Se ele cair, boa parte do seu patrimônio sofre junto.", 15)
        elif part > 20:
            add("alerta", f"{p['ticker']} pesa muito", f"{p['ticker']} é {num(part,1)}% da carteira. Uma referência comum é cada ativo ficar abaixo de 10% a 20%.", 7)

    n_acoes = len([p for p in r["rv"] if p["classe"] == "Ações"])
    n_fiis = len([p for p in r["rv"] if p["classe"] == "FIIs"])
    if aloc["Ações"] > 10 and n_acoes < 5:
        add("alerta", "Poucas ações na carteira", f"Você tem {n_acoes} ação(ões) e {num(aloc['Ações'],1)}% em ações. Com poucas empresas, o risco de uma delas pesa muito. Estude diversificação por setores.", 6)
    if aloc["FIIs"] > 5 and n_fiis < 3:
        add("info", "Poucos FIIs", f"Você tem {n_fiis} FII(s). Diversificar entre tipos (tijolo, papel, logística, lajes) reduz o risco de vacância de um fundo só.", 3)
    if aloc["Cripto"] > 10:
        add("alerta", "Cripto acima de 10%", f"Cripto é {num(aloc['Cripto'],1)}% da carteira. É uma classe muito volátil; costuma ficar entre 0% e 5% do patrimônio.", 8)

    for p in r["rv"]:
        if p["tem_cotacao"] and p["rent"] < -30:
            add("alerta", f"{p['ticker']} caiu {num(abs(p['rent']),0)}%", "Revise a tese: o que mudou na empresa ou no fundo? A queda veio do mercado todo ou só desse ativo? Decida com base em fundamentos, não no susto.", 4)
    rk = risco_agora(r)
    for t, v in rk["quedas"]:
        add("alerta" if v <= -5 else "info", f"{t} caindo {num(abs(v),1)}% hoje",
            "Queda forte no dia. Veja se há notícia (aba 💬 Mentor → 📰 Notícias e riscos agora) antes de qualquer decisão.", 3 if v <= -5 else 0)
    for t, v in rk["volateis"]:
        add("info", f"{t} oscila muito", f"Volatilidade de {num(v,0)}% ao ano nos últimos 30 pregões. Ativos assim pedem posição menor.", 2)
    sem_cot = [p["ticker"] for p in r["rv"] if not p["tem_cotacao"]]
    if sem_cot:
        add("info", "Ativos sem cotação", "Sem preço atualizado: " + ", ".join(sem_cot) + ". Atualize as cotações em 💼 Carteira para a análise ficar precisa.", 2)

    if r["dias"] >= 90 and r["investido"]:
        if r["rent"] < r["cdi_periodo"] - 2:
            add("info", "Abaixo do CDI no período", f"Sua carteira rendeu {pct(r['rent'])} desde {br_data(r['inicio'])}; o CDI rendeu {pct(r['cdi_periodo'])}. Em renda variável isso pode acontecer em períodos curtos — avalie no longo prazo.", 0)
        else:
            add("ok", "Rendimento acima ou próximo do CDI", f"Carteira {pct(r['rent'])} x CDI {pct(r['cdi_periodo'])} desde {br_data(r['inicio'])}.")

    feitos = {k for k, v in S.modulos.items() if v.get("aprovado")}
    if aloc["Ações"] > 0 and "m8" not in feitos:
        add("info", "Estude antes de aumentar ações", "Você já tem ações, mas ainda não passou no módulo 'Ações: o que analisar'. Faça esse módulo na 🎓 Trilha.", 3)
    if aloc["FIIs"] > 0 and "m9" not in feitos:
        add("info", "Estude FIIs", "Você tem FIIs, mas ainda não passou no módulo de Fundos imobiliários.", 2)

    ult = [a for a in S.aportes if a["data"] >= (HOJE - timedelta(days=95)).isoformat()]
    meses_com = len({a["data"][:7] for a in ult})
    if S.ops or S.rf:
        if meses_com >= 3:
            add("ok", "Aportes em dia", "Você aportou nos últimos 3 meses. Constância é o que mais faz a carteira crescer.")
        elif meses_com == 0:
            add("alerta", "Sem aportes recentes", "Nenhum aporte registrado nos últimos 3 meses. Mesmo valores pequenos mantêm o hábito.", 6)
        else:
            add("info", "Aportes irregulares", f"Aportes em {meses_com} dos últimos 3 meses.", 2)
    return {"pontos": max(min(pontos, 100), 0), "achados": achados, "resumo": r, "risco": rk}


def contexto_aluno():
    r = resumo_carteira()
    aloc = alocacao_pct(r) if r["total"] else {}
    feitos = [MOD[k][2] for k, v in S.modulos.items() if v.get("aprovado") and k in MOD]
    linhas = [
        f"Nome: {S.i_nome}. Perfil: {S.perfil or 'não definido'}. Nível: {nivel_atual()[0]} ({S.xp} XP).",
        f"Renda mensal: {brl(S.financas.get('renda'))}; gastos: {brl(S.financas.get('gastos'))}; reserva: {brl(S.financas.get('reserva'))}; aporte planejado: {brl(S.financas.get('aporte_plano'))}/mês; dívida cara: {'sim' if S.financas.get('dividas_caras') else 'não'}.",
        f"Patrimônio investido: {brl(r['total'])}; aplicado: {brl(r['investido'])}; resultado total: {brl(r['lucro'])} ({pct(r['rent'])}); CDI no mesmo período: {pct(r['cdi_periodo'])}.",
        "Alocação atual: " + (", ".join(f"{c} {num(v,1)}%" for c, v in aloc.items()) if aloc else "sem investimentos registrados") + ".",
        "Alvo do perfil: " + ", ".join(f"{c} {v}%" for c, v in ALVOS.get(S.perfil or "Moderado").items()) + ".",
        "Ativos: " + (", ".join(f"{p['ticker']} ({p['classe']}, {num(p['atual']/r['total']*100 if r['total'] else 0,1)}%, {pct(p['rent'])})" for p in r["rv"]) or "nenhum") + ".",
        "Renda fixa: " + (", ".join(f"{x['produto']} {x['tipo']} {num(x.get('taxa',0),2)}" for x in r["rf"]) or "nenhuma") + ".",
        "Metas: " + (", ".join(f"{m['nome']} {brl(m['valor'])} até {br_data(m['prazo'])}" for m in S.metas) or "nenhuma") + ".",
        "Módulos aprovados: " + (", ".join(feitos) or "nenhum") + ".",
        f"Indicadores usados: CDI {num(S.premissas['cdi'])}% a.a., Selic {num(S.premissas['selic'])}% a.a., IPCA 12m {num(S.premissas['ipca'])}%.",
    ]
    if r["rv"]:
        rk = risco_agora(r)
        linhas.append(f"Agora ({S.ultima_atualizacao.strftime('%d/%m %H:%M') if S.ultima_atualizacao else 'sem atualização'}): carteira {pct(rk['var_dia'],2)} hoje; "
                      f"volatilidade média {num(rk['vol'],0)}% a.a.; perda estimada num dia ruim (95%) até {brl(rk['perda_dia'])}. "
                      + "Mercado: " + (", ".join(f"{k} {pct(v.get('var_dia'),2)}" for k, v in S.mercado.items()) or "sem dados") + ".")
    if S.revisoes:
        u = S.revisoes[-1]
        linhas.append(f"Último pente fino ({br_data(u['data'])}): nota {u['pontos']}/100.")
    return "\n".join(linhas)


# ══════════════════════════════════════════════════════════════════════════
# NÍVEL
# ══════════════════════════════════════════════════════════════════════════
def niveis_trilha_concluidos():
    feitos = {k for k, v in S.modulos.items() if v.get("aprovado")}
    n = 0
    for nv in sorted(NIVEIS_TRILHA):
        ids = [m[0] for m in MODULOS if m[1] == nv]
        if all(i in feitos for i in ids):
            n = nv
        else:
            break
    return n


def nivel_atual():
    concl = niveis_trilha_concluidos()
    atual = NIVEIS_INV[0]
    for nv in NIVEIS_INV:
        nome, xp_min, req = nv
        if S.xp >= xp_min and concl >= req:
            if nome.endswith("Fera"):
                boas = [x for x in S.revisoes if x["pontos"] >= 80]
                if len(boas) < 3:
                    continue
            atual = nv
    idx = NIVEIS_INV.index(atual)
    prox = NIVEIS_INV[idx + 1] if idx + 1 < len(NIVEIS_INV) else None
    return atual[0], atual, prox


def requisitos_proximo(prox):
    if not prox:
        return []
    nome, xp_min, req = prox
    falta = []
    if S.xp < xp_min:
        falta.append(f"{xp_min - S.xp} XP")
    if niveis_trilha_concluidos() < req:
        falta.append(f"concluir o nível {req} da trilha ({NIVEIS_TRILHA[req]})")
    if nome.endswith("Fera"):
        boas = len([x for x in S.revisoes if x["pontos"] >= 80])
        if boas < 3:
            falta.append(f"{3 - boas} pente(s) fino(s) com nota 80 ou mais")
    return falta


def proximo_passo():
    if not S.perfil:
        return "Responda o questionário em 🧭 Meu Perfil para descobrir seu perfil de investidor."
    feitos = {k for k, v in S.modulos.items() if v.get("aprovado")}
    for m in MODULOS:
        if m[0] not in feitos:
            return f"Estude o módulo **{m[2]}** na 🎓 Trilha e faça a prova."
    if not (S.ops or S.rf):
        return "Registre seus investimentos em 💼 Carteira."
    if not S.revisoes or S.revisoes[-1]["data"] < (HOJE - timedelta(days=30)).isoformat():
        return "Faça o 🔍 Pente fino do mês."
    return "Mantenha os aportes e faça o pente fino todo mês."


# ══════════════════════════════════════════════════════════════════════════
# MEMÓRIA (.json)
# ══════════════════════════════════════════════════════════════════════════
def memoria_json():
    d = {k: S[k] for k in CHAVES_MEMORIA}
    d["_app"] = "investidor_fera"
    d["_salvo_em"] = datetime.now().isoformat(timespec="seconds")
    return json.dumps(d, ensure_ascii=False, indent=2).encode("utf-8")


# ══════════════════════════════════════════════════════════════════════════
# TELA DE ENTRADA
# ══════════════════════════════════════════════════════════════════════════
if not S.i_chave:
    _, meio, _ = st.columns([1, 2, 1])
    with meio:
        st.markdown("""<div style="text-align:center;padding:18px 0 4px 0;">
          <div style="font-size:3.2em;">📈</div><h1 style="margin:0;">Investidor Fera</h1>
          <p style="color:#4B6358 !important;">Aprenda a investir do zero, acompanhe sua carteira e receba um pente fino até virar fera.</p>
        </div>""", unsafe_allow_html=True)
        nome = st.text_input("👤 Seu nome", placeholder="Como quer ser chamado?", key="i_inp_nome")
        chave = st.text_input("🔑 Sua chave Groq API", type="password", placeholder="gsk_...", key="i_inp_chave")
        if st.button("✨ ENTRAR", type="primary", width="stretch"):
            if len(nome.strip()) < 2:
                st.warning("Digite um nome com pelo menos 2 letras.")
            elif not chave.strip().startswith("gsk_"):
                st.warning("A chave Groq começa com **gsk_**. Confira e cole novamente.")
            else:
                S.i_nome, S.i_chave = nome.strip(), chave.strip()
                st.rerun()
        st.markdown(f"""<div class="card" style="font-size:.92em;line-height:1.7;">
        🔑 <b>Não tem chave?</b> Crie grátis em <a href="https://console.groq.com/keys" target="_blank">console.groq.com/keys</a>
        (entre com Google, clique em <b>Create API Key</b> e copie).<br>
        🔒 Sua chave fica só nesta sessão do navegador.<br>
        💾 Já usa o app? Depois de entrar, abra sua memória salva em <b>💾 Minha memória</b>.<br>
        🤖 Mais agentes em <a href="{SITE}" target="_blank">MeusAgentesIA.com.br</a>.</div>""", unsafe_allow_html=True)
        st.markdown('<p class="aviso-cvm">Conteúdo educativo. O app não faz recomendação individual de investimentos. '
                    'Rentabilidade passada não garante rentabilidade futura.</p>', unsafe_allow_html=True)
    st.stop()


# ══════════════════════════════════════════════════════════════════════════
# CABEÇALHO + MEMÓRIA
# ══════════════════════════════════════════════════════════════════════════
if S.indicadores is None:
    atualizar_indicadores()
if S.ultima_atualizacao is None:
    atualizar_tudo()

nome_nivel, _, prox = nivel_atual()
c_cab, c_mem = st.columns([3, 2])
with c_cab:
    st.markdown(f"""<div class="cab"><h1>📈 Investidor Fera</h1>
    <p>Olá, {S.i_nome}! <span class="nivel">{nome_nivel}</span> &nbsp;{S.xp} XP · Perfil: {S.perfil or 'a definir'}</p></div>""",
                unsafe_allow_html=True)
with c_mem:
    with st.expander("💾 Minha memória: salvar, abrir, recomeçar ou sair"):
        st.caption("Os dados ficam só nesta sessão. Salve o arquivo .json no seu aparelho e abra na próxima visita.")
        st.download_button("💾 Salvar minha memória (.json)", data=memoria_json(),
                           file_name=f"investidor_fera_{re.sub(r'[^a-z0-9]+', '_', S.i_nome.lower())}_{HOJE.isoformat()}.json",
                           mime="application/json", width="stretch")
        arq = st.file_uploader("📂 Abrir minha memória", type=["json"], key=f"up_mem_{S.ver}")
        if arq is not None and st.button("Carregar esta memória", width="stretch"):
            try:
                dados = json.loads(arq.getvalue().decode("utf-8"))
                if dados.get("_app") != "investidor_fera":
                    raise ValueError
                for k in CHAVES_MEMORIA:
                    if k in dados:
                        S[k] = dados[k]
                S.ver += 1
                st.success("Memória carregada!")
                st.rerun()
            except Exception:
                st.error("Esse arquivo não é uma memória do Investidor Fera.")
        st.divider()
        if not S.get("_conf_reset"):
            if st.button("🆕 Recomeçar do zero", width="stretch"):
                S["_conf_reset"] = True
                st.rerun()
        else:
            st.warning("Isso apaga perfil, carteira, trilha e histórico desta tela. **Salve a memória antes** se quiser guardar.")
            r1, r2 = st.columns(2)
            if r1.button("✅ Sim, apagar", width="stretch"):
                chave, nome = S.i_chave, S.i_nome
                for k in list(S.keys()):
                    del S[k]
                S.i_chave, S.i_nome = chave, nome
                st.rerun()
            if r2.button("Cancelar", width="stretch"):
                S["_conf_reset"] = False
                st.rerun()
        if st.button("🚪 Sair", width="stretch"):
            for k in list(S.keys()):
                del S[k]
            st.rerun()

abas = st.tabs(["🏠 Painel", "🧭 Meu Perfil", "🎓 Trilha", "💼 Carteira", "🔍 Pente fino", "🎯 Metas",
                "🧮 Simuladores", "🏆 Nível", "💬 Mentor", "📘 Guia"])


def mostrar_erro(e):
    st.error(f"⚠️ {e}")


# ══════════════════════════════════════════════════════════════════════════
# 1. PAINEL
# ══════════════════════════════════════════════════════════════════════════
@st.fragment(run_every=60)
def ao_vivo():
    """Atualiza cotações e risco sozinho, no intervalo escolhido, sem recarregar a página toda."""
    if S.auto_min and S.ultima_atualizacao and (datetime.now() - S.ultima_atualizacao).total_seconds() >= S.auto_min * 60 - 5:
        atualizar_tudo()
    r = resumo_carteira()
    st.markdown("#### 📡 Ao vivo")
    cm = st.columns(len(MERCADO) + 1)
    for (nome, q), col in zip([(n, S.mercado.get(n)) for n in MERCADO], cm):
        if q:
            v = q.get("var_dia")
            col.markdown(f'<div class="kpi"><div class="l">{nome}</div><div class="v">{num(q["preco"], 0 if nome != "Dólar" else 3)}</div>'
                         f'<div class="{"pos" if (v or 0) >= 0 else "neg"}">{pct(v,2)}</div></div>', unsafe_allow_html=True)
        else:
            col.markdown(f'<div class="kpi"><div class="l">{nome}</div><div class="v">—</div></div>', unsafe_allow_html=True)
    if r["rv"]:
        rk = risco_agora(r)
        cls = "pos" if rk["var_dia"] >= 0 else "neg"
        cm[-1].markdown(f'<div class="kpi"><div class="l">Sua carteira hoje</div><div class="v {cls}">{pct(rk["var_dia"],2)}</div>'
                        f'<div class="{cls}">{brl(rk["ganho_dia"])}</div></div>', unsafe_allow_html=True)
        alertas = [f"🔻 {t} {pct(v,1)} hoje" for t, v in rk["quedas"]]
        st.markdown(f'<div class="card">⚠️ <b>Risco agora:</b> num dia ruim (1 em 20), a parte em renda variável pode perder até '
                    f'<b>{brl(rk["perda_dia"])}</b> · oscilação média dos ativos: <b>{num(rk["vol"],0)}% ao ano</b>'
                    + ("<br>" + " · ".join(alertas) if alertas else "") + '</div>', unsafe_allow_html=True)
    quando = S.ultima_atualizacao.strftime("%H:%M:%S") if S.ultima_atualizacao else "—"
    st.caption(f"Atualizado às {quando}" + (f" · próxima atualização automática em até {S.auto_min} min" if S.auto_min else " · atualização automática desligada")
               + ". Cotações gratuitas da B3 têm atraso de cerca de 15 minutos.")


with abas[0]:
    r = resumo_carteira()
    t1, t2 = st.columns([3, 1])
    with t2:
        escolha = st.selectbox("Atualização automática", ["A cada 1 min", "A cada 5 min", "A cada 15 min", "Desligada"],
                               index={1: 0, 5: 1, 15: 2, 0: 3}.get(S.auto_min, 1), key="auto_sel")
        S.auto_min = {"A cada 1 min": 1, "A cada 5 min": 5, "A cada 15 min": 15, "Desligada": 0}[escolha]
        if st.button("🔄 Atualizar agora", width="stretch"):
            atualizar_tudo()
            st.rerun()
    with t1:
        ao_vivo()
    k1, k2, k3, k4 = st.columns(4)
    cls = "pos" if r["lucro"] >= 0 else "neg"
    k1.markdown(f'<div class="kpi"><div class="l">Patrimônio</div><div class="v">{brl(r["total"])}</div></div>', unsafe_allow_html=True)
    k2.markdown(f'<div class="kpi"><div class="l">Resultado total</div><div class="v {cls}">{brl(r["lucro"])}</div></div>', unsafe_allow_html=True)
    k3.markdown(f'<div class="kpi"><div class="l">Rentabilidade</div><div class="v {cls}">{pct(r["rent"])}</div></div>', unsafe_allow_html=True)
    k4.markdown(f'<div class="kpi"><div class="l">CDI no período</div><div class="v">{pct(r["cdi_periodo"])}</div></div>', unsafe_allow_html=True)
    st.write("")
    a, b = st.columns([3, 2])
    with a:
        st.markdown("#### 👣 Seu próximo passo")
        st.info(proximo_passo())
        if r["total"] > 0:
            st.markdown("#### 🧩 Alocação: atual x alvo do perfil")
            aloc = alocacao_pct(r)
            alvo = ALVOS.get(S.perfil or "Moderado")
            df = pd.DataFrame([{"Classe": c, "Tipo": "Atual", "%": round(aloc[c], 1)} for c in CLASSES] +
                              [{"Classe": c, "Tipo": "Alvo", "%": alvo[c]} for c in CLASSES])
            ch = alt.Chart(df).mark_bar(cornerRadiusEnd=4).encode(
                y=alt.Y("Classe:N", title=None, sort=CLASSES), x=alt.X("%:Q", title="% da carteira"),
                color=alt.Color("Tipo:N", scale=alt.Scale(domain=["Atual", "Alvo"], range=["#0F5132", "#A7D7BF"]), title=None),
                yOffset="Tipo:N", tooltip=["Classe", "Tipo", "%"]).properties(height=260)
            st.altair_chart(ch, width="stretch")
        else:
            st.markdown('<div class="card">💼 Quando você registrar seus investimentos, aqui aparecem a alocação, '
                        'a rentabilidade e a comparação com o CDI.</div>', unsafe_allow_html=True)
    with b:
        st.markdown("#### 🏆 Sua evolução")
        nome_nivel, _, prox = nivel_atual()
        st.markdown(f'<div class="card"><span class="nivel">{nome_nivel}</span> &nbsp;<b>{S.xp} XP</b><br>'
                    + (f'Próximo: <b>{prox[0]}</b> — falta: {", ".join(requisitos_proximo(prox)) or "nada! atualize a página"}' if prox else "Você chegou ao topo! 🦁")
                    + '</div>', unsafe_allow_html=True)
        feitos = len([1 for v in S.modulos.values() if v.get("aprovado")])
        st.progress(feitos / len(MODULOS), text=f"Trilha: {feitos} de {len(MODULOS)} módulos")
        if S.revisoes:
            u = S.revisoes[-1]
            st.markdown(f'<div class="card">🔍 Último pente fino: <b>{u["pontos"]}/100</b> em {br_data(u["data"])}</div>', unsafe_allow_html=True)
        st.markdown("#### 📊 Indicadores")
        st.markdown(f'<div class="card">CDI: <b>{num(S.premissas["cdi"])}% a.a.</b> · Selic: <b>{num(S.premissas["selic"])}% a.a.</b><br>'
                    f'IPCA 12 meses: <b>{num(S.premissas["ipca"])}%</b><br><span style="font-size:.8em;color:#4B6358;">'
                    + (f'Banco Central, {S.indicadores["quando"]}' if S.indicadores and S.indicadores.get("ok") else
                       "Valores de referência (não consegui falar com o Banco Central agora). Ajuste em 🧮 Simuladores → Premissas.")
                    + '</span></div>', unsafe_allow_html=True)
    st.markdown('<p class="aviso-cvm">Conteúdo educativo. O app não faz recomendação individual de investimentos. '
                'Rentabilidade passada não garante rentabilidade futura.</p>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# 2. MEU PERFIL
# ══════════════════════════════════════════════════════════════════════════
with abas[1]:
    st.markdown("### 🧭 Meu perfil de investidor")
    st.caption("Responda com sinceridade. O app calcula seu perfil e define a alocação-alvo da sua carteira.")
    with st.form(f"f_perfil_{S.ver}"):
        resp = {}
        for i, (perg, opcoes) in enumerate(PERGUNTAS_PERFIL):
            rotulos = [o[0] for o in opcoes]
            atual = S.respostas_perfil.get(str(i))
            resp[str(i)] = st.radio(f"**{i+1}. {perg}**", rotulos, index=rotulos.index(atual) if atual in rotulos else None, key=f"pp_{i}_{S.ver}")
        st.markdown("**💰 Sua situação financeira**")
        f1, f2, f3 = st.columns(3)
        renda = f1.number_input("Renda mensal (R$)", min_value=0.0, step=100.0, value=float(S.financas.get("renda") or 0))
        gastos = f2.number_input("Gastos mensais (R$)", min_value=0.0, step=100.0, value=float(S.financas.get("gastos") or 0))
        reserva = f3.number_input("Reserva de emergência hoje (R$)", min_value=0.0, step=100.0, value=float(S.financas.get("reserva") or 0))
        g1, g2 = st.columns(2)
        aporte = g1.number_input("Quanto pretende investir por mês (R$)", min_value=0.0, step=50.0, value=float(S.financas.get("aporte_plano") or 0))
        dividas = g2.checkbox("Tenho dívida de cartão de crédito ou cheque especial", value=bool(S.financas.get("dividas_caras")))
        enviar = st.form_submit_button("🧭 CALCULAR MEU PERFIL", width="stretch")
    if enviar:
        if any(v is None for v in resp.values()):
            st.warning("Responda todas as perguntas.")
        else:
            pts = sum(dict(PERGUNTAS_PERFIL[int(i)][1])[v] for i, v in resp.items())
            perfil = "Conservador" if pts <= 6 else ("Moderado" if pts <= 12 else "Arrojado")
            if dividas or (gastos > 0 and reserva < 3 * gastos):
                if perfil == "Arrojado":
                    perfil = "Moderado"
            S.respostas_perfil, S.perfil = resp, perfil
            S.financas = {"renda": renda, "gastos": gastos, "reserva": reserva, "aporte_plano": aporte, "dividas_caras": dividas}
            ganhar_xp(50, "Perfil de investidor definido", unico="perfil")
            S["_perfil_msg"] = pts
            st.rerun()
    if S.perfil:
        alvo = ALVOS[S.perfil]
        st.success(f"Seu perfil: **{S.perfil}**" + (f" ({S.get('_perfil_msg')} de 18 pontos)" if S.get("_perfil_msg") is not None else ""))
        if S.financas.get("dividas_caras") or (S.financas.get("gastos") and S.financas.get("reserva", 0) < 3 * S.financas["gastos"]):
            st.warning("Enquanto houver dívida cara ou reserva menor que 3 meses de gastos, o app limita seu perfil a no máximo **Moderado**. Priorize a reserva.")
        cols = st.columns(len(CLASSES))
        for c, col in zip(CLASSES, cols):
            col.markdown(f'<div class="kpi"><div class="l">{c}</div><div class="v">{alvo[c]}%</div></div>', unsafe_allow_html=True)
        st.caption("Essa é uma alocação de referência para estudo. Você pode adaptá-la ao seu momento; o pente fino compara sua carteira com ela.")
        if st.button("🤖 Explicar meu perfil e por onde começar", width="stretch"):
            with st.spinner("O mentor está analisando…"):
                try:
                    S["_explica_perfil"] = ia_texto("Explique meu perfil de investidor, o que a alocação-alvo significa e quais os 3 primeiros passos práticos que devo dar, considerando minha reserva, dívidas e aporte mensal. Seja breve.")
                except RuntimeError as e:
                    mostrar_erro(e)
        if S.get("_explica_perfil"):
            st.markdown(f'<div class="card">{S["_explica_perfil"]}</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# 3. TRILHA
# ══════════════════════════════════════════════════════════════════════════
def gerar_prova(mid):
    _, nv, titulo, pontos, reserva = MOD[mid]
    try:
        d = ia_json(
            f"Crie uma prova com 5 questões de múltipla escolha (4 alternativas) sobre '{titulo}', nível "
            f"{NIVEIS_TRILHA[nv]}, para um investidor brasileiro iniciante. Baseie-se nestes pontos: {' | '.join(limpar_md(p) for p in pontos)}. "
            "Questões práticas, com situações do dia a dia, sem pegadinhas e com só UMA alternativa correta. "
            'Formato: {"questoes":[{"pergunta":"...","opcoes":["a","b","c","d"],"correta":0,"explicacao":"..."}]}', max_tokens=2200)
        qs = []
        for q in d.get("questoes", [])[:5]:
            ops = [str(o) for o in q.get("opcoes", [])][:4]
            c = int(q.get("correta", -1))
            if len(ops) == 4 and 0 <= c < 4 and q.get("pergunta"):
                qs.append((str(q["pergunta"]), ops, c, str(q.get("explicacao", ""))))
        if len(qs) >= 3:
            return qs, "IA"
    except Exception:
        pass
    return list(reserva), "reserva"


with abas[2]:
    st.markdown("### 🎓 Trilha do investidor")
    st.caption("Estude cada módulo e faça a prova. Acertando 80% ou mais, o módulo é aprovado e o próximo é liberado.")
    feitos = {k for k, v in S.modulos.items() if v.get("aprovado")}
    liberado_ate = 0
    for i, m in enumerate(MODULOS):
        if i == 0 or MODULOS[i - 1][0] in feitos:
            liberado_ate = i
        else:
            break
    for nv, nome_nv in NIVEIS_TRILHA.items():
        mods = [m for m in MODULOS if m[1] == nv]
        ok_nv = len([m for m in mods if m[0] in feitos])
        st.markdown(f"#### {nome_nv} · {ok_nv}/{len(mods)}")
        for m in mods:
            mid, _, titulo, pontos, _ = m
            idx = MODULOS.index(m)
            info = S.modulos.get(mid, {})
            if mid in feitos:
                rot = f"✅ {titulo} — nota {info.get('nota', 0)}%"
            elif idx <= liberado_ate:
                rot = f"📖 {titulo}"
            else:
                rot = f"🔒 {titulo}"
            with st.expander(rot, expanded=(idx == liberado_ate and mid not in feitos and S.quiz is None)):
                if idx > liberado_ate:
                    st.info("Conclua o módulo anterior para liberar este.")
                    continue
                st.markdown("**Pontos-chave**")
                for p in pontos:
                    st.markdown(f"- {p}")
                c1, c2 = st.columns(2)
                if c1.button("📖 Aula completa com a IA", key=f"aula_{mid}", width="stretch"):
                    with st.spinner("Preparando a aula…"):
                        try:
                            S.aulas[mid] = ia_texto(
                                f"Dê uma aula completa e didática sobre '{titulo}' para o meu nível e perfil. Use estes pontos "
                                f"como base: {' | '.join(limpar_md(p) for p in pontos)}. Inclua: explicação simples, um exemplo com "
                                "números em reais, erros comuns e um mini exercício no final (com a resposta). Até 500 palavras.",
                                max_tokens=2200)
                            ganhar_xp(10, f"Aula: {titulo}", unico=f"aula_{mid}")
                        except RuntimeError as e:
                            mostrar_erro(e)
                if c2.button("📝 Fazer a prova", key=f"prova_{mid}", width="stretch"):
                    with st.spinner("Montando a prova…"):
                        qs, origem = gerar_prova(mid)
                    S.quiz = {"mid": mid, "qs": qs, "origem": origem, "resp": None}
                    st.rerun()
                if S.aulas.get(mid):
                    st.markdown(f'<div class="card">{S.aulas[mid]}</div>', unsafe_allow_html=True)
                if S.quiz and S.quiz["mid"] == mid:
                    qz = S.quiz
                    st.markdown("---")
                    st.markdown(f"**📝 Prova — {titulo}**" + (" · *perguntas fixas do app*" if qz["origem"] == "reserva" else ""))
                    if qz["resp"] is None:
                        with st.form(f"f_quiz_{mid}"):
                            escolhas = []
                            for j, (perg, ops, _, _) in enumerate(qz["qs"]):
                                escolhas.append(st.radio(f"**{j+1}. {perg}**", ops, index=None, key=f"q_{mid}_{j}"))
                            entregar = st.form_submit_button("✅ Entregar prova", width="stretch")
                        if entregar:
                            if any(e is None for e in escolhas):
                                st.warning("Responda todas as questões.")
                            else:
                                acertos = sum(1 for (perg, ops, c, _), e in zip(qz["qs"], escolhas) if ops.index(e) == c)
                                nota = round(acertos / len(qz["qs"]) * 100)
                                qz["resp"] = {"escolhas": escolhas, "nota": nota}
                                ant = S.modulos.get(mid, {})
                                aprovado = nota >= 80
                                S.modulos[mid] = {"nota": max(nota, ant.get("nota", 0)), "aprovado": ant.get("aprovado") or aprovado,
                                                  "data": HOJE.isoformat(), "tentativas": ant.get("tentativas", 0) + 1}
                                if aprovado:
                                    ganhar_xp(100, f"Módulo aprovado: {titulo}", unico=f"mod_{mid}")
                                    if nota == 100:
                                        ganhar_xp(50, f"Nota 100: {titulo}", unico=f"mod100_{mid}")
                                st.rerun()
                    else:
                        nota = qz["resp"]["nota"]
                        if nota >= 80:
                            st.success(f"🎉 Aprovado com {nota}%! +100 XP" + (" e +50 XP pela nota máxima" if nota == 100 else ""))
                        else:
                            st.error(f"Nota {nota}%. Você precisa de 80% para passar. Revise os pontos-chave e tente de novo.")
                        for j, ((perg, ops, c, expl), e) in enumerate(zip(qz["qs"], qz["resp"]["escolhas"])):
                            certo = ops.index(e) == c
                            st.markdown(f"{'✅' if certo else '❌'} **{j+1}. {perg}**  \nSua resposta: {e}"
                                        + ("" if certo else f"  \nCorreta: **{ops[c]}**") + (f"  \n_{expl}_" if expl else ""))
                        if st.button("Fechar prova", key=f"fechar_{mid}"):
                            S.quiz = None
                            st.rerun()


# ══════════════════════════════════════════════════════════════════════════
# 4. CARTEIRA
# ══════════════════════════════════════════════════════════════════════════
with abas[3]:
    st.markdown("### 💼 Minha carteira")
    sub = st.tabs(["📋 Posição", "➕ Ações, FIIs, ETFs, cripto", "🏦 Renda fixa", "💵 Proventos", "📅 Aportes"])

    with sub[0]:
        r = resumo_carteira()
        if r["total"] <= 0:
            st.info("Sua carteira está vazia. Registre suas compras nas abas ao lado.")
        else:
            cA, cB = st.columns([1, 3])
            with cA:
                if st.button("🔄 Atualizar cotações", width="stretch"):
                    with st.spinner("Buscando cotações…"):
                        falha = atualizar_tudo()
                    S["_cot_msg"] = (len(r["rv"]) - len(falha), falha)
                    st.rerun()
            with cB:
                if S.get("_cot_msg"):
                    ok, falha = S["_cot_msg"]
                    msg = f"{ok} cotação(ões) atualizada(s)."
                    if falha:
                        msg += f" Não encontrei: {', '.join(falha)} — confira o código ou informe o preço à mão em ✏️ Preço manual."
                    st.caption(msg)
                else:
                    st.caption("Cotações do Yahoo Finance (atraso de cerca de 15 min), atualizadas sozinhas pelo 📡 Ao vivo do Painel. Ativo sem cotação usa o preço médio.")
            if r["rv"]:
                st.markdown("**Renda variável**")
                tab = pd.DataFrame([{
                    "Ativo": p["ticker"], "Classe": p["classe"], "Qtd": p["qtd"], "Preço médio": p["pm"],
                    "Preço atual": p["preco"], "Hoje %": S.precos.get(p["ticker"], {}).get("var_dia"),
                    "Valor atual": p["atual"], "Lucro": p["lucro"], "Rentab. %": p["rent"],
                    "Oscilação a.a. %": S.precos.get(p["ticker"], {}).get("vol"), "Queda máx. 3m %": S.precos.get(p["ticker"], {}).get("dd"),
                    "% carteira": p["atual"] / r["total"] * 100,
                    "Cotação": (S.precos[p["ticker"]]["fonte"] + " " + S.precos[p["ticker"]]["quando"]) if p["tem_cotacao"] else "sem cotação",
                } for p in r["rv"]])
                st.dataframe(tab, hide_index=True, width="stretch", column_config={
                    "Qtd": st.column_config.NumberColumn(format="%.4g"),
                    "Preço médio": st.column_config.NumberColumn(format="R$ %.2f"),
                    "Preço atual": st.column_config.NumberColumn(format="R$ %.2f"),
                    "Valor atual": st.column_config.NumberColumn(format="R$ %.2f"),
                    "Lucro": st.column_config.NumberColumn(format="R$ %.2f"),
                    "Rentab. %": st.column_config.NumberColumn(format="%.1f%%"),
                    "Hoje %": st.column_config.NumberColumn(format="%.2f%%"),
                    "Oscilação a.a. %": st.column_config.NumberColumn(format="%.0f%%", help="Volatilidade anualizada dos últimos 30 pregões"),
                    "Queda máx. 3m %": st.column_config.NumberColumn(format="%.1f%%", help="Maior queda a partir de um topo nos últimos 3 meses"),
                    "% carteira": st.column_config.NumberColumn(format="%.1f%%"),
                })
            if r["rf"]:
                st.markdown("**Renda fixa** (valores estimados pelo app)")
                tab2 = pd.DataFrame([{
                    "Produto": x["produto"], "Emissor": x.get("emissor", ""), "Tipo": x["tipo"], "Taxa": x.get("taxa", 0),
                    "Aplicado": float(x["valor"]), "Bruto hoje": x["bruto"], "IR estimado": x["ir"], "Líquido": x["liquido"],
                    "Desde": br_data(x["data"]), "Vencimento": br_data(x["venc"]) if x.get("venc") else "—",
                } for x in r["rf"]])
                st.dataframe(tab2, hide_index=True, width="stretch", column_config={
                    "Taxa": st.column_config.NumberColumn(format="%.2f"),
                    "Aplicado": st.column_config.NumberColumn(format="R$ %.2f"),
                    "Bruto hoje": st.column_config.NumberColumn(format="R$ %.2f"),
                    "IR estimado": st.column_config.NumberColumn(format="R$ %.2f"),
                    "Líquido": st.column_config.NumberColumn(format="R$ %.2f"),
                })
                st.caption("Estimativa: pós-fixado usa o CDI diário do Banco Central; IPCA+ usa o IPCA de 12 meses como aproximação. "
                           "Para o valor exato, use o extrato do banco e informe em 'Valor atual (opcional)'.")
            pc = pd.DataFrame([{"Classe": c, "Valor": v} for c, v in r["por_classe"].items() if v > 0])
            if not pc.empty:
                pie = alt.Chart(pc).mark_arc(innerRadius=60).encode(
                    theta="Valor:Q", color=alt.Color("Classe:N", scale=alt.Scale(scheme="greens"), title=None),
                    tooltip=["Classe", alt.Tooltip("Valor:Q", format=",.2f")]).properties(height=260)
                st.altair_chart(pie, width="stretch")
            if r["realizado"]:
                st.caption(f"Lucro/prejuízo já realizado em vendas: {brl(r['realizado'])}")
            with st.expander("✏️ Preço manual (quando a cotação automática não funcionar)"):
                ativos = [p["ticker"] for p in r["rv"]]
                if ativos:
                    m1, m2, m3 = st.columns([2, 2, 1])
                    t_man = m1.selectbox("Ativo", ativos, key="pm_t")
                    p_man = m2.number_input("Preço atual (R$)", min_value=0.0, step=0.01, key="pm_p")
                    if m3.button("Salvar", key="pm_ok", width="stretch") and p_man > 0:
                        S.precos[t_man] = {"preco": p_man, "fonte": "manual", "quando": datetime.now().strftime("%d/%m %H:%M"), "manual": True}
                        st.rerun()
                    st.caption("Preço manual não é sobrescrito pela atualização automática. Para voltar ao automático, informe 0 e salve.")

    with sub[1]:
        st.markdown("**Registrar compra ou venda**")
        with st.form(f"f_op_{S.ver}", clear_on_submit=True):
            o1, o2, o3 = st.columns(3)
            tipo = o1.radio("Operação", ["Compra", "Venda"], horizontal=True)
            ticker = o2.text_input("Código (ticker)", placeholder="ex.: PETR4, MXRF11, IVVB11, BTC")
            classe = o3.selectbox("Classe", ["Detectar pelo código"] + CLASSES[1:])
            o4, o5, o6, o7 = st.columns(4)
            qtd = o4.number_input("Quantidade", min_value=0.0, step=1.0, format="%.6g")
            preco = o5.number_input("Preço unitário (R$)", min_value=0.0, step=0.01)
            taxas = o6.number_input("Taxas (R$)", min_value=0.0, step=0.01)
            data_op = o7.date_input("Data", value=HOJE, max_value=HOJE, format="DD/MM/YYYY")
            conta_aporte = st.checkbox("Contar como aporte do mês (dinheiro novo)", value=True)
            salvar = st.form_submit_button("💾 Registrar operação", width="stretch")
        if salvar:
            t = ticker_ok(ticker)
            cl = classe_sugerida(t) if classe == "Detectar pelo código" else classe
            if not t or qtd <= 0 or preco <= 0:
                st.warning("Informe código, quantidade e preço.")
            else:
                pos_atual = {p["ticker"]: p for p in posicoes_rv()}
                if tipo == "Venda" and pos_atual.get(t, {}).get("qtd", 0) < qtd - 1e-9:
                    st.warning(f"Você só tem {num(pos_atual.get(t, {}).get('qtd', 0), 4)} de {t} registrados.")
                else:
                    S.ops.append({"id": str(uuid.uuid4())[:8], "tipo": tipo, "ticker": t, "classe": cl, "qtd": qtd,
                                  "preco": preco, "taxas": taxas, "data": data_op.isoformat(), "criado": datetime.now().isoformat()})
                    if tipo == "Compra" and conta_aporte:
                        S.aportes.append({"data": data_op.isoformat(), "valor": qtd * preco + taxas, "origem": t})
                        ganhar_xp(10, "Aporte registrado", unico=f"aporte_{data_op.isoformat()[:7]}")
                    ganhar_xp(5, f"{tipo} de {t}")
                    if t not in S.precos:
                        buscar_cotacao(t, cl)
                    S["_op_msg"] = f"{tipo} de {num(qtd, 4)} {t} ({cl}) registrada."
                    st.rerun()
        if S.get("_op_msg"):
            st.success(S.pop("_op_msg"))
        st.caption("Dica: o final do código indica a classe — 3/4 ações, 11 FIIs/ETFs/units, 34 BDRs. "
                   "ETFs com final 11 (ex.: BOVA11, IVVB11) devem ser marcados como 'ETFs e BDRs'.")
        if S.ops:
            st.markdown("**Histórico de operações**")
            for op in sorted(S.ops, key=lambda o: o["data"], reverse=True)[:60]:
                c1, c2 = st.columns([6, 1])
                c1.markdown(f"{br_data(op['data'])} · **{op['tipo']}** {num(op['qtd'], 4)} {op['ticker']} a {brl(op['preco'])} "
                            f"({op['classe']}) — total {brl(float(op['qtd']) * float(op['preco']) + float(op.get('taxas') or 0))}")
                if c2.button("🗑️", key=f"del_op_{op['id']}", help="Apagar operação"):
                    S.ops = [o for o in S.ops if o["id"] != op["id"]]
                    st.rerun()

    with sub[2]:
        st.markdown("**Registrar aplicação de renda fixa**")
        with st.form(f"f_rf_{S.ver}", clear_on_submit=True):
            r1, r2, r3 = st.columns(3)
            produto = r1.selectbox("Produto", PRODUTOS_RF)
            emissor = r2.text_input("Emissor / banco", placeholder="ex.: Banco X, Tesouro Nacional")
            tipo_rf = r3.selectbox("Rentabilidade", TIPOS_RF)
            r4, r5, r6 = st.columns(3)
            valor = r4.number_input("Valor aplicado (R$)", min_value=0.0, step=100.0)
            taxa = r5.number_input("Taxa (% do CDI, % a.a. ou IPCA + % a.a.)", min_value=0.0, step=0.1,
                                   help="Pós-fixado: % do CDI (ex.: 110). Prefixado: % ao ano (ex.: 13,5). IPCA+: só a taxa real (ex.: 6,5).")
            data_rf = r6.date_input("Data da aplicação", value=HOJE, max_value=HOJE, format="DD/MM/YYYY")
            r7, r8, r9 = st.columns(3)
            venc = r7.date_input("Vencimento (opcional)", value=None, format="DD/MM/YYYY")
            liq = r8.selectbox("Liquidez", ["Diária", "No vencimento", "Após carência"])
            manual = r9.number_input("Valor atual (opcional, do extrato)", min_value=0.0, step=10.0)
            conta_ap = st.checkbox("Contar como aporte do mês (dinheiro novo)", value=True, key="rf_aporte")
            ok_rf = st.form_submit_button("💾 Registrar aplicação", width="stretch")
        if ok_rf:
            if valor <= 0:
                st.warning("Informe o valor aplicado.")
            else:
                S.rf.append({"id": str(uuid.uuid4())[:8], "produto": produto, "emissor": emissor.strip(), "tipo": tipo_rf,
                             "valor": valor, "taxa": taxa, "data": data_rf.isoformat(), "venc": venc.isoformat() if venc else "",
                             "liquidez": liq, "valor_manual": manual or 0})
                if conta_ap:
                    S.aportes.append({"data": data_rf.isoformat(), "valor": valor, "origem": produto})
                    ganhar_xp(10, "Aporte registrado", unico=f"aporte_{data_rf.isoformat()[:7]}")
                ganhar_xp(5, f"Aplicação em {produto}")
                st.rerun()
        if S.rf:
            st.markdown("**Suas aplicações**")
            for it in S.rf:
                bruto, rend, ir = valor_rf(it)
                c1, c2, c3 = st.columns([5, 2, 1])
                c1.markdown(f"**{it['produto']}** {it.get('emissor') or ''} · {it['tipo']} {num(it.get('taxa', 0))} · aplicado {brl(it['valor'])} em {br_data(it['data'])}"
                            + (f" · vence {br_data(it['venc'])}" if it.get("venc") else ""))
                c2.markdown(f"Hoje ≈ **{brl(bruto)}** ({brl(rend)})")
                if c3.button("🗑️", key=f"del_rf_{it['id']}", help="Apagar"):
                    S.rf = [x for x in S.rf if x["id"] != it["id"]]
                    st.rerun()
                for x in S.rf:
                    if x["id"] == it["id"]:
                        novo = st.number_input("Atualizar valor atual pelo extrato (0 = usar estimativa)", min_value=0.0, step=10.0,
                                               value=float(it.get("valor_manual") or 0), key=f"vm_{it['id']}", label_visibility="collapsed")
                        if novo != float(it.get("valor_manual") or 0):
                            x["valor_manual"] = novo
                            st.rerun()

    with sub[3]:
        st.markdown("**Registrar dividendos, JCP e rendimentos**")
        with st.form(f"f_prov_{S.ver}", clear_on_submit=True):
            p1, p2, p3, p4 = st.columns(4)
            t_prov = p1.text_input("Ativo", placeholder="ex.: ITSA4, MXRF11")
            tipo_prov = p2.selectbox("Tipo", ["Dividendo", "JCP", "Rendimento de FII", "Outro"])
            v_prov = p3.number_input("Valor líquido (R$)", min_value=0.0, step=1.0)
            d_prov = p4.date_input("Data", value=HOJE, max_value=HOJE, format="DD/MM/YYYY")
            ok_p = st.form_submit_button("💾 Registrar provento", width="stretch")
        if ok_p and v_prov > 0 and t_prov.strip():
            S.proventos.append({"id": str(uuid.uuid4())[:8], "ticker": ticker_ok(t_prov), "tipo": tipo_prov, "valor": v_prov, "data": d_prov.isoformat()})
            ganhar_xp(5, "Provento registrado")
            st.rerun()
        if S.proventos:
            dfp = pd.DataFrame(S.proventos)
            dfp["Mês"] = dfp["data"].str[:7]
            total12 = dfp[dfp["data"] >= (HOJE - timedelta(days=365)).isoformat()]["valor"].sum()
            st.markdown(f'<div class="card">💵 Proventos nos últimos 12 meses: <b>{brl(total12)}</b> · média mensal <b>{brl(total12/12)}</b></div>', unsafe_allow_html=True)
            g = dfp.groupby("Mês", as_index=False)["valor"].sum()
            st.altair_chart(alt.Chart(g).mark_bar(color="#0F5132").encode(x=alt.X("Mês:N", title=None), y=alt.Y("valor:Q", title="R$"),
                                                                           tooltip=["Mês", alt.Tooltip("valor:Q", format=",.2f")]).properties(height=220), width="stretch")
            for pv in sorted(S.proventos, key=lambda x: x["data"], reverse=True)[:30]:
                c1, c2 = st.columns([6, 1])
                c1.markdown(f"{br_data(pv['data'])} · {pv['tipo']} de **{pv['ticker']}** · {brl(pv['valor'])}")
                if c2.button("🗑️", key=f"del_pv_{pv['id']}"):
                    S.proventos = [x for x in S.proventos if x["id"] != pv["id"]]
                    st.rerun()

    with sub[4]:
        st.markdown("**Aportes por mês** (dinheiro novo investido)")
        st.caption("Compras e aplicações marcadas como 'aporte' entram aqui automaticamente. A constância conta no pente fino.")
        if S.aportes:
            dfa = pd.DataFrame(S.aportes)
            dfa["Mês"] = dfa["data"].str[:7]
            g = dfa.groupby("Mês", as_index=False)["valor"].sum()
            plano = float(S.financas.get("aporte_plano") or 0)
            base = alt.Chart(g).mark_bar(color="#0F5132").encode(x=alt.X("Mês:N", title=None), y=alt.Y("valor:Q", title="R$"),
                                                                 tooltip=["Mês", alt.Tooltip("valor:Q", format=",.2f")])
            if plano > 0:
                base = base + alt.Chart(pd.DataFrame({"y": [plano]})).mark_rule(color="#D97706", strokeDash=[6, 4]).encode(y="y:Q")
            st.altair_chart(base.properties(height=240), width="stretch")
            if plano > 0:
                st.caption(f"Linha laranja: seu plano de {brl(plano)}/mês.")
        else:
            st.info("Nenhum aporte registrado ainda.")


# ══════════════════════════════════════════════════════════════════════════
# 5. PENTE FINO
# ══════════════════════════════════════════════════════════════════════════
with abas[4]:
    st.markdown("### 🔍 Pente fino da carteira")
    st.caption("O app confere reserva, alocação, concentração, diversificação, aportes e rendimento x CDI, e dá uma nota de 0 a 100. "
               "Faça todo mês: com 3 notas de 80 ou mais (e a trilha completa) você vira 🦁 Fera.")
    pf = pente_fino()
    cor = "#0F7A43" if pf["pontos"] >= 80 else ("#D97706" if pf["pontos"] >= 60 else "#B42318")
    c1, c2 = st.columns([1, 3])
    c1.markdown(f'<div class="kpi"><div class="l">Nota da carteira</div><div class="v" style="color:{cor}">{pf["pontos"]}/100</div></div>', unsafe_allow_html=True)
    if pf["resumo"]["rv"]:
        rk = pf["risco"]
        c1.markdown(f'<div class="kpi" style="margin-top:8px"><div class="l">Perda possível num dia ruim</div><div class="v neg">{brl(rk["perda_dia"])}</div>'
                    f'<div style="font-size:.75em;color:#4B6358">95% de confiança, com as cotações de {S.ultima_atualizacao.strftime("%H:%M") if S.ultima_atualizacao else "—"}</div></div>',
                    unsafe_allow_html=True)
        if c1.button("🔄 Refazer com cotações de agora", width="stretch"):
            atualizar_tudo()
            st.rerun()
    with c2:
        icone = {"critico": "🔴", "alerta": "🟠", "info": "🔵", "ok": "🟢"}
        ordem = {"critico": 0, "alerta": 1, "info": 2, "ok": 3}
        for a in sorted(pf["achados"], key=lambda x: ordem[x["nivel"]]):
            st.markdown(f'<div class="achado {a["nivel"]}">{icone[a["nivel"]]} <b>{a["titulo"]}</b><br>{a["texto"]}</div>', unsafe_allow_html=True)
    r = pf["resumo"]
    if r["total"] > 0:
        st.markdown("#### 🧭 Para onde vão os próximos aportes")
        aloc = alocacao_pct(r)
        alvo = ALVOS.get(S.perfil or "Moderado")
        aporte = float(S.financas.get("aporte_plano") or 0)
        novo_total = r["total"] + aporte
        falta = {c: max(alvo[c] / 100 * novo_total - r["por_classe"].get(c, 0), 0) for c in CLASSES}
        soma = sum(falta.values()) or 1
        dist = {c: aporte * falta[c] / soma for c in CLASSES} if aporte > 0 else {}
        if dist:
            st.markdown('<div class="card">Com o seu aporte de <b>' + brl(aporte) + '</b>, a divisão que aproxima a carteira do alvo é: '
                        + " · ".join(f"<b>{c}</b> {brl(v)}" for c, v in dist.items() if v >= 1) + '. '
                        '<br><span style="font-size:.85em;color:#4B6358;">Isso indica classes, não ativos. A escolha de cada ativo é sua.</span></div>',
                        unsafe_allow_html=True)
        else:
            st.caption("Informe quanto pretende investir por mês em 🧭 Meu Perfil para ver a divisão sugerida por classe.")
    b1, b2 = st.columns(2)
    if b1.button("💾 Registrar este pente fino", width="stretch"):
        S.revisoes.append({"data": HOJE.isoformat(), "pontos": pf["pontos"], "patrimonio": r["total"], "rent": r["rent"],
                           "achados": [a["titulo"] for a in pf["achados"] if a["nivel"] in ("critico", "alerta")]})
        ganhar_xp(30, "Pente fino registrado", unico=f"pente_{HOJE.isoformat()[:7]}")
        if pf["pontos"] >= 80:
            ganhar_xp(40, "Pente fino com nota 80+", unico=f"pente80_{HOJE.isoformat()[:7]}")
        st.rerun()
    if b2.button("🤖 Análise do mentor sobre este pente fino", width="stretch"):
        with st.spinner("O mentor está analisando sua carteira…"):
            try:
                achados_txt = "\n".join(f"- [{a['nivel']}] {a['titulo']}: {a['texto']}" for a in pf["achados"])
                S["_analise_pf"] = ia_texto(
                    f"Faça o pente fino da minha carteira. Nota calculada pelo app: {pf['pontos']}/100. Achados do app:\n{achados_txt}\n"
                    "Explique em linguagem simples: 1) o que está bom, 2) os 3 pontos mais importantes para corrigir, em ordem de "
                    "prioridade, com ações práticas para o próximo mês (sem indicar ativos específicos), 3) o que eu devo estudar "
                    "agora para evoluir como investidor. Termine com uma meta clara para o próximo pente fino.", max_tokens=2000)
            except RuntimeError as e:
                mostrar_erro(e)
    if S.get("_analise_pf"):
        st.markdown(f'<div class="card">{S["_analise_pf"]}</div>', unsafe_allow_html=True)
    if S.revisoes:
        st.markdown("#### 📈 Evolução das notas")
        dfr = pd.DataFrame(S.revisoes)
        dfr["Data"] = pd.to_datetime(dfr["data"])
        st.altair_chart(alt.Chart(dfr).mark_line(point=True, color="#0F5132").encode(
            x=alt.X("Data:T", title=None), y=alt.Y("pontos:Q", title="Nota", scale=alt.Scale(domain=[0, 100])),
            tooltip=[alt.Tooltip("Data:T", format="%d/%m/%Y"), "pontos"]).properties(height=220), width="stretch")


# ══════════════════════════════════════════════════════════════════════════
# 6. METAS
# ══════════════════════════════════════════════════════════════════════════
with abas[5]:
    st.markdown("### 🎯 Minhas metas")
    st.caption("O app recalcula o aporte necessário com base no seu patrimônio real e no rendimento que a carteira está tendo de fato.")
    with st.form(f"f_meta_{S.ver}", clear_on_submit=True):
        m1, m2, m3 = st.columns(3)
        nome_meta = m1.text_input("Meta", placeholder="ex.: Independência financeira, casa própria")
        valor_meta = m2.number_input("Valor (R$, em dinheiro de hoje)", min_value=0.0, step=1000.0)
        prazo_meta = m3.date_input("Prazo", value=date(HOJE.year + 10, HOJE.month, 1), min_value=HOJE + timedelta(days=30), format="DD/MM/YYYY")
        usa_carteira = st.checkbox("Usar todo o patrimônio da carteira para esta meta", value=True)
        ok_m = st.form_submit_button("🎯 Criar meta", width="stretch")
    if ok_m and nome_meta.strip() and valor_meta > 0:
        S.metas.append({"id": str(uuid.uuid4())[:8], "nome": nome_meta.strip(), "valor": valor_meta, "prazo": prazo_meta.isoformat(),
                        "usa_carteira": usa_carteira, "criada": HOJE.isoformat()})
        ganhar_xp(20, f"Meta criada: {nome_meta.strip()}", unico=f"meta_{nome_meta.strip().lower()}")
        st.rerun()
    r = resumo_carteira()
    real_obs = rent_anual_real(r)
    premissa = taxa_real_usada()
    st.markdown(f'<div class="card">📐 Premissa de rendimento real (acima da inflação): <b>{num(premissa,1)}% ao ano</b> '
                f'(padrão do perfil {S.perfil or "Moderado"}; ajuste em 🧮 Simuladores → Premissas).'
                + (f'<br>📊 Rendimento real que sua carteira teve até agora: <b>{num(real_obs,1)}% ao ano</b> (estimativa do app).' if real_obs is not None else
                   '<br>📊 O rendimento real da sua carteira aparece depois de 60 dias de histórico.')
                + '</div>', unsafe_allow_html=True)
    aporte_plano = float(S.financas.get("aporte_plano") or 0)
    for mt in S.metas:
        atual = r["total"] if mt.get("usa_carteira") else 0.0
        anos = max((datetime.fromisoformat(mt["prazo"]).date() - HOJE).days / 365, 1 / 12)
        nec = aporte_necessario(mt["valor"], atual, anos, premissa)
        prog = min(atual / mt["valor"], 1) if mt["valor"] else 0
        with st.container(border=True):
            c1, c2 = st.columns([5, 1])
            c1.markdown(f"**{mt['nome']}** · {brl(mt['valor'])} até {br_data(mt['prazo'])} ({num(anos,1)} anos)")
            if c2.button("🗑️", key=f"del_meta_{mt['id']}"):
                S.metas = [x for x in S.metas if x["id"] != mt["id"]]
                st.rerun()
            st.progress(prog, text=f"{num(prog*100,1)}% — você tem {brl(atual)}")
            linhas = [f"Aporte mensal necessário com a premissa de {num(premissa,1)}% real: **{brl(nec)}**"]
            if aporte_plano > 0:
                m_plano = meses_ate(mt["valor"], atual, aporte_plano, premissa)
                linhas.append(f"Com seu aporte de {brl(aporte_plano)}/mês: " + (f"chega em **{num(m_plano/12,1)} anos**" if m_plano else "não chega em 100 anos — aumente o aporte"))
            if real_obs is not None:
                nec_real = aporte_necessario(mt["valor"], atual, anos, max(real_obs, 0))
                linhas.append(f"Se a carteira continuar rendendo o que rendeu até agora ({num(real_obs,1)}% real): **{brl(nec_real)}/mês**")
            st.markdown("  \n".join(linhas))
    if not S.metas:
        st.info("Crie sua primeira meta. Exemplo: 'Independência financeira' com o valor que geraria a renda que você quer (veja em 🧮 Simuladores → Viver de renda).")


# ══════════════════════════════════════════════════════════════════════════
# 7. SIMULADORES
# ══════════════════════════════════════════════════════════════════════════
with abas[6]:
    st.markdown("### 🧮 Simuladores")
    s1, s2, s3, s4 = st.tabs(["📈 Juros compostos", "🏖️ Viver de renda", "⚖️ Comparar renda fixa", "⚙️ Premissas"])
    with s1:
        a1, a2, a3, a4 = st.columns(4)
        ini = a1.number_input("Valor inicial (R$)", min_value=0.0, value=1000.0, step=100.0)
        mens = a2.number_input("Aporte mensal (R$)", min_value=0.0, value=float(S.financas.get("aporte_plano") or 300.0), step=50.0)
        tx = a3.number_input("Rendimento (% ao ano)", min_value=0.0, value=float(S.premissas["cdi"]), step=0.5)
        anos_s = a4.slider("Anos", 1, 40, 10)
        i = (1 + tx / 100) ** (1 / 12) - 1
        v, apl, linhas = ini, ini, []
        for mth in range(1, anos_s * 12 + 1):
            v = v * (1 + i) + mens
            apl += mens
            if mth % 12 == 0:
                linhas.append({"Ano": mth // 12, "Total": v, "Investido": apl})
        dfj = pd.DataFrame(linhas)
        k1, k2, k3 = st.columns(3)
        k1.markdown(f'<div class="kpi"><div class="l">Total ao final</div><div class="v">{brl(v)}</div></div>', unsafe_allow_html=True)
        k2.markdown(f'<div class="kpi"><div class="l">Você investiu</div><div class="v">{brl(apl)}</div></div>', unsafe_allow_html=True)
        k3.markdown(f'<div class="kpi"><div class="l">Juros ganhos</div><div class="v pos">{brl(v - apl)}</div></div>', unsafe_allow_html=True)
        dl = dfj.melt("Ano", var_name="Série", value_name="R$")
        st.altair_chart(alt.Chart(dl).mark_area(opacity=.55).encode(
            x="Ano:Q", y=alt.Y("R$:Q", stack=None), color=alt.Color("Série:N", scale=alt.Scale(domain=["Total", "Investido"], range=["#0F5132", "#A7D7BF"]), title=None),
            tooltip=["Ano", "Série", alt.Tooltip("R$:Q", format=",.2f")]).properties(height=280), width="stretch")
        st.caption("Valores nominais, sem impostos e sem descontar a inflação.")
    with s2:
        b1, b2, b3 = st.columns(3)
        renda_d = b1.number_input("Renda mensal desejada (R$ de hoje)", min_value=0.0, value=5000.0, step=500.0)
        retirada = b2.number_input("Taxa de retirada (% ao ano, real)", min_value=1.0, max_value=10.0, value=4.0, step=0.5,
                                   help="A 'regra dos 4%' é uma referência internacional; no Brasil muitos usam de 4% a 6% real.")
        tx_real = b3.number_input("Rendimento real até lá (% a.a.)", min_value=0.0, value=taxa_real_usada(), step=0.5)
        alvo_v = renda_d * 12 / (retirada / 100)
        r = resumo_carteira()
        aporte_p = float(S.financas.get("aporte_plano") or 0)
        mm = meses_ate(alvo_v, r["total"], aporte_p, tx_real) if aporte_p > 0 else None
        st.markdown(f'<div class="card">Para tirar <b>{brl(renda_d)}/mês</b> retirando {num(retirada,1)}% ao ano, você precisa de '
                    f'<b>{brl(alvo_v)}</b> (em dinheiro de hoje).<br>'
                    + (f'Com {brl(r["total"])} hoje e {brl(aporte_p)}/mês a {num(tx_real,1)}% real: cerca de <b>{num(mm/12,1)} anos</b>.' if mm else
                       'Informe seu aporte mensal em 🧭 Meu Perfil para ver em quanto tempo chega.') + '</div>', unsafe_allow_html=True)
        if st.button("🎯 Criar meta de independência com esse valor", width="stretch"):
            S.metas.append({"id": str(uuid.uuid4())[:8], "nome": "Independência financeira", "valor": round(alvo_v, 2),
                            "prazo": date(HOJE.year + 20, HOJE.month, 1).isoformat(), "usa_carteira": True, "criada": HOJE.isoformat()})
            ganhar_xp(20, "Meta criada: Independência financeira", unico="meta_independência financeira")
            st.success("Meta criada em 🎯 Metas (prazo de 20 anos; você pode apagar e recriar com outro prazo).")
    with s3:
        st.caption(f"Compara o valor líquido no fim do prazo, com CDI de {num(S.premissas['cdi'])}% e Selic de {num(S.premissas['selic'])}% ao ano.")
        c1, c2, c3 = st.columns(3)
        val_c = c1.number_input("Valor (R$)", min_value=0.0, value=10000.0, step=500.0, key="cmp_v")
        dias_c = c2.number_input("Prazo (dias corridos)", min_value=30, value=730, step=30, key="cmp_d")
        c4, c5 = st.columns(2)
        cdb = c3.number_input("CDB (% do CDI)", min_value=0.0, value=110.0, step=1.0)
        lci = c4.number_input("LCI/LCA (% do CDI)", min_value=0.0, value=92.0, step=1.0)
        pre = c5.number_input("CDB prefixado (% a.a.)", min_value=0.0, value=round(S.premissas["cdi"], 1), step=0.1)
        du = dias_c * 252 / 365
        f_cdi = (1 + S.premissas["cdi"] / 100) ** (du / 252) - 1
        f_selic = (1 + S.premissas["selic"] / 100) ** (du / 252) - 1
        al = aliquota_rf(dias_c) / 100
        selic = S.premissas["selic"]
        mensal_p = 0.005 + S.premissas["tr"] / 100 if selic > 8.5 else (1 + selic * 0.7 / 100) ** (1 / 12) - 1
        opcoes = {
            f"CDB {num(cdb,0)}% do CDI": val_c * f_cdi * cdb / 100 * (1 - al),
            f"LCI/LCA {num(lci,0)}% do CDI (isenta)": val_c * f_cdi * lci / 100,
            "Tesouro Selic (custódia 0,20% a.a. acima de R$ 10 mil)": val_c * (f_selic * (1 - al)) - max(val_c - 10000, 0) * 0.002 * dias_c / 365,
            f"CDB prefixado {num(pre,1)}% a.a.": val_c * ((1 + pre / 100) ** (du / 252) - 1) * (1 - al),
            "Poupança (isenta)": val_c * ((1 + mensal_p) ** (dias_c / 30.4) - 1),
        }
        dfc = pd.DataFrame([{"Opção": k, "Ganho líquido": v, "Valor final": val_c + v} for k, v in opcoes.items()]).sort_values("Ganho líquido", ascending=False)
        st.dataframe(dfc, hide_index=True, width="stretch", column_config={
            "Ganho líquido": st.column_config.NumberColumn(format="R$ %.2f"), "Valor final": st.column_config.NumberColumn(format="R$ %.2f")})
        st.caption(f"IR da tabela regressiva para {dias_c} dias: {num(al*100,1)}%. Estimativa com taxas constantes; o resultado real varia.")
    with s4:
        st.caption("Valores usados nos cálculos. CDI, Selic e IPCA vêm do Banco Central quando a conexão funciona.")
        if st.button("🔄 Buscar CDI, Selic e IPCA no Banco Central"):
            ok = atualizar_indicadores()
            st.success("Atualizado: " + ", ".join(ok)) if ok else st.warning("Não consegui falar com o Banco Central agora. Ajuste os valores à mão.")
        p1, p2, p3, p4 = st.columns(4)
        S.premissas["cdi"] = p1.number_input("CDI (% a.a.)", value=float(S.premissas["cdi"]), step=0.05, key=f"pr_cdi_{S.ver}")
        S.premissas["selic"] = p2.number_input("Selic (% a.a.)", value=float(S.premissas["selic"]), step=0.05, key=f"pr_selic_{S.ver}")
        S.premissas["ipca"] = p3.number_input("IPCA 12 meses (%)", value=float(S.premissas["ipca"]), step=0.05, key=f"pr_ipca_{S.ver}")
        S.premissas["tr"] = p4.number_input("TR (% ao mês)", value=float(S.premissas["tr"]), step=0.01, key=f"pr_tr_{S.ver}")
        q1, q2 = st.columns(2)
        tr_in = q1.number_input("Rendimento real das metas (% a.a.; 0 = padrão do perfil)", min_value=0.0, max_value=15.0,
                                value=float(S.premissas.get("taxa_real") or 0), step=0.5, key=f"pr_real_{S.ver}")
        S.premissas["taxa_real"] = tr_in or None
        S.premissas["brapi_token"] = q2.text_input("Token da brapi.dev (opcional, cotações reserva)", value=S.premissas.get("brapi_token", ""),
                                                   type="password", key=f"pr_brapi_{S.ver}")


# ══════════════════════════════════════════════════════════════════════════
# 8. NÍVEL
# ══════════════════════════════════════════════════════════════════════════
with abas[7]:
    st.markdown("### 🏆 Meu nível de investidor")
    nome_nivel, atual_nv, prox = nivel_atual()
    cols = st.columns(len(NIVEIS_INV))
    idx_atual = NIVEIS_INV.index(atual_nv)
    for j, (nv, col) in enumerate(zip(NIVEIS_INV, cols)):
        estilo = "background:#0F5132;color:#fff;" if j <= idx_atual else "background:#fff;color:#4B6358;"
        col.markdown(f'<div class="kpi" style="{estilo}"><div style="font-size:1.1em;font-weight:800;">{nv[0]}</div>'
                     f'<div style="font-size:.8em;">{nv[1]} XP' + (f' + nível {nv[2]} da trilha' if nv[2] else '') +
                     (' + 3 pentes finos 80+' if nv[0].endswith("Fera") else '') + '</div></div>', unsafe_allow_html=True)
    st.write("")
    if prox:
        falta = requisitos_proximo(prox)
        st.info(f"Para chegar a **{prox[0]}** falta: " + (", ".join(falta) if falta else "nada!"))
    else:
        st.success("🦁 Você é um Investidor Fera! Continue com os aportes e o pente fino mensal para manter a carteira afiada.")
    st.markdown("#### Como ganhar XP")
    st.markdown("- Definir o perfil: **+50**\n- Aula com a IA: **+10** por módulo\n- Módulo aprovado: **+100** (nota 100: **+50** extra)\n"
                "- Registrar operação ou aplicação: **+5**\n- Primeiro aporte de cada mês: **+10**\n- Criar meta: **+20**\n"
                "- Pente fino do mês: **+30** (nota 80+: **+40** extra)")
    if S.xp_log:
        st.markdown("#### Histórico")
        for x in reversed(S.xp_log[-25:]):
            st.markdown(f"{br_data(x['data'])} · **+{x['xp']} XP** · {x['motivo']}")


# ══════════════════════════════════════════════════════════════════════════
# 9. MENTOR
# ══════════════════════════════════════════════════════════════════════════
with abas[8]:
    st.markdown("### 💬 Mentor de investimentos")
    st.caption("Pergunte qualquer coisa: conceitos, como analisar um ativo, impostos, sua carteira. O mentor conhece seus números do app. "
               "Ele ensina e mostra riscos, mas não diz o que comprar.")
    ativos_cart = [p["ticker"] for p in resumo_carteira()["rv"]]
    n1, n2 = st.columns([2, 1])
    with n1:
        if st.button("📰 Notícias e riscos agora (pesquisa na internet)", width="stretch"):
            alvo_txt = ", ".join(ativos_cart) if ativos_cart else "Ibovespa, juros (Selic) e dólar"
            with st.spinner("Pesquisando notícias de agora…"):
                try:
                    S.noticias = ia_web(
                        f"Pesquise as notícias mais recentes (últimos dias) sobre: {alvo_txt}, e sobre o mercado brasileiro hoje. "
                        "Para cada ativo: o que aconteceu, data, fonte e qual RISCO isso pode trazer para quem tem esse ativo. "
                        "Depois, um resumo dos riscos do mercado hoje (juros, dólar, Ibovespa). Não recomende comprar ou vender.")
                    S["_noticias_quando"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                except RuntimeError as e:
                    mostrar_erro(e)
    with n2:
        web_chat = st.toggle("🌐 Pesquisar na internet nas respostas", value=False,
                             help="O mentor busca informações de agora antes de responder (mais lento).")
    if S.noticias:
        with st.expander(f"📰 Notícias e riscos — pesquisa de {S.get('_noticias_quando', '')}", expanded=True):
            st.markdown(S.noticias)
    sug = ["Como escolho um FII?", "Vale a pena Tesouro IPCA+ agora?", "Como declarar ações no IR?", "Minha carteira está muito arriscada?"]
    cs = st.columns(len(sug))
    pergunta_rapida = None
    for s_, c in zip(sug, cs):
        if c.button(s_, width="stretch"):
            pergunta_rapida = s_
    caixa = st.container(height=420)
    with caixa:
        if not S.chat:
            st.markdown("👋 Olá! Sou o seu mentor. Pergunte o que quiser sobre investimentos.")
        for msg in S.chat:
            with st.chat_message("user" if msg["role"] == "user" else "assistant", avatar="🙂" if msg["role"] == "user" else "📈"):
                st.markdown(msg["content"])
    pergunta = st.chat_input("Escreva sua pergunta…") or pergunta_rapida
    if pergunta:
        S.chat.append({"role": "user", "content": pergunta})
        msgs = [{"role": "system", "content": REGRA_IA},
                {"role": "system", "content": "DADOS DO ALUNO (calculados pelo app):\n" + contexto_aluno()}] + S.chat[-12:]
        try:
            resp = ia_web(pergunta + "\n\n(Contexto da conversa: " + " | ".join(m["content"][:200] for m in S.chat[-6:-1]) + ")") if web_chat else ia(msgs, max_tokens=1500)
        except RuntimeError as e:
            resp = f"⚠️ {e}"
        S.chat.append({"role": "assistant", "content": resp})
        st.rerun()
    if S.chat and st.button("🧹 Limpar conversa"):
        S.chat = []
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════
# 10. GUIA
# ══════════════════════════════════════════════════════════════════════════
with abas[9]:
    st.markdown("### 📘 Como usar o Investidor Fera")
    GUIA = [
        ("1. Defina seu perfil", "Em **🧭 Meu Perfil**, responda as 6 perguntas e informe renda, gastos, reserva e quanto quer investir por mês. "
         "O app calcula seu perfil (Conservador, Moderado ou Arrojado) e a alocação-alvo da carteira."),
        ("2. Estude a trilha", "Em **🎓 Trilha**, abra o módulo liberado, leia os pontos-chave e, se quiser, peça a **aula completa com a IA**. "
         "Depois faça a **prova**: com 80% ou mais o módulo é aprovado e o próximo é liberado. São 15 módulos em 4 níveis."),
        ("3. Registre sua carteira", "Em **💼 Carteira**, registre compras e vendas de ações, FIIs, ETFs e cripto (com o código, ex.: PETR4) e suas aplicações "
         "de renda fixa. Clique em **🔄 Atualizar cotações** para ver os preços atuais. Registre também dividendos e rendimentos."),
        ("📡 Tempo real", "No **🏠 Painel**, o quadro **📡 Ao vivo** busca sozinho Ibovespa, dólar, S&P 500 e as cotações dos seus ativos "
         "(a cada 1, 5 ou 15 minutos, você escolhe) e recalcula o risco: variação do dia, quedas fortes e quanto a carteira poderia perder num dia ruim. "
         "As cotações gratuitas da B3 têm atraso de cerca de 15 minutos. No **💬 Mentor**, o botão **📰 Notícias e riscos agora** pesquisa na internet "
         "as notícias recentes dos seus ativos."),
        ("4. Faça o pente fino todo mês", "Em **🔍 Pente fino**, veja a nota da carteira e os pontos de atenção. Clique em **💾 Registrar** para guardar a nota "
         "e em **🤖 Análise do mentor** para receber um plano para o próximo mês. O app também mostra como dividir o próximo aporte entre as classes."),
        ("5. Acompanhe suas metas", "Em **🎯 Metas**, crie objetivos. O app recalcula o aporte mensal necessário com o seu patrimônio real e com o rendimento que a carteira está tendo."),
        ("6. Suba de nível", "XP vem de estudar, registrar, aportar e fazer o pente fino. Para virar **🦁 Fera**: 2.600 XP, toda a trilha aprovada e 3 pentes finos com nota 80 ou mais."),
        ("7. Salve sua memória", "Os dados ficam só nesta sessão. Em **💾 Minha memória**, salve o arquivo .json no seu aparelho e abra na próxima visita."),
        ("⚠️ Importante", "O Investidor Fera é **educativo**. Ele ensina, calcula e acompanha, mas **não recomenda comprar ou vender** ativos específicos — "
         "isso exige um profissional certificado. Rentabilidade passada não garante rentabilidade futura. Confira regras de imposto na Receita Federal."),
    ]
    for t, c in GUIA:
        with st.expander(t):
            st.markdown(c)
    st.markdown(f'<p class="aviso-cvm">🤖 Mais agentes em <a href="{SITE}" target="_blank">MeusAgentesIA.com.br</a></p>', unsafe_allow_html=True)
