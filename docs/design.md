# Design — Skill `refactor-arch`

**Data:** 2026-09-21
**Contexto:** Desafio MBA Full Cycle — criar uma skill que analisa, audita e refatora projetos legados para MVC, de forma agnóstica de tecnologia.

## 1. Objetivo

Uma skill do Claude Code, invocada por `/refactor-arch`, que executa três fases sequenciais sobre o projeto no diretório corrente:

1. **Análise** — detecta stack e mapeia a arquitetura real.
2. **Auditoria** — cruza o código contra um catálogo de anti-patterns, emite relatório e **pausa**.
3. **Refatoração** — reestrutura para MVC e prova, por diff de contrato, que nada quebrou.

Ela precisa funcionar nos três projetos do repositório: dois Python/Flask com níveis de organização opostos e um Node.js/Express.

## 2. Insumo: a análise manual

A análise manual dos três projetos (em `analise-manual.md`) produziu **76 findings** e é a fonte de verdade do catálogo. Três conclusões dela viraram requisitos duros deste design:

**2.1. Estrutura de diretórios não indica arquitetura.** O `task-manager-api` tem `models/`, `routes/`, `services/`, `utils/` e Blueprints. Mesmo assim, `Task.is_overdue()` está definido e nunca é chamado, enquanto a regra está copiada inline em cinco rotas; `process_task_data()` e `NotificationService` são código morto. Doze símbolos do projeto aparecem exatamente uma vez — na própria definição. Uma heurística baseada na árvore de arquivos concluiria "já é MVC" e falharia exatamente no projeto que o desafio plantou para testar isso.

**2.2. APIs deprecated não vivem só no código-fonte.** O `ecommerce-api-legacy` tem o `src/` limpo de APIs obsoletas, mas o `package-lock.json` carrega sete pacotes marcados como deprecated pelo npm, arrastados por `sqlite3@5.1.6`. A detecção precisa varrer **código-fonte, manifesto e lockfile**.

**2.3. Código de segurança presente pode ser pior que ausente.** O projeto 3 tem hash de senha — MD5 sem salt — e devolve esse hash em quatro endpoints públicos. Ter "criptografia" desarma a suspeita de quem lê rápido. O catálogo precisa detectar *criptografia própria ou obsoleta* como sinal, sem tentar julgar qualidade criptográfica.

## 3. Decisões de escopo

### 3.1. A Fase 3 corrige sem alterar o contrato HTTP

O enunciado pede duas coisas que colidem: *"eliminando os problemas encontrados"* e *"os endpoints originais continuam respondendo corretamente"*. Corrigir os CRITICALs de autenticação faria toda rota responder 401 e quebraria o critério de aceite obrigatório nos três projetos.

**Regra:** a Fase 3 corrige tudo que é invisível ao cliente HTTP — query parametrizada, hash moderno, segredos em `.env`, N+1 resolvido, camadas separadas, erro centralizado. **Não adiciona autenticação nova.** Os findings de autenticação permanecem no relatório, marcados como `REQUER DECISÃO DE PRODUTO`, com a transformação descrita e não aplicada.

### 3.2. Exceções declaradas ao contrato

Três classes de correção mudam o contrato por definição, porque o elemento exposto *é* o achado:

| Exceção | Exemplo | Regra |
|---|---|---|
| Endpoint que só existe como vulnerabilidade | `/admin/query`, `/admin/reset-db` (projeto 1) | Removido |
| Campo sensível no corpo da resposta | `password` no `to_dict()` (projeto 3), `senha` em `GET /usuarios` (projeto 1) | Campo removido, resto do objeto intacto |
| Dado sensível em log | PAN do cartão e chave `pk_live_` (projeto 2) | Log removido ou mascarado |

Cada exceção aplicada precisa ser **listada nominalmente no relatório da Fase 2**, antes do gate. O humano confirma sabendo exatamente o que vai mudar de contrato. O diff da Fase 3 trata essas divergências como esperadas; qualquer outra é falha.

### 3.3. A validação é baseline + diff de contrato

Antes de tocar em qualquer arquivo, a Fase 3 sobe a aplicação original, dispara todos os endpoints e grava status e corpo em `.refactor-arch/baseline.json`. Depois de refatorar, sobe de novo, redispara e compara. Divergência não declarada = falha.

Se a aplicação original não sobe, a Fase 3 **aborta**: sem baseline não há como provar nada, e refatorar às cegas é pior que não refatorar.

## 4. Arquitetura da skill

```
.claude/skills/refactor-arch/
├── SKILL.md                      # orquestra as 3 fases e o gate
└── references/
    ├── project-analysis.md       # heurísticas de detecção (Fase 1)
    ├── antipattern-catalog.md    # catálogo de anti-patterns (Fase 2)
    ├── report-template.md        # formato do relatório (Fase 2)
    ├── mvc-guidelines.md         # camadas alvo (Fase 3)
    ├── refactoring-playbook.md   # transformações antes/depois (Fase 3)
    └── contract-baseline.md      # captura e diff do contrato (Fase 3)
```

O `SKILL.md` é fino: descreve o fluxo, o gate e quando carregar cada referência. Cada fase lê **apenas** os arquivos de que precisa — a Fase 1 nunca carrega o playbook. É a mesma disciplina de separação que a skill impõe ao código auditado.

As cinco áreas de conhecimento exigidas pelo enunciado mapeiam assim: análise de projeto → `project-analysis.md`; catálogo → `antipattern-catalog.md`; template → `report-template.md`; guidelines → `mvc-guidelines.md`; playbook → `refactoring-playbook.md`. O `contract-baseline.md` é adicional, servindo à decisão 3.3.

### 4.1. O mecanismo de agnosticismo

Cada entrada do catálogo descreve o anti-pattern por **sinal observável**, não por sintaxe de linguagem, e traz uma tabela de manifestações:

```markdown
### AP-04 — Segredo hardcoded
Severidade: CRITICAL
Sinal: literal com aparência de credencial atribuído a constante,
       campo de config ou argumento de conexão
Onde procurar: código-fonte · manifesto · lockfile
Manifestações:
  Python  app.config['SECRET_KEY'] = '...'  ·  smtplib login('user', 'senha')
  Node    const config = { dbPass: '...', paymentGatewayKey: 'pk_live_...' }
  Geral   string com prefixo sk_ / pk_ / AKIA / ghp_ / xoxb-
Transformação: → PB-02
```

Adicionar uma stack nova significa acrescentar uma linha na tabela de manifestações, não criar um arquivo. O sinal e a severidade não mudam.

## 5. Fase 1 — Análise

**Saída:** bloco `PHASE 1: PROJECT ANALYSIS` com linguagem, framework e versão, dependências, domínio, arquitetura, contagem de arquivos e tabelas do banco.

**Heurísticas:**

| Alvo | Sinal |
|---|---|
| Linguagem | manifesto presente (`requirements.txt`, `package.json`, `go.mod`, `Gemfile`, `pom.xml`) + extensão predominante |
| Framework e versão | dependências do manifesto cruzadas com os imports do entry point |
| Entry point | campo `main` do manifesto, `if __name__ == '__main__'`, ou o arquivo que instancia o servidor |
| Banco | driver no manifesto + string de conexão + DDL no código |
| Tabelas | `CREATE TABLE` no código-fonte ou classes de model do ORM |
| Domínio | nomes de tabela, de rota e de entidade |

**Contagem de arquivos:** conta apenas fonte do projeto. Exclui dependências instaladas, lockfiles, a própria skill e artefatos de build. A contagem tem que bater com a realidade — é item do checklist de validação.

**Mapeamento de arquitetura real** — a parte que não pode olhar a árvore de diretórios. A skill localiza quem exerce cada uma de quatro responsabilidades:

1. quem abre conexão ou sessão de banco;
2. quem monta query ou invoca o ORM;
3. quem decide regra de negócio (cálculo, condição de domínio, transição de estado);
4. quem registra rota e trata HTTP.

Se as quatro colidem em um arquivo, é monolito. Se estão distribuídas em pastas mas a responsabilidade vaza — regra de negócio dentro da rota, query dentro do controller —, a arquitetura é **camadas decorativas**, e a Fase 1 precisa dizer isso com essas palavras, não "já segue MVC".

## 6. Fase 2 — Auditoria

Cruza o código contra o catálogo e emite o relatório no formato de `report-template.md`.

**Cada finding traz:** severidade, nome do anti-pattern, `arquivo:linha` exatos, descrição em no máximo duas frases, impacto, e a transformação recomendada (referência ao playbook).

**Ordenação:** CRITICAL → HIGH → MEDIUM → LOW. Cabeçalho com a contagem por severidade e o total.

**Seção obrigatória antes do gate:** as exceções de contrato da seção 3.2 que serão aplicadas, nominalmente, e os findings marcados `REQUER DECISÃO DE PRODUTO` que **não** serão corrigidos.

**O gate:** a fase termina perguntando `Proceed with refactoring (Phase 3)? [y/n]` e **não modifica nenhum arquivo** até receber confirmação afirmativa explícita. Escrever o relatório em `reports/` é permitido antes do gate; tocar em código do projeto, não.

## 7. Fase 3 — Refatoração

Ordem de execução:

**7.1. Captura do baseline.** Enumera os endpoints a partir das rotas mapeadas na Fase 1, mais os exemplos de `api.http` quando existirem. Reseta o banco ao estado de seed, sobe a aplicação original, dispara cada endpoint e grava status e corpo em `.refactor-arch/baseline.json`. Endpoints destrutivos são disparados por último. Se o boot falhar, aborta.

**7.2. Estrutura alvo.** Cria o esqueleto descrito em `mvc-guidelines.md` (seção 8).

**7.3. Transformações.** Aplica o playbook em ordem de dependência: config → camada de dados → regra de negócio → controllers → rotas → middlewares de erro → composition root.

**7.4. Verificação.** Reseta o banco ao mesmo estado de seed, sobe a aplicação refatorada, redispara os mesmos endpoints e faz diff contra o baseline. Campos declaradamente voláteis são normalizados (seção 9). Divergência não declarada = falha, e a skill corrige ou reverte.

**7.5. Relatório final.** Estrutura nova, resultado do diff endpoint a endpoint, e a lista de anti-patterns eliminados versus remanescentes.

## 8. Estrutura MVC alvo

```
src/
├── config/          # configuração lida de ambiente, zero literal sensível
├── models/          # entidade e persistência, um módulo por domínio
├── controllers/     # orquestra request → regra → resposta
├── views/ (routes/) # apenas registro de rota e binding para controller
├── middlewares/     # erro centralizado, CORS, logging
└── app.(py|js)      # composition root
```

`services/` e `repositories/` são criados **quando o volume de regra de negócio justifica** — o relatório de vendas do projeto 1 e o `summary_report` do projeto 3 justificam; o projeto 2 provavelmente não. A skill se adapta ao contexto em vez de impor o mesmo esqueleto aos três.

Regras de camada, verificáveis:

- `views/routes` não importa driver de banco nem ORM;
- `controllers` não monta query nem string SQL;
- `models` não importa nada de HTTP;
- nenhum literal sensível fora de `config/`;
- toda resposta de erro passa pelo middleware central.

## 9. Diff de contrato

**Normalização.** Só campos declaradamente voláteis são normalizados, e a lista fica registrada no baseline: timestamps (`created_at`, `updated_at`, `generated_at`, `timestamp`), e valores derivados de id auto-increment quando a ordem de inserção não é determinística. Todo o resto compara exato.

**Paridade de estado.** As duas capturas precisam partir do mesmo estado de banco. Por projeto:

| Projeto | Reset |
|---|---|
| `code-smells-project` | apagar `loja.db` — o seed roda no primeiro `get_db()` |
| `ecommerce-api-legacy` | reiniciar o processo — banco é `:memory:` e semeia no boot |
| `task-manager-api` | apagar `tasks.db` e rodar `seed.py` |

**Saída do diff:** uma linha por endpoint com método, caminho, status e veredito. Divergências mostram o campo e os dois valores.

## 10. Catálogo de anti-patterns

Mínimo exigido: 8, com severidades distribuídas e detecção de APIs deprecated. O catálogo terá cerca de 20 entradas, derivadas dos 76 findings da análise manual.

**CRITICAL** — SQL injection por concatenação; execução de SQL ou código arbitrário exposta por endpoint; segredo hardcoded; dado sensível em log ou resposta; hash de senha ausente, próprio ou obsoleto; God class/module; autenticação ausente ou simulada; debug habilitado em bind público.

**HIGH** — regra de negócio na camada errada; escrita multi-entidade sem transação; estado global mutável; efeito colateral escondido no fluxo; **camada decorativa**; controle de fluxo assíncrono manual; erro engolido silenciosamente.

**MEDIUM** — N+1 queries; **API ou dependência deprecated**; duplicação entre handlers irmãos; tratamento de erro repetido sem handler central; contrato de resposta sem serializer único; schema sem constraints; limpeza em cascata manual deixando órfãos; bootstrap acoplado à inicialização; CORS irrestrito.

**LOW** — magic numbers e literais repetidos; `print` como logging; nomes não descritivos; código e imports mortos; ausência de paginação.

**Camada decorativa** é entrada nova, não presente em catálogos padrão de code smells. Sinal: símbolo definido cuja contagem de referências no projeto é 1, combinado com lógica equivalente duplicada em outra camada. Foi o achado central do projeto 3.

## 11. Playbook de refatoração

Mínimo exigido: 8 transformações com exemplos antes/depois. Serão cerca de 12, cada uma referenciada por um ou mais anti-patterns do catálogo:

PB-01 concatenação → query parametrizada · PB-02 literal → módulo de config e `.env` · PB-03 God module → módulos por domínio · PB-04 regra de negócio no repositório ou no controller → camada própria · PB-05 hash próprio ou MD5 → algoritmo de derivação com salt · PB-06 N+1 → JOIN ou eager loading · PB-07 escritas soltas → transação com rollback · PB-08 `try/except` repetido → middleware de erro central · PB-09 rotas manuais → agrupamento por domínio (Blueprint, Router) · PB-10 callback aninhado → async/await · PB-11 API deprecated → equivalente moderno · PB-12 dict montado à mão → serializer único.

Cada entrada traz o exemplo nas duas stacks quando a transformação difere entre elas.

## 12. Distribuição da skill

A cópia canônica vive em `code-smells-project/.claude/skills/refactor-arch/`. Um `rsync` replica para os outros dois projetos antes de cada execução, evitando que as três cópias divirjam ao longo das iterações. O comando entra na seção "Como Executar" do README.

## 13. Entregáveis e mapeamento

| Entregável | Onde |
|---|---|
| Skill completa | `.claude/skills/refactor-arch/` nos 3 projetos |
| Código refatorado | os 3 projetos, commitado |
| Relatórios da Fase 2 | `reports/audit-project-{1,2,3}.md` |
| Análise manual (seção A) | de `analise-manual.md` para o `README.md` |
| Seções B, C, D | `README.md` |

## 14. Riscos

**O diff acusa divergência legítima.** Refatorar pode corrigir um bug que o baseline capturou como comportamento — por exemplo, `PUT /tasks/<id>` estourando 500 com prioridade não numérica enquanto o `POST` devolve 400. Tratamento: a divergência é apresentada ao humano com os dois valores, e a correção de bug é aceita como exceção declarada, não silenciada.

**Endpoints destrutivos no baseline.** `/admin/reset-db` e os `DELETE` alteram o estado que as capturas seguintes leem. Tratamento: ordem fixa de disparo, destrutivos por último, e reset completo entre as duas capturas.

**O projeto 2 não tem `.gitignore` para `node_modules`.** A contagem de arquivos e as buscas precisam excluí-lo explicitamente, ou a Fase 1 reporta milhares de arquivos.

**Contaminação de contexto na validação.** Executar a skill na mesma sessão em que o código foi analisado não prova que ela funciona — o agente já sabe as respostas. As três execuções precisam acontecer em sessões limpas.
