const { createHmac, timingSafeEqual } = require('node:crypto');

const TTL_SECONDS = 12 * 60 * 60;
const HEADER = Buffer.from(JSON.stringify({ alg: 'HS256', typ: 'JWT' })).toString('base64url');

// Minimal HS256 JWT on node:crypto, to avoid a new dependency.
class TokenService {
    constructor({ secret }) {
        this.secret = secret;
    }

    sign({ sub, role }) {
        const now = Math.floor(Date.now() / 1000);
        const payload = Buffer.from(JSON.stringify({ sub: String(sub), role, iat: now, exp: now + TTL_SECONDS })).toString('base64url');
        return `${HEADER}.${payload}.${this.#signature(`${HEADER}.${payload}`)}`;
    }

    // Returns the claims, or throws when the token is malformed, forged or expired.
    verify(token) {
        const [header, payload, signature] = String(token).split('.');
        if (header !== HEADER || !payload || !signature) throw new Error('malformed token');

        const expected = Buffer.from(this.#signature(`${header}.${payload}`));
        const actual = Buffer.from(signature);
        if (expected.length !== actual.length || !timingSafeEqual(expected, actual)) throw new Error('bad signature');

        const claims = JSON.parse(Buffer.from(payload, 'base64url').toString());
        if (!(claims.exp > Math.floor(Date.now() / 1000))) throw new Error('expired token');
        return claims;
    }

    #signature(data) {
        return createHmac('sha256', this.secret).update(data).digest('base64url');
    }
}

module.exports = { TokenService };
