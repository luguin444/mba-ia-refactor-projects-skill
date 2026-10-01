const { scryptSync, randomBytes, timingSafeEqual } = require('node:crypto');

const SALT_BYTES = 16;
const KEY_LENGTH = 64;

// Stored format: "scrypt:<salt hex>:<hash hex>".
function hashPassword(password) {
    const salt = randomBytes(SALT_BYTES);
    const hash = scryptSync(password, salt, KEY_LENGTH);
    return `scrypt:${salt.toString('hex')}:${hash.toString('hex')}`;
}

function verifyPassword(password, stored) {
    if (!stored) return false;
    const [scheme, saltHex, hashHex] = stored.split(':');
    if (scheme !== 'scrypt' || !saltHex || !hashHex) return false;
    const expected = Buffer.from(hashHex, 'hex');
    const actual = scryptSync(password, Buffer.from(saltHex, 'hex'), expected.length);
    return timingSafeEqual(actual, expected);
}

module.exports = { hashPassword, verifyPassword };
