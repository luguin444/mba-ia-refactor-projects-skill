# Catálogo de anti-patterns

Usado na **Fase 2**. 32 entradas.

Cada entrada descreve o anti-pattern por **sinal observável**, não por sintaxe de uma linguagem. A tabela de manifestações mostra como o mesmo sinal aparece em cada stack. Suportar uma stack nova significa acrescentar uma linha — o sinal e a severidade não mudam.

Regra de uso: procure o **sinal**. Se ele estiver presente, o finding existe, independentemente de quão sofisticado o código em volta pareça.

---

## CRITICAL

### AP-01 — Injeção de SQL por concatenação
**Sinal:** query montada por concatenação, interpolação ou template string contendo valor vindo de request, argumento de função pública ou parâmetro de rota.
**Manifestações:** Python `"SELECT * FROM t WHERE id = " + str(id)`, f-string em `cursor.execute` · JS `` `SELECT * FROM t WHERE id = ${id}` `` · qualquer stack: `WHERE 1=1` seguido de `query +=`.
**Severidade:** CRITICAL sempre. Não rebaixe para MEDIUM só porque "usar ORM facilitaria" — o achado é a injeção, não a ergonomia.
**Atenção:** o mesmo arquivo pode usar placeholders corretamente em um ponto e concatenar em outro. Verifique todas as queries.
**Transformação:** → PB-01

### AP-02 — Endpoint perigoso exposto sem proteção
**Sinal:** rota que executa entrada do cliente como código ou query, ou que apaga dados em massa, sem verificação de identidade.
**Manifestações:** `POST /admin/query` recebendo SQL no body · `POST /admin/reset-db` · `eval`/`exec` sobre o request · endpoint que dispara migração ou seed.
**Por que CRITICAL:** a severidade se ancora no pior caso — dump de credenciais ou `DROP TABLE`, não na lentidão de uma query pesada.
**Transformação:** → PB-13 (remoção; é exceção de contrato declarada)

### AP-03 — Segredo hardcoded
**Sinal:** literal com aparência de credencial atribuído a constante, campo de config ou argumento de conexão.
**Onde procurar:** código-fonte · arquivos de config versionados · manifesto.
**Manifestações:** Python `app.config['SECRET_KEY'] = '...'`, `smtplib.login('user', 'senha')` · JS `const config = { dbPass: '...', apiKey: 'pk_live_...' }` · geral: strings com prefixo `sk_`, `pk_`, `AKIA`, `ghp_`, `xoxb-`, ou chaves nomeadas `password`, `secret`, `token`, `key`.
**Transformação:** → PB-02

### AP-04 — Dado sensível em log ou resposta
**Sinal:** credencial, hash, número de cartão, token ou chave aparecendo em saída de log ou no corpo de uma resposta HTTP.
**Onde procurar:** chamadas de log · funções de serialização (`to_dict`, `toJSON`, `serialize`) · literais dentro de `jsonify`/`res.json`.
**Manifestações:** `console.log(\`cartão ${cc} chave ${apiKey}\`)` · `to_dict()` incluindo o campo `password` · endpoint de health devolvendo `secret_key`.
**Por que CRITICAL:** transforma má prática interna em vazamento externo. Um serializer que inclui a senha faz de toda rota que o usa um endpoint de exfiltração.
**Transformação:** → PB-14 (exceção de contrato declarada)

### AP-05 — Hash de senha ausente, caseiro ou obsoleto
**Sinal:** senha armazenada em claro; **ou** algoritmo implementado à mão; **ou** função de hash de propósito geral usada para senha.
**Manifestações:** comparação direta `senha == row['senha']` · `hashlib.md5(pwd)`, `sha1`, `sha256` sem derivação · loop próprio concatenando base64 · `crypto.createHash` para senha.
**Regra:** não avalie a qualidade do algoritmo. Implementação própria é o sinal, por si só. Custo computacional alto não é segurança — um loop de 10.000 iterações que trunca o resultado em 10 caracteres tem entropia quase nula e foi escrito para *parecer* key stretching.
**Transformação:** → PB-05

### AP-06 — God class / God module
**Sinal:** um arquivo ou classe concentra três ou mais das quatro responsabilidades (conexão, query, regra de negócio, HTTP), ou atende três ou mais domínios distintos.
**Manifestações:** classe chamada `Manager`, `Helper`, `Service` sem qualificador de domínio · módulo com funções de 4 entidades diferentes · arquivo de rota entre os maiores do projeto.
**Transformação:** → PB-03

### AP-07 — Autenticação ausente ou simulada
**Sinal:** rotas que alteram ou expõem dados sem verificação de identidade; **ou** um endpoint de login que não emite credencial verificável; **ou** token previsível ou não assinado.
**Manifestações:** `'token': 'fake-jwt-token-' + str(user.id)` · login que valida a senha e devolve o usuário sem sessão · nenhuma rota lendo header de autorização · cadastro público que aceita `role` do body (escalonamento de privilégio).
**Não corrigir automaticamente.** Marque `REQUER DECISÃO DE PRODUTO` — implementar auth faria toda rota responder 401 e quebraria o contrato. Descreva a transformação sem aplicá-la.

### AP-08 — Modo debug habilitado em bind público
**Sinal:** flag de debug ou verbose ligada junto com bind em interface não-local.
**Manifestações:** `app.run(debug=True, host='0.0.0.0')` · `DEBUG = True` em config versionada · `NODE_ENV` ausente com stack trace na resposta.
**Por que CRITICAL:** o console interativo do Werkzeug exposto na rede é execução remota de código, não inconveniência.
**Transformação:** → PB-02

---

## HIGH

### AP-09 — Regra de negócio na camada errada
**Sinal:** cálculo de domínio, faixa de valor, transição de estado ou validação de regra dentro de um handler HTTP **ou** dentro de uma função de acesso a dados.
**Manifestações:** controller conferindo estoque · repositório calculando desconto por faixa de faturamento · rota decidindo se uma entidade está atrasada.
**Atenção:** a violação acontece nas duas direções. Aponte a camada exata — errar isso invalida o finding.
**Transformação:** → PB-04

### AP-10 — Escrita multi-entidade sem transação
**Sinal:** duas ou mais escritas relacionadas sem transação explícita, ou sem rollback no caminho de erro.
**Manifestações:** inserir pedido, inserir itens e debitar estoque com um único commit ao final · escritas encadeadas em callbacks sem `BEGIN` · `except` que não chama rollback.
**Por que HIGH:** falha no meio deixa estado inconsistente — matrícula sem pagamento, estoque debitado sem venda.
**Transformação:** → PB-07

### AP-11 — Estado global mutável
**Sinal:** variável de módulo mutável compartilhada entre requisições.
**Manifestações:** singleton de conexão em variável global · cache em objeto de módulo que cresce sem limite · contador exportado do módulo.
**Atenção:** em JS, exportar um número ou string exporta **por valor** — quem importa recebe uma cópia congelada e nunca vê atualização. É bug latente, não só acoplamento.
**Transformação:** → PB-04

### AP-12 — Efeito colateral escondido no fluxo
**Sinal:** operação não anunciada pelo nome nem pelo contrato da rota.
**Manifestações:** checkout que cria conta de usuário silenciosamente, com senha default quando o campo vem vazio · controller disparando e-mail, SMS e push · getter que grava em log de auditoria.
**Transformação:** → PB-04

### AP-13 — Acesso a dados sem camada própria
**Sinal:** rota ou controller importando driver de banco, ORM ou montando query.
**Manifestações:** `from database import get_db` dentro do módulo de rotas · `this.db.run(...)` dentro do handler · `Model.query.filter(...)` no controller.
**Transformação:** → PB-03

### AP-14 — Camada decorativa
**Sinal:** símbolo definido na camada correta cuja contagem de referências no projeto é **1** — a própria definição — enquanto lógica equivalente aparece duplicada em outra camada.
**Como detectar:** para cada método público de model/service/helper, conte as ocorrências do nome no projeto. Contagem 1 = nunca chamado. Depois procure a lógica dele copiada nas rotas ou controllers.
**Manifestações:** `Task.is_overdue()` definido e a mesma condição copiada inline em cinco rotas · função de validação de payload escrita e nunca usada enquanto os handlers revalidam à mão · classe de serviço que ninguém instancia.
**Por que HIGH:** é pior que ausência de camada. A estrutura desarma a suspeita de quem lê rápido, e as cópias divergem entre si sem ninguém perceber.
**Transformação:** → PB-15

### AP-15 — Erro engolido silenciosamente
**Sinal:** caminho de erro que não trata, não registra e não propaga.
**Manifestações:** callback que recebe `err` e nunca o checa · `except:` nu · `catch {}` vazio · resposta 200 num caminho que falhou.
**Atenção:** `except:` sem tipo captura também `KeyboardInterrupt` e `SystemExit`.
**Transformação:** → PB-08

### AP-16 — Controle de fluxo assíncrono manual
**Sinal:** aninhamento profundo de callbacks, ou contadores decrementados à mão para decidir quando responder.
**Manifestações:** pirâmide de 4+ níveis · `let pending = items.length` com `pending--` dentro de cada callback · `const self = this` convivendo com arrow functions.
**Por que HIGH:** se um callback falha, o contador nunca zera e a requisição fica pendurada até o timeout do cliente.
**Transformação:** → PB-10

---

## MEDIUM

### AP-17 — Queries N+1
**Sinal:** consulta ao banco dentro de laço, iterador ou callback que já percorre um resultado anterior.
**Manifestações:** `for` sobre pedidos com uma query de itens por pedido · `forEach` com `db.get` dentro · contagem por linha de uma listagem · relacionamento do ORM declarado e ignorado em favor de busca manual.
**Dica:** variáveis numeradas (`cursor2`, `cursor3`) são sintoma quase certo.
**Transformação:** → PB-06

### AP-18 — Resposta não-determinística
**Sinal:** ordem ou conteúdo do corpo variando entre chamadas idênticas.
**Manifestações:** array montado por `push` dentro de callbacks concorrentes · listagem sem `ORDER BY` · agregação dependente de ordem de conclusão.
**Como confirmar:** chame o endpoint 5 a 10 vezes e compare. É o único anti-pattern deste catálogo que exige execução para ser provado.
**Por que importa:** quebra clientes que indexam o array, e torna qualquer diff de contrato inútil sem normalização.
**Transformação:** → PB-16

### AP-19 — API ou dependência deprecated
**Sinal:** uso de API marcada como obsoleta pela linguagem ou framework, ou dependência marcada como deprecated pelo registry.
**Onde procurar:** os três lugares — código-fonte, manifesto, lockfile.
**Manifestações:**

| Stack | Deprecated | Equivalente moderno |
|---|---|---|
| Python 3.12+ | `datetime.utcnow()` | `datetime.now(timezone.utc)` |
| SQLAlchemy 2.x | `Model.query`, `Query.get()` | `db.session.get(Model, id)`, `select()` |
| Flask 2.3+ | `@app.before_first_request` | inicialização no factory |
| Node | `new Buffer()`, `url.parse()`, `crypto.createCipher` | `Buffer.from()`, `new URL()`, `createCipheriv` |
| Node 22+ | pacote `sqlite3` nativo com deps podres | `node:sqlite`, `better-sqlite3` |
| npm | pacote com campo `deprecated` no lock | versão corrente ou substituto |

**Detector mais barato:** rode a aplicação uma vez e leia os `DeprecationWarning` do boot; rode o install e leia os `npm warn deprecated`.
**Transformação:** → PB-11

### AP-20 — Duplicação entre handlers irmãos
**Sinal:** dois handlers do mesmo recurso com blocos equivalentes, tipicamente criar e atualizar.
**Como confirmar a severidade:** compare os blocos. Se já divergiram, o finding tem impacto demonstrável — cite qual regra existe num e falta no outro.
**Transformação:** → PB-12

### AP-21 — Tratamento de erro repetido sem handler central
**Sinal:** o mesmo bloco de captura repetido em cada handler, e/ou mensagem crua da exceção devolvida ao cliente.
**Manifestações:** `except Exception as e: return jsonify({'erro': str(e)}), 500` em 17 funções · ausência de middleware de erro no framework · respostas de erro em texto puro enquanto o sucesso é JSON.
**Transformação:** → PB-08

### AP-22 — Contrato de resposta sem serializer único
**Sinal:** corpo da resposta montado por literal em cada ponto, sem fonte única de verdade.
**Manifestações:** o mesmo recurso com formatos diferentes dependendo da rota · dicionário montado campo a campo em vários lugares · serializer existindo e sendo ignorado por parte das rotas (ver AP-14).
**Transformação:** → PB-12

### AP-23 — Schema sem constraints de integridade
**Sinal:** DDL ou definição de model sem `NOT NULL`, `UNIQUE` ou `FOREIGN KEY` onde o domínio exige.
**Manifestações:** coluna de e-mail sem `UNIQUE` combinada com verifica-e-insere na aplicação (race de duplicata) · chave estrangeira ausente permitindo registro órfão.
**Transformação:** → PB-17

### AP-24 — Limpeza em cascata manual
**Sinal:** remoção de entidade pai percorrendo filhos em laço, ou não tratando os filhos.
**Manifestações:** `for t in tasks: session.delete(t)` antes de deletar o usuário · `DELETE FROM users` deixando matrículas e pagamentos apontando para id inexistente.
**Transformação:** → PB-17

### AP-25 — Bootstrap acoplado à inicialização
**Sinal:** criação de schema ou inserção de dados de exemplo disparada por import, por obtenção de conexão, ou pelo boot.
**Manifestações:** seeds dentro de `get_db()` · `db.create_all()` em tempo de import · DDL no construtor.
**Por que importa:** dados fictícios entram em qualquer ambiente que importar o módulo, e não há versionamento de schema.
**Transformação:** → PB-18

### AP-26 — CORS irrestrito
**Sinal:** CORS habilitado sem restringir origem.
**Manifestações:** `CORS(app)` · `app.use(cors())` · header `Access-Control-Allow-Origin: *` fixo.
**Atenção:** presença de CORS configurado não é defesa. Liberado para tudo é o achado.
**Transformação:** → PB-02

---

## LOW

### AP-27 — Magic numbers e literais repetidos
**Sinal:** valor de domínio cravado no meio da lógica, ou lista de valores válidos repetida.
**Manifestações:** faixas de desconto `10000 / 5000 / 1000` com multiplicadores soltos · lista de status válidos repetida em cinco arquivos · limites de tamanho literais.
**Agrava:** se existe uma constante definida para isso e os handlers repetem o literal mesmo assim, some ao AP-14.
**Transformação:** → PB-19

### AP-28 — `print` como logging
**Sinal:** saída de diagnóstico por impressão direta, sem nível nem destino configurável.
**Manifestações:** `print(...)` / `console.log(...)` em caminho de erro ou auditoria · função de log própria que só imprime.
**Transformação:** → PB-20

### AP-29 — Nomes não descritivos
**Sinal:** identificador de uma letra fora de laço curto, numeração incremental, ou abreviação no contrato público.
**Manifestações:** `u`, `e`, `p`, `cc` para dados de negócio · `cursor2`, `cursor3` · campos de API `usr`, `eml`, `pwd`, `c_id`.
**Atenção:** `e` para um valor de negócio colide com a convenção de `error`.
**Transformação:** → PB-19

### AP-30 — Código e imports mortos
**Sinal:** símbolo cuja contagem de referências no projeto é 1, ou import nunca usado no arquivo.
**Diferença para AP-14:** aqui é só código morto. Se a lógica equivalente estiver duplicada em outra camada, é AP-14 e a severidade sobe para HIGH.
**Transformação:** → PB-21

### AP-31 — Ausência de paginação
**Sinal:** listagem carregando a tabela inteira, sem limite nem cursor.
**Manifestações:** `SELECT *` sem `LIMIT` · `Model.query.all()` seguido de serialização de tudo.
**Transformação:** → PB-22

### AP-32 — Verbosidade evitável
**Sinal:** construção que expressa em muitas linhas o que a linguagem expressa em uma.
**Manifestações:** `if cond: return True else: return False` · `type(x) == list` em vez de `isinstance` · concatenação com conversão explícita em vez de interpolação · `let` para valor nunca reatribuído.
**Transformação:** → PB-19
