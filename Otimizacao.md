**Relatório de Otimização**

Plugin de Gerenciamento de Software

*Análise de Consumo da API Anthropic | Janeiro–Fevereiro 2026*

# **1\. Resumo Executivo**

O plugin de gerenciamento de software, implantado em 06/02/2026, gerou um aumento de 550% no custo diário da API Anthropic. A análise dos dados granulares por modelo revela que o Opus (4-5 e 4-6) é responsável por \~96% do custo total ($889 de $926), enquanto o Haiku processa volumes significativos por menos de $10 no total do período.

Este documento apresenta três eixos de otimização que, combinados, podem reduzir o custo mensal de \~$650 para \~$150, uma economia de 77%.

# **2\. Diagnóstico: Impacto do Plugin**

## **2.1 Comparativo de Custos por Período**

A tabela abaixo mostra o impacto direto da implantação do plugin:

| Período | Opus ($) | Sonnet ($) | Haiku ($) | Total ($) | Variação |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **Jan (01-09 a 01-30)** | 221.47 | 1.44 | 5.64 | 230.99 | baseline |
| **Fev pré-plugin (02-02 a 02-05)** | 85.87 | 10.46 | 3.01 | 99.74 | \+73%/sem |
| **Fev pós-plugin (02-06 a 02-17)** | 627.64 | 4.97 | 4.70 | 647.65 | \+550% |

O salto de custo após o plugin se deve a dois fatores: o volume de tokens processados aumentou (mais chamadas à API) e o contexto por chamada cresceu (backlogs carregados integralmente no prompt).

## **2.2 Distribuição de Custo por Modelo**

A análise por modelo revela uma concentração extrema no Opus:

| Métrica | Opus | Sonnet | Haiku |
| :---- | :---- | :---- | :---- |
| **% do custo total** | **\~96%** | \~2% | \~2% |
| **Custo/MTok (input)** | $15.00 | $3.00 | $0.80 |
| **Custo/MTok (cache read)** | $1.50 | $0.30 | $0.08 |
| **Uso recomendado** | Decisões complexas | Análise e geração | Triagem e consultas |

Nos dias de pico como 02-14 ($101.87), o Opus foi responsável por $101.13 (99.3%) enquanto Haiku custou apenas $0.36 processando 1.4M tokens. Isso demonstra que o Haiku é extremamente eficiente para tarefas de menor complexidade.

## **2.3 Padrão de Cache: Ineficiência Identificada**

O cache create apresenta variação de 80x entre dias (66K a 5.4M), indicando que o conteúdo cacheado (backlogs em markdown) muda frequentemente e invalida o cache. Os dias mais caros coincidem com os maiores volumes de cache create no Opus:

* 02-14: 3.2M cache create no Opus → $101.13

* 02-11: 2.2M cache create no Opus → $94.69

* 02-16: 2.4M cache create no Opus → $85.27

* 02-13: 3.1M cache create no Opus → $64.17

Esses 4 dias representam $345 (37% do custo total) e indicam que alterações nos backlogs estão forçando recriações massivas de cache no modelo mais caro.

# **3\. Eixos de Otimização**

## **3.1 Eixo 1: API Interna para Backlogs**

**Problema**

O plugin carrega backlogs completos em markdown como contexto do prompt. A cada alteração (novo item, repriorização, mudança de status), o cache é invalidado e recriado integralmente no Opus.

**Solução**

Substituir o carregamento estático por uma API REST interna consumida via tool use (skill). O modelo consulta apenas os dados necessários sob demanda.

| Método | Endpoint | Descrição | Redução de Contexto |
| :---- | :---- | :---- | :---- |
| **GET** | /backlog/sprint-atual | Itens do sprint ativo | \~90% (só itens do sprint) |
| **GET** | /backlog/item/{id} | Detalhe de um item | \~99% (1 item) |
| **GET** | /backlog?prioridade=alta | Filtro por prioridade | \~80% (subset filtrado) |
| **GET** | /backlog/resumo | Visão geral compacta | \~95% (contadores) |
| **PATCH** | /backlog/item/{id} | Atualizar item | N/A (escrita) |
| **POST** | /backlog/item | Criar novo item | N/A (escrita) |

**Benefícios esperados**

* Redução de 70-90% nos tokens de contexto por chamada

* Cache do system prompt estabilizado (definição dos tools muda raramente)

* Sessões do Claude Code mais longas sem atingir o limite de contexto

* Menor latência por turno (menos tokens para processar)

**Impacto nas sessões do Claude Code**

Com o contexto do backlog fora da janela de contexto, o espaço disponível para o histórico de conversa aumenta significativamente. Isso permite sessões mais produtivas: o modelo mantém mais contexto sobre o raciocínio em andamento e atinge o limite de contexto com menos frequência, reduzindo a necessidade de reiniciar sessões e perder continuidade.

## **3.2 Eixo 2: Roteamento Inteligente de Modelos**

**Problema**

Atualmente, \~96% do custo está concentrado no Opus, independentemente da complexidade da tarefa. Consultas simples como buscar status de um item ou listar o sprint atual estão sendo processadas pelo modelo mais caro.

**Solução**

Implementar uma camada de roteamento que classifica a tarefa antes de selecionar o modelo:

| Tipo de Tarefa | Modelo | Custo Relativo | Exemplos |
| :---- | :---- | :---- | :---- |
| **Consulta e triagem** | **Haiku** | 1x (base) | Buscar itens, listar sprints, status check |
| **Análise e geração** | **Sonnet** | 4x | Escrever specs, analisar bugs, code review |
| **Decisão complexa** | **Opus** | 19x | Arquitetura, refactoring crítico, planejamento |

**Implementação sugerida**

O roteamento pode ser implementado no próprio plugin com lógica baseada em padrões:

* Comandos que iniciam com verbos de consulta (listar, buscar, verificar, status) → Haiku

* Comandos de análise, geração de código, escrita de documentação → Sonnet

* Comandos explícitos de arquitetura, revisão crítica ou planejamento → Opus

* Fallback: se o modelo menor não conseguir resolver, escalar automaticamente

## **3.3 Eixo 3: Otimização de Prompts e Cache**

**Problema**

O system prompt do plugin provavelmente inclui instruções extensas que mudam junto com o contexto do backlog, invalidando o cache inteiro.

**Solução**

Separar o prompt em camadas com diferentes frequências de mudança:

* Camada estática (cacheable): definição dos tools, regras de negócio fixas, formato de resposta

* Camada semi-estática: configurações do projeto, preferências do usuário

* Camada dinâmica (não cacheable): dados do backlog (via API), contexto da tarefa atual

Essa separação maximiza o cache hit ratio, mantendo a camada estática cacheada por longos períodos enquanto os dados dinâmicos são consultados sob demanda via tool use.

# **4\. Projeção de Economia**

Estimativa conservadora baseada nos dados de fevereiro 2026 (período pós-plugin):

| Melhoria | Custo Atual | Custo Estimado | Economia |
| :---- | :---- | :---- | :---- |
| **API de Backlogs** | \~$650/mês | \~$400/mês | **\-38%** |
| **Roteamento de Modelos** | \~$650/mês | \~$250/mês | **\-62%** |
| **Ambas combinadas** | \~$650/mês | \~$150/mês | **\-77%** |

A economia combinada de 77% é viável porque as duas melhorias atuam em vetores diferentes: a API reduz o volume de tokens processados, enquanto o roteamento reduz o custo por token ao usar modelos mais baratos para tarefas simples.

# **5\. Plano de Implementação**

## **Fase 1: API de Backlogs (1-2 semanas)**

1. Criar endpoints REST para consulta do backlog (GET /backlog/sprint-atual, /backlog/item/{id}, etc.)

2. Definir schema da skill/tool no system prompt do plugin

3. Remover carregamento estático dos markdowns do contexto

4. Testar impacto no cache create e no tamanho do contexto por sessão

## **Fase 2: Roteamento de Modelos (1 semana)**

1. Implementar classificador de tarefas (regex/heurística ou LLM leve)

2. Configurar roteamento Haiku/Sonnet/Opus baseado na classificação

3. Implementar fallback automático (escalação se o modelo menor falhar)

4. Monitorar distribuição de custo por modelo após a mudança

## **Fase 3: Otimização de Cache (1 semana)**

1. Separar system prompt em camadas estática/dinâmica

2. Monitorar ratio cache read/create (meta: \>30:1 consistentemente)

3. Ajustar max\_tokens para evitar respostas excessivamente longas

4. Configurar alertas de custo diário para detectar anomalias

# **6\. Métricas de Acompanhamento**

Para validar o sucesso das otimizações, monitorar as seguintes métricas semanalmente:

* Custo diário médio (meta: \<$10/dia vs atual \~$45/dia)

* Ratio cache read/create (meta: \>30:1 vs atual \~22:1)

* % do custo no Opus (meta: \<40% vs atual \~96%)

* Duração média das sessões do Claude Code (meta: \+50%)

* Número de sessões reiniciadas por dia (meta: redução de 50%)

* Tokens médios de contexto por chamada (meta: redução de 70%)

# **7\. Considerações Finais**

O plugin de gerenciamento de software trouxe funcionalidade valiosa, mas sua arquitetura atual de carregamento de contexto não é sustentável em termos de custo. As otimizações propostas não reduzem funcionalidade — pelo contrário, a API de backlogs permite consultas mais granulares e o roteamento de modelos mantém a qualidade onde ela importa (tarefas complexas no Opus) enquanto usa modelos eficientes para o trabalho rotineiro.

A implementação faseada permite validar cada melhoria isoladamente e medir o impacto real antes de avançar para a próxima etapa. O investimento de 3-4 semanas de desenvolvimento deve se pagar em menos de 1 mês de operação.