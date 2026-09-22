---
name: refactor-arch
description: Audita a arquitetura de um projeto e o refatora para o padrão MVC, de forma agnóstica de linguagem e framework. Executa três fases — análise de stack, auditoria com relatório de findings por severidade, e refatoração validada por diff de contrato HTTP. Use quando pedirem /refactor-arch, auditoria de arquitetura, detecção de code smells e anti-patterns, ou reestruturação de um projeto legado para MVC.
---

# refactor-arch

Três fases sequenciais sobre o projeto no diretório corrente: **analisar**, **auditar**, **refatorar**.

Funciona em qualquer stack. Nada aqui assume Python, Node ou framework específico — o conhecimento dependente de tecnologia vive nas tabelas de manifestação dos arquivos de referência.

## Regras invioláveis

1. **A Fase 2 pausa.** Nenhum arquivo do projeto é criado, alterado ou removido antes de uma confirmação afirmativa explícita do humano. Escrever o relatório fora do projeto é permitido; tocar no código, não.
2. **Sem baseline, sem Fase 3.** Se a aplicação original não sobe, a Fase 3 aborta. Refatorar sem poder provar que nada quebrou é pior que não refatorar.
3. **Nunca infira arquitetura da árvore de diretórios.** Um projeto com `models/`, `routes/` e `services/` pode ter toda a regra de negócio dentro das rotas. Descubra onde a responsabilidade *mora*, não como as pastas se chamam.
4. **O contrato HTTP é preservado.** As únicas exceções permitidas estão na seção "Exceções de contrato" abaixo, e cada uma precisa ser declarada no relatório antes do gate.
5. **Todo finding tem `arquivo:linha` verificado.** Abra o arquivo e confirme a linha antes de escrever o finding. Número de linha errado invalida o achado.
6. **Não invente severidade.** Use a escala da seção abaixo. Na dúvida entre dois níveis, a severidade se ancora no *pior caso plausível*, não no primeiro efeito que vier à cabeça.

## Escala de severidade

| Nível | Critério |
|---|---|
| **CRITICAL** | Falha de segurança explorável, exposição de dado sensível, ou violação total de separação de responsabilidades (God class com banco, regra e roteamento juntos) |
| **HIGH** | Violação forte de MVC ou SOLID que impede teste e manutenção: regra de negócio presa em controller ou repositório, acoplamento sem injeção, estado global mutável |
| **MEDIUM** | Duplicação, padronização, performance moderada: N+1, API deprecated, validação ausente, erro sem tratamento centralizado |
| **LOW** | Legibilidade: nomes ruins, magic numbers, código morto, `print` como log |

## Carregamento de referências

Carregue **apenas** o que a fase corrente exige. Não leia tudo de uma vez.

| Fase | Arquivos |
|---|---|
| 1 | `references/project-analysis.md` |
| 2 | `references/antipattern-catalog.md`, `references/report-template.md` |
| 3 | `references/contract-baseline.md`, `references/mvc-guidelines.md`, `references/refactoring-playbook.md` |

---

## Fase 1 — Análise

Leia `references/project-analysis.md` e siga as heurísticas dali.

1. Detecte linguagem, framework e versão, dependências e banco a partir do manifesto e do entry point.
2. Conte os arquivos-fonte **do projeto** — exclua dependências instaladas, lockfiles, artefatos de build, bancos de dados e a própria pasta `.claude/`.
3. Identifique as tabelas ou coleções.
4. Infira o domínio a partir dos nomes de tabela, rota e entidade.
5. **Mapeie a arquitetura real** pelas quatro responsabilidades (quem abre conexão, quem monta query, quem decide regra, quem trata HTTP). Classifique conforme a tabela de arquiteturas do arquivo de referência.
6. Enumere todas as rotas com método e caminho — a Fase 3 vai precisar dessa lista.

Imprima:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem e versão>
Framework:     <framework e versão>
Dependencies:  <as relevantes>
Domain:        <domínio em uma linha>
Architecture:  <classificação + justificativa em uma linha>
Source files:  <N> files analyzed | ~<N> lines
Routes:        <N> endpoints
DB tables:     <lista>
================================
```

O campo `Architecture` precisa descrever onde a responsabilidade está, não quais pastas existem. `"Monolítica — 4 arquivos, sem separação de camadas"` e `"Camadas decorativas — models/ e routes/ existem, mas a regra de negócio está nas rotas"` são respostas válidas. `"Segue MVC"` só é válido se as regras de camada de `mvc-guidelines.md` forem verificadas e passarem.

---

## Fase 2 — Auditoria

Leia `references/antipattern-catalog.md` e `references/report-template.md`.

1. Para cada anti-pattern do catálogo, procure o sinal nos lugares indicados no campo `Onde procurar` — que inclui manifesto e lockfile, não só código-fonte.
2. Confirme `arquivo:linha` abrindo o arquivo. Agrupe ocorrências do mesmo anti-pattern num finding só, listando as linhas.
3. Classifique pela severidade do catálogo.
4. Monte o relatório no formato de `report-template.md`, ordenado CRITICAL → HIGH → MEDIUM → LOW.
5. Liste as **exceções de contrato** que a Fase 3 vai aplicar e os findings marcados `REQUER DECISÃO DE PRODUTO`, que não serão corrigidos.
6. Salve o relatório conforme a seção "Onde salvar" de `report-template.md` — na raiz do git (`git rev-parse --show-toplevel`), não dentro do projeto auditado.

Termine perguntando, e **pare**:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

Não prossiga sem um "y" explícito. "Parece bom", silêncio ou uma pergunta do usuário não são confirmação.

### Exceções de contrato

Três classes de correção mudam o contrato porque o elemento exposto *é* o achado. Só estas são permitidas, e cada uma precisa aparecer nominalmente no relatório antes do gate:

| Exceção | Ação |
|---|---|
| Endpoint que existe apenas como vulnerabilidade (executor de SQL arbitrário, reset de banco sem auth) | Removido |
| Campo sensível no corpo da resposta (senha, hash, chave, token) | Campo removido, resto do objeto intacto |
| Dado sensível gravado em log (cartão, credencial, segredo) | Log removido ou mascarado |

**A Fase 3 não adiciona autenticação.** Findings de autenticação ausente ou simulada ficam no relatório marcados `REQUER DECISÃO DE PRODUTO`, com a transformação descrita e não aplicada — implementá-la faria toda rota responder 401 e quebraria o contrato que esta skill se compromete a preservar.

---

## Fase 3 — Refatoração

Leia `references/contract-baseline.md`, `references/mvc-guidelines.md` e `references/refactoring-playbook.md`.

**3.1. Capture o baseline.** Siga `contract-baseline.md`. Resete o estado do banco, suba a aplicação original, dispare todos os endpoints da Fase 1 e grave status e corpo em `.refactor-arch/baseline.json`. Se o boot falhar, **aborte e informe** — não refatore.

**3.2. Crie a estrutura alvo** conforme `mvc-guidelines.md`, adaptada ao porte do projeto.

**3.3. Aplique as transformações** do playbook, nesta ordem de dependência:

```
config → camada de dados → regra de negócio → controllers
       → rotas → middleware de erro → composition root
```

**3.4. Verifique.** Resete o banco ao mesmo estado, suba a aplicação refatorada, redispare os mesmos endpoints e faça diff contra o baseline. Divergência que não seja exceção declarada é falha: corrija e repita. Se uma divergência for conserto de bug que o baseline capturou como comportamento, **apresente ao humano com os dois valores** — nunca silencie.

**3.5. Relate:**

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore>

## Contract Validation
<N>/<N> endpoints idênticos
<divergências declaradas, se houver>

## Anti-patterns
Eliminados: <N> | Remanescentes: <N> (requerem decisão de produto)
================================
```

---

## Adaptação ao contexto

O esforço da Fase 3 depende do que a Fase 1 encontrou. Um monolito de 4 arquivos precisa de reestruturação completa; um projeto com camadas decorativas precisa que a responsabilidade volte para a camada que já existe — mover a regra duplicada para o método que já estava escrito e ninguém chamava, não criar pastas novas.

Não imponha o mesmo esqueleto aos dois. Estrutura que não reflete responsabilidade real é exatamente o anti-pattern que esta skill detecta.
