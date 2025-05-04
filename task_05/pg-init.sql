CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR NOT NULL UNIQUE,
    email VARCHAR NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL,
    name VARCHAR NOT NULL,
    surname VARCHAR NOT NULL,
    age INTEGER
);


CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_name_surname ON users (name, surname);
CREATE INDEX idx_users_surname ON users(surname);


INSERT INTO users (username, email, hashed_password, name, surname, age)
VALUES (
    'admin',
    'admin@yandex.ru',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
    'Name',
    'Surname',
    32
);

DO $$
DECLARE
    v_name TEXT;
    v_surname TEXT;
    v_dept TEXT;
    v_username TEXT;
    v_email TEXT;
    v_age INTEGER;
    v_hashed_password TEXT := '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW';
    
    names TEXT[] := ARRAY[
      'John', 'Jane', 'Michael', 'Emily', 'David', 'Sarah', 'Robert', 'Laura', 'William', 'Elizabeth',
      'James', 'Olivia', 'Richard', 'Sophia', 'Thomas', 'Emma', 'Charles', 'Ava', 'Daniel', 'Mia',
      'Matthew', 'Isabella', 'Anthony', 'Charlotte', 'Mark', 'Amelia', 'Donald', 'Harper', 'Steven', 'Evelyn',
      'Paul', 'Abigail', 'Andrew', 'Emily', 'Joshua', 'Madison', 'Kenneth', 'Scarlett', 'Kevin', 'Victoria',
      'Brian', 'Ella', 'George', 'Grace', 'Edward', 'Chloe', 'Ronald', 'Penelope', 'Timothy', 'Lily'
    ];
    surnames TEXT[] := ARRAY[
      'Smith', 'Johnson', 'Williams', 'Jones', 'Brown', 'Davis', 'Miller', 'Wilson', 'Moore', 'Taylor',
      'Anderson', 'Thomas', 'Jackson', 'White', 'Harris', 'Martin', 'Thompson', 'Garcia', 'Martinez', 'Robinson',
      'Clark', 'Rodriguez', 'Lewis', 'Lee', 'Walker', 'Hall', 'Allen', 'Young', 'Hernandez', 'King',
      'Wright', 'Lopez', 'Hill', 'Scott', 'Green', 'Adams', 'Baker', 'Gonzalez', 'Nelson', 'Carter',
      'Mitchell', 'Perez', 'Roberts', 'Turner', 'Phillips', 'Campbell', 'Parker', 'Evans', 'Edwards', 'Collins'
    ];
    departments TEXT[] := ARRAY[
      'dev', 'marketing', 'sales', 'hr', 'finance', 'support', 'legal', 'design', 'product', 'research'
    ];
    
    inserted INTEGER := 0;
    skipped INTEGER := 0;
BEGIN
    -- Вставляем первых пользователей
    BEGIN
        INSERT INTO users (username, name, surname, email, age, hashed_password)
        VALUES ('admin', 'Admin', 'Adminov', 'admin@example.com', 35, v_hashed_password);
        inserted := inserted + 1;
    EXCEPTION WHEN unique_violation THEN
        skipped := skipped + 1;
    END;
    
    BEGIN
        INSERT INTO users (username, name, surname, email, age, hashed_password)
        VALUES ('john.admin', 'John', 'Admin', 'john.admin@example.com', 42, v_hashed_password);
        inserted := inserted + 1;
    EXCEPTION WHEN unique_violation THEN
        skipped := skipped + 1;
    END;

    FOR i IN 1..10000 LOOP
        v_name := names[1 + (i % array_length(names, 1))];
        v_surname := surnames[1 + (i % array_length(surnames, 1))];
        v_dept := departments[1 + (i % array_length(departments, 1))];

        v_username := LOWER(v_name || '.' || v_surname || '_' || i || '_' || v_dept);
        v_email := LOWER(v_name || '.' || v_surname || '_' || i || '@' || v_dept || '.example.com');
        v_age := 20 + (i % 40);

        BEGIN
            INSERT INTO users (username, name, surname, email, age, hashed_password)
            VALUES (v_username, v_name, v_surname, v_email, v_age, v_hashed_password);
            inserted := inserted + 1;
        EXCEPTION WHEN unique_violation THEN
            skipped := skipped + 1;
        END;

        IF i % 500 = 0 THEN
            RAISE NOTICE 'Progress: % / 10000 (inserted: %, skipped: %)', i, inserted, skipped;
        END IF;
    END LOOP;
    
    RAISE NOTICE 'Done: inserted %, skipped %', inserted, skipped;
END $$;

SELECT COUNT(*) AS total_users FROM users;
