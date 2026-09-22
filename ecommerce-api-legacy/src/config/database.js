const sqlite3 = require('sqlite3');

// Envelope promisificado em volta do driver sqlite3, que só fala callback.
// Existe para que nenhuma camada acima precise conhecer o driver (AP-13, AP-16).

class Database {
    #queue = Promise.resolve();

    constructor(driver) {
        this.driver = driver;
    }

    static open(filename = ':memory:') {
        return new Database(new sqlite3.Database(filename));
    }

    get(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.driver.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
        });
    }

    all(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.driver.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
        });
    }

    run(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.driver.run(sql, params, function callback(err) {
                if (err) reject(err);
                else resolve({ lastID: this.lastID, changes: this.changes });
            });
        });
    }

    exec(sql) {
        return new Promise((resolve, reject) => {
            this.driver.exec(sql, (err) => (err ? reject(err) : resolve()));
        });
    }

    close() {
        return new Promise((resolve, reject) => {
            this.driver.close((err) => (err ? reject(err) : resolve()));
        });
    }

    // SQLite não aninha transações, e todas as requisições compartilham esta
    // conexão. Sem a fila, dois checkouts concorrentes emitiriam dois BEGIN e o
    // segundo falharia. A fila serializa as transações, não as leituras.
    transaction(work) {
        const result = this.#queue.then(() => this.#runInTransaction(work));
        this.#queue = result.then(
            () => undefined,
            () => undefined,
        );
        return result;
    }

    async #runInTransaction(work) {
        await this.run('BEGIN');
        try {
            const value = await work();
            await this.run('COMMIT');
            return value;
        } catch (error) {
            await this.run('ROLLBACK').catch(() => undefined);
            throw error;
        }
    }
}

module.exports = Database;
