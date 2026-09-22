const config = require('./config/env');
const createLogger = require('./config/logger');
const Database = require('./config/database');
const { createSchema } = require('./database/schema');
const { seed } = require('./database/seed');
const createApp = require('./create-app');

// Entry point: lê config, abre a conexão, prepara o banco, monta a app e sobe o
// servidor. Nenhuma rota e nenhuma regra são definidas aqui.
async function main() {
    const logger = createLogger({ level: config.logLevel });
    const db = Database.open(':memory:');
    const { app, services } = createApp({ db, config, logger });

    // Schema e seed deixaram de ser efeito colateral do boot e passaram a ser
    // chamadas explícitas (AP-25). O banco é em memória: sem o seed a aplicação
    // sobe vazia, então em desenvolvimento ele continua rodando — é o estado que
    // o baseline de contrato observa.
    await createSchema(db);
    if (config.isProduction) {
        logger.info('seed ignorado em produção');
    } else {
        await seed(db, services.passwordService);
    }

    app.listen(config.port, () => {
        logger.info(`servidor ouvindo na porta ${config.port}`, { env: config.nodeEnv });
    });
}

main().catch((error) => {
    console.error('falha ao iniciar a aplicação:', error);
    process.exit(1);
});
