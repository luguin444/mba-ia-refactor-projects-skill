# Template do relatório de auditoria

Usado na **Fase 2**. Formato fixo — não improvise seções nem reordene.

## Estrutura

````markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome do diretório>
Stack:   <linguagem + framework + versão>
Files:   <N> analyzed | ~<N> lines of code
Date:    <YYYY-MM-DD>

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
```

**Requires Product Decision.** Findings cuja correção exigiria mudar o comportamento da API — tipicamente AP-07. Descreva a transformação e diga por que não foi aplicada.

**O gate é a última linha.** Depois dele, nada. Não antecipe a estrutura nova, não comece a refatorar, não sugira que já começou.

## Onde salvar

`<raiz-do-git>/reports/audit-<nome-do-diretório-do-projeto>.md`, onde a raiz do git é a saída de `git rev-parse --show-toplevel`.

O projeto auditado pode ser um subdiretório do repositório — nesse caso o relatório vai para a raiz, **não** para dentro do projeto. Se não houver repositório git, use o diretório corrente e informe.

Escrever este arquivo é permitido antes do gate — ele não é código do projeto. Qualquer arquivo **dentro** do projeto auditado só depois do "y".
