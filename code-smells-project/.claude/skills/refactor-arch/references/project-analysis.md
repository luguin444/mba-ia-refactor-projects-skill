# Análise de projeto — heurísticas de detecção

Usado na **Fase 1**. Objetivo: descobrir a stack e, principalmente, **onde a responsabilidade realmente mora**.

## 1. Linguagem e gerenciador

Procure o manifesto na raiz. Ele decide, não a contagem de extensões — um projeto Python com um `build.js` continua sendo Python.

| Manifesto | Linguagem | Lockfile |
|---|---|---|
| `requirements.txt`, `pyproject.toml`, `Pipfile` | Python | `poetry.lock`, `Pipfile.lock` |
| `package.json` | JavaScript / TypeScript | `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml` |
| `go.mod` | Go | `go.sum` |
| `Gemfile` | Ruby | `Gemfile.lock` |
| `pom.xml`, `build.gradle` | Java / Kotlin | — |
| `composer.json` | PHP | `composer.lock` |
| `Cargo.toml` | Rust | `Cargo.lock` |
| `*.csproj` | C# | — |

Sem manifesto: use a extensão predominante entre os arquivos-fonte e diga no relatório que a detecção foi por extensão.

## 2. Framework e versão

Cruze duas fontes — só o manifesto não basta, porque uma dependência declarada pode não ser usada:

1. a dependência no manifesto (com a versão fixada);
2. o import no entry point.

| Sinal no código | Framework |
|---|---|
| `Flask(__name__)` | Flask |
| `FastAPI()` | FastAPI |
| `django` em `INSTALLED_APPS` ou `manage.py` | Django |
| `express()` | Express |
| `@nestjs/core` | NestJS |
| `fastify()` | Fastify |
| `gin.Default()`, `http.ListenAndServe` | Gin / net-http |
| `Rails::Application` | Rails |
| `@SpringBootApplication` | Spring Boot |

Reporte a versão exatamente como o manifesto a fixa (`flask==3.1.1`, `express: ^4.18.2`). Se o manifesto usa faixa (`^`, `~`), a versão instalada pode ser outra — consulte o lockfile quando a distinção importar.

## 3. Entry point

Em ordem de confiança:

1. campo do manifesto (`main` no `package.json`, `scripts.start`);
2. bloco de execução direta (`if __name__ == '__main__'`, `func main()`);
3. o arquivo que instancia o servidor e chama `listen` / `run`.

## 4. Banco de dados

| Sinal | Onde |
|---|---|
| Driver no manifesto (`sqlite3`, `psycopg2`, `mysql2`, `pg`, `mongoose`) | manifesto |
| String de conexão (`sqlite:///`, `postgres://`, `mongodb://`) | config ou código |
| `CREATE TABLE` literal | código de bootstrap |
| Classes de model do ORM | camada de dados |

**Tabelas:** extraia dos `CREATE TABLE` quando o SQL é escrito à mão, ou do `__tablename__` / nome das entidades quando há ORM.

## 5. Contagem de arquivos

Conte **apenas fonte do projeto**. A contagem aparece no relatório e precisa bater com a realidade.

Exclua sempre:

```
node_modules/  .venv/  venv/  vendor/  target/  dist/  build/
__pycache__/  .git/  .claude/  .refactor-arch/
*.lock  *-lock.json  *.db  *.sqlite  *.pyc  *.min.js
```

Um projeto Node sem `.gitignore` adequado tem milhares de arquivos em `node_modules/`. Excluir não é opcional.

## 6. Enumeração de rotas

A Fase 3 precisa da lista completa com método e caminho. Procure por stack:

| Stack | Sinal |
|---|---|
| Flask | `@app.route`, `@bp.route`, `app.add_url_rule(...)` |
| FastAPI | `@app.get`, `@router.post` |
| Django | `urlpatterns` em `urls.py` |
| Express | `app.get/post/put/delete`, `router.<verbo>` |
| NestJS | `@Get()`, `@Post()` em controllers |
| Rails | `routes.rb` |
| Spring | `@RequestMapping`, `@GetMapping` |

Registro programático conta. `app.add_url_rule("/produtos", ...)` é uma rota tanto quanto um decorator.

Se existir um arquivo de exemplos de requisição (`*.http`, `*.rest`, coleção de Postman, `curl` no README), leia — ele traz payloads válidos que a Fase 3 vai usar no baseline.

## 7. Arquitetura real

**Esta é a parte que não pode olhar a árvore de diretórios.**

Localize quem exerce cada responsabilidade. Para cada uma, anote arquivo e linha:

| # | Responsabilidade | Sinal |
|---|---|---|
| R1 | Abre conexão ou sessão de banco | `connect(`, `createPool`, `new Database`, `SQLAlchemy()`, singleton de conexão |
| R2 | Monta query ou invoca o ORM | SQL literal, `.query(`, `.execute(`, `.find(`, query builder |
| R3 | Decide regra de negócio | cálculo de total, faixa de desconto, transição de estado, validação de domínio, condição sobre entidade |
| R4 | Trata HTTP | registro de rota, leitura de `request`, montagem de `response`, status code |

Depois classifique:

| Situação | Classificação |
|---|---|
| R1–R4 no mesmo arquivo, ou em 2–4 arquivos sem fronteira | **Monolítica** |
| Pastas por camada existem, mas R3 aparece dentro de R4, ou R2 dentro de R4 | **Camadas decorativas** |
| Pastas por camada existem e cada R vive na sua, mas uma camada concentra domínios demais | **MVC parcial** |
| Cada R na sua camada e as regras de `mvc-guidelines.md` passam | **MVC** |

**Camadas decorativas** é o caso mais traiçoeiro e o mais comum em projeto que já sofreu uma tentativa de organização. Dois sinais confirmam:

1. um arquivo de rota está entre os maiores do projeto — rota deveria ser a camada mais fina;
2. existe um método ou função na camada certa cuja lógica está **duplicada inline** na camada errada.

Para o segundo, conte referências: um símbolo definido que aparece **uma única vez no projeto inteiro** — na própria definição — é código morto. Se a lógica equivalente existe em outro lugar, é camada decorativa. Veja `AP-14` no catálogo.

## 8. Onde procurar APIs e dependências deprecated

Três lugares, e os três importam. Um projeto pode ter o código-fonte impecável e a árvore de dependências podre.

| Lugar | O que procurar | Como |
|---|---|---|
| **Código-fonte** | chamadas a APIs obsoletas da linguagem ou do framework | catálogo `AP-19`; rode a aplicação e leia os `DeprecationWarning` |
| **Manifesto** | versão major atrás da atual, pacote arquivado | comparar com a versão estável corrente |
| **Lockfile** | pacotes marcados como deprecated pelo registry | `grep '"deprecated"' package-lock.json`; a saída de `npm install` e `npm audit` lista |

Executar a aplicação uma vez é o detector mais barato que existe: runtimes modernos imprimem os avisos de depreciação no boot.
