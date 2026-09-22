const { scrypt, randomBytes, timingSafeEqual } = require('node:crypto');
const { promisify } = require('node:util');

const scryptAsync = promisify(scrypt);

const SALT_BYTES = 16;
const KEY_BYTES = 64;

// Substitui o `badCrypto`, que repetia 10.000 vezes os dois primeiros caracteres
// do base64 da senha e truncava em 10 — saída determinística, sem salt e com
// entropia quase nula (AP-05). scrypt vem da biblioteca padrão do Node: nenhuma
// dependência nova entra no projeto.
class PasswordService {
    async hash(plainPassword) {
        const salt = randomBytes(SALT_BYTES).toString('hex');
        const derivedKey = await scryptAsync(plainPassword, salt, KEY_BYTES);
        return `scrypt$${salt}$${derivedKey.toString('hex')}`;
    }

    async verify(plainPassword, storedHash) {
        const [algorithm, salt, keyHex] = String(storedHash).split('$');
        if (algorithm !== 'scrypt' || !salt || !keyHex) return false;

        const expected = Buffer.from(keyHex, 'hex');
        const actual = await scryptAsync(plainPassword, salt, expected.length);
        return timingSafeEqual(expected, actual);
    }
}

module.exports = PasswordService;
