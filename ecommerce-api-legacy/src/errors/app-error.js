// Error with an HTTP status and the exact text body the client receives.
class AppError extends Error {
    constructor(status, message, { cause } = {}) {
        super(message, { cause });
        this.status = status;
    }
}

// Runs a persistence step; any unexpected failure becomes a 500 with the
// step's message, keeping the original error as `cause` for the log.
function failsWith(message, step) {
    try {
        return step();
    } catch (err) {
        if (err instanceof AppError) throw err;
        throw new AppError(500, message, { cause: err });
    }
}

module.exports = { AppError, failsWith };
