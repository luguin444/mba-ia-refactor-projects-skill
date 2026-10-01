const LEVELS = { debug: 10, info: 20, warn: 30, error: 40 };

function createLogger(levelName = 'info') {
    const threshold = LEVELS[levelName] ?? LEVELS.info;

    const write = (level, message, meta) => {
        if (LEVELS[level] < threshold) return;
        const line = JSON.stringify({ time: new Date().toISOString(), level, message, ...meta });
        (LEVELS[level] >= LEVELS.warn ? process.stderr : process.stdout).write(`${line}\n`);
    };

    return {
        debug: (message, meta) => write('debug', message, meta),
        info: (message, meta) => write('info', message, meta),
        warn: (message, meta) => write('warn', message, meta),
        error: (message, meta) => write('error', message, meta),
    };
}

module.exports = { createLogger };
