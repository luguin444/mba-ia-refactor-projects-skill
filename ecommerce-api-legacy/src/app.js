const { createLogger } = require('./config/logger');
const { loadEnv } = require('./config/env');
const { createApp } = require('./create-app');

const logger = createLogger(process.env.LOG_LEVEL);
const env = loadEnv(logger);

createApp({ env, logger }).listen(env.port, () => {
    logger.info('Frankenstein LMS rodando', { port: env.port });
});
