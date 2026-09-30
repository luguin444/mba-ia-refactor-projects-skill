# Template do relatório de auditoria

Usado na **Fase 2**. Formato fixo — não improvise seções nem reordene.

## Estrutura

````markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project:      <nome do diretório>
Stack:        <linguagem + framework + versão>
Dependencies: <as relevantes>
Domain:       <domínio em uma linha>
Architecture: <classificação da Fase 1 + justificativa em uma linha>
Files:        <N> analyzed | ~<N> lines of code
Routes:       <N> endpoints
DB tables:    <lista>
Date:         <YYYY-MM-DD>

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [CRITICAL] <Nome do anti-pattern> (AP-NN)
**File:** `caminho/arquivo.ext:linha` (ou `:início-fim`, ou lista de linhas)
**Description:** <o que está acontecendo — máximo 2 frases>
**Impact:** <por que dói: segurança, manutenção ou performance — 1 frase>
**Recommendation:** <a transformação> (→ PB-NN)

### [CRITICAL] <próximo>
...

### [HIGH] ...
### [MEDIUM] ...
### [LOW] ...

## Contract Exceptions
<Alterações de contrato que a Fase 3 vai aplicar, uma por linha, com arquivo e motivo.>
<"Nenhuma" se não houver.>

## Requires Product Decision
<Findings que NÃO serão corrigidos porque a correção quebraria o contrato.>
<"Nenhum" se não houver.>

================================
Total: <N> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
````

## Regras

**O cabeçalho carrega o bloco inteiro da Fase 1.** `Domain`, `Architecture`, `Routes` e `DB tables` não ficam só no stdout: a classificação de arquitetura é o julgamento que determina a estratégia da Fase 3, e um relatório sem ela não permite a ninguém — nem a você numa sessão futura — verificar se a estratégia aplicada foi a certa. Copie os valores exatos que a Fase 1 imprimiu, sem reescrever.

**Ordenação.** CRITICAL → HIGH → MEDIUM → LOW. Dentro de cada nível, o de maior impacto primeiro.

**Agrupamento.** Um anti-pattern com N ocorrências é **um** finding, listando as linhas — não N findings. Quando passar de dez linhas, cite as principais e escreva o total: `models.py:28, 47-50, 68, 92 (+11 ocorrências)`.

**Linhas.** Sempre verificadas abrindo o arquivo. Intervalo quando o achado é o bloco inteiro (`models.py:1-314` para uma God class), linha exata quando é pontual.

**Descrição.** Máximo duas frases, no que é observável. `"SECRET_KEY fixa no código e devolvida pelo /health"` serve; `"código ruim"` não.

**Impacto.** O que acontece se não corrigir, em termos concretos. `"Um GET /usuarios anônimo devolve a senha de todos os usuários"` serve; `"prejudica a segurança"` não.

**Recomendação.** A transformação, com a referência do playbook. Se for exceção de contrato, diga.

**Contract Exceptions.** Antes do gate, nominalmente. O humano confirma sabendo o que muda:

```
- app.py:59-78 — endpoint POST /admin/query removido (AP-02)
- models/user.py:21 — campo `password` removido de User.to_dict() (AP-04)
- src/AppManager.js:45 — log com número de cartão e chave removido (AP-04)
- rotas que passam a exigir credencial (AP-07), anônimo 200 → 401:
    POST/PUT/DELETE /produtos · PUT /pedidos/<id>/status · GET /usuarios
    GET /pedidos · GET /pedidos/usuario/<id>
  permanecem públicas, deliberadamente:
    / · /health · GET /produtos · GET /produtos/<id> · POST /usuarios · POST /login
    (cadastro e login são o único caminho de entrada do usuário no sistema)
```

Quando houver mudança de autenticação, a lista é obrigatória com **uma linha por rota**, contendo o nível e o motivo — nunca rotas agrupadas sob um nível comum. Agrupar parece completo e esconde a diferença entre ler dado próprio, dado compartilhado e dado de terceiro; ver a tabela de escopo do PB-24. Escopo implícito é o que faz o humano aprovar uma coisa e receber outra.

### Raio de alcance: enumere, não amostre

Correção de validação ou de parsing raramente atinge uma rota só. Trocar a leitura do corpo por uma versão tolerante, centralizar tratamento de erro, ou adicionar uma constraint **muda o status de toda rota que passa por aquele caminho** — inclusive as que você não testou.

Antes do gate, para cada correção que altera status code ou corpo, percorra **todas** as rotas que usam o mecanismo alterado e liste cada uma. Não escreva "no login e no status" quando a mudança está na função que todas as rotas chamam.

O teste: se depois de aplicar você descobrir uma rota afetada que não estava na lista, a declaração estava incompleta — e o humano aprovou um escopo menor do que recebeu. Isso é a mesma falha da regra 7, só na direção contrária.

Quando não der para enumerar com certeza, diga o mecanismo e o alcance esperado: *"todas as rotas que leem corpo JSON"*, em vez de listar duas e esperar que sejam as únicas.

**Requires Product Decision.** Reservado ao que **não é dedutível do código** — ver a seção correspondente no `SKILL.md`. Autenticação, token previsível e privilégio vindo do cliente **não** entram aqui: são corrigidos. Se esta seção contiver um finding cuja própria recomendação já descreve em detalhe o que fazer, a classificação está errada.

**O gate é a última linha.** Depois dele, nada. Não antecipe a estrutura nova, não comece a refatorar, não sugira que já começou.

## Onde salvar

`<raiz-do-git>/reports/audit-<nome-do-diretório-do-projeto>.md`, onde a raiz do git é a saída de `git rev-parse --show-toplevel`.

O projeto auditado pode ser um subdiretório do repositório — nesse caso o relatório vai para a raiz, **não** para dentro do projeto. Se não houver repositório git, use o diretório corrente e informe.

Escrever este arquivo é permitido antes do gate — ele não é código do projeto. Qualquer arquivo **dentro** do projeto auditado só depois do "y".
