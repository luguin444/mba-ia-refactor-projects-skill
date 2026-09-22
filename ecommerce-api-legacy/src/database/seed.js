// Dados de exemplo, acionados por chamada explícita (AP-25).
// A aplicação usa banco em memória: sem o seed não há nada para servir, então o
// composition root o executa em desenvolvimento. Em produção ele não roda.

const SEED_USER = { name: 'Leonan', email: 'leonan@fullcycle.com.br', password: '123' };

const SEED_COURSES = [
    { title: 'Clean Architecture', price: 997.0, active: 1 },
    { title: 'Docker', price: 497.0, active: 1 },
];

async function seed(db, passwordService) {
    // A senha do seed era gravada em claro no código original. Agora passa pela
    // mesma derivação dos usuários criados no checkout (AP-05).
    const passwordHash = await passwordService.hash(SEED_USER.password);

    await db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [
        SEED_USER.name,
        SEED_USER.email,
        passwordHash,
    ]);

    for (const course of SEED_COURSES) {
        await db.run('INSERT INTO courses (title, price, active) VALUES (?, ?, ?)', [
            course.title,
            course.price,
            course.active,
        ]);
    }

    await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [1, 1]);
    await db.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)', [
        1,
        997.0,
        'PAID',
    ]);
}

module.exports = { seed };
