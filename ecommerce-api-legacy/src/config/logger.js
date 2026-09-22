// Logger com níveis, em substituição ao console.log espalhado (AP-28).
// Nunca receba segredo, senha, hash ou dado de cartão aqui — mascare na origem.

const LEVELS = { error: 0, warn: 1, info: 2, debug: 3 };

function createLogger({ level = 'info', sink = console } = {}) {
    const threshold = LEVELS[level] ?? LEVELS.info;

    const emit = (levelName, write) => (message, meta) => {
        if (LEVELS[levelName] > threshold) return;
        const line = `[${new Date().toISOString()}] ${levelName.toUpperCase()} ${message}`;
        if (meta === undefined) write(line);
        else write(line, meta);
    };

    return {
        error: emit('error', sink.error.bind(sink)),
        warn: emit('warn', sink.warn.bind(sink)),
        info: emit('info', sink.log.bind(sink)),
        debug: emit('debug', sink.log.bind(sink)),
    };
}

module.exports = createLogger;
