-- Seed data for Chinese Tutoring System (PostgreSQL version)
-- Run this to populate the database with mock data
-- Assumes users and tutors already exist

-- Insert Availabilities (recurring slots for each tutor)
-- Tutor 1 (Anh Nguyen)
INSERT INTO availabilities (tutor_id, day_of_week, start_time, end_time, session_type, is_recurring, created_at)
SELECT t.id, 0, DATE_TRUNC('day', NOW()) + INTERVAL '9 hours', DATE_TRUNC('day', NOW()) + INTERVAL '11 hours', 'office_hours', TRUE, NOW()
FROM tutors t JOIN users u ON t.user_id = u.id WHERE u.clerk_user_id = 'clerk_tutor_001'
UNION ALL SELECT t.id, 0, DATE_TRUNC('day', NOW()) + INTERVAL '11 hours', DATE_TRUNC('day', NOW()) + INTERVAL '13 hours', 'tutoring', TRUE, NOW()
FROM tutors t JOIN users u ON t.user_id = u.id WHERE u.clerk_user_id = 'clerk_tutor_001'
UNION ALL SELECT t.id, 0, DATE_TRUNC('day', NOW()) + INTERVAL '13 hours', DATE_TRUNC('day', NOW()) + INTERVAL '15 hours', 'office_hours', TRUE, NOW()
FROM tutors t JOIN users u ON t.user_id = u.id WHERE u.clerk_user_id = 'clerk_tutor_001'
UNION ALL SELECT t.id, 1, DATE_TRUNC('day', NOW()) + INTERVAL '9 hours', DATE_TRUNC('day', NOW()) + INTERVAL '11 hours', 'tutoring', TRUE, NOW()
FROM tutors t JOIN users u ON t.user_id = u.id WHERE u.clerk_user_id = 'clerk_tutor_001'
UNION ALL SELECT t.id, 1, DATE_TRUNC('day', NOW()) + INTERVAL '11 hours', DATE_TRUNC('day', NOW()) + INTERVAL '13 hours', 'office_hours', TRUE, NOW()
FROM tutors t JOIN users u ON t.user_id = u.id WHERE u.clerk_user_id = 'clerk_tutor_001'
UNION ALL SELECT t.id, 1, DATE_TRUNC('day', NOW()) + INTERVAL '13 hours', DATE_TRUNC('day', NOW()) + INTERVAL '15 hours', 'tutoring', TRUE, NOW()
FROM tutors t JOIN users u ON t.user_id = u.id WHERE u.clerk_user_id = 'clerk_tutor_001';

-- Tutor 2 (Linh Tong)
INSERT INTO availabilities (tutor_id, day_of_week, start_time, end_time, session_type, is_recurring, created_at)
SELECT t.id, 2, DATE_TRUNC('day', NOW()) + INTERVAL '10 hours', DATE_TRUNC('day', NOW()) + INTERVAL '12 hours', 'tutoring', TRUE, NOW()
FROM tutors t JOIN users u ON t.user_id = u.id WHERE u.clerk_user_id = 'clerk_tutor_002'
UNION ALL SELECT t.id, 2, DATE_TRUNC('day', NOW()) + INTERVAL '13 hours', DATE_TRUNC('day', NOW()) + INTERVAL '15 hours', 'office_hours', TRUE, NOW()
FROM tutors t JOIN users u ON t.user_id = u.id WHERE u.clerk_user_id = 'clerk_tutor_002'
UNION ALL SELECT t.id, 3, DATE_TRUNC('day', NOW()) + INTERVAL '9 hours', DATE_TRUNC('day', NOW()) + INTERVAL '11 hours', 'office_hours', TRUE, NOW()
FROM tutors t JOIN users u ON t.user_id = u.id WHERE u.clerk_user_id = 'clerk_tutor_002'
UNION ALL SELECT t.id, 3, DATE_TRUNC('day', NOW()) + INTERVAL '14 hours', DATE_TRUNC('day', NOW()) + INTERVAL '16 hours', 'tutoring', TRUE, NOW()
FROM tutors t JOIN users u ON t.user_id = u.id WHERE u.clerk_user_id = 'clerk_tutor_002';

-- Tutor 3 (Chinh Nguyen)
INSERT INTO availabilities (tutor_id, day_of_week, start_time, end_time, session_type, is_recurring, created_at)
SELECT t.id, 4, DATE_TRUNC('day', NOW()) + INTERVAL '9 hours', DATE_TRUNC('day', NOW()) + INTERVAL '11 hours', 'office_hours', TRUE, NOW()
FROM tutors t JOIN users u ON t.user_id = u.id WHERE u.clerk_user_id = 'clerk_tutor_003'
UNION ALL SELECT t.id, 4, DATE_TRUNC('day', NOW()) + INTERVAL '13 hours', DATE_TRUNC('day', NOW()) + INTERVAL '15 hours', 'tutoring', TRUE, NOW()
FROM tutors t JOIN users u ON t.user_id = u.id WHERE u.clerk_user_id = 'clerk_tutor_003'
UNION ALL SELECT t.id, 0, DATE_TRUNC('day', NOW()) + INTERVAL '10 hours', DATE_TRUNC('day', NOW()) + INTERVAL '12 hours', 'tutoring', TRUE, NOW()
FROM tutors t JOIN users u ON t.user_id = u.id WHERE u.clerk_user_id = 'clerk_tutor_003';

-- Insert Past Sessions (last 90 days)
-- Week 1
INSERT INTO sessions (tutor_id, student_id, course, session_type, start_time, end_time, status, created_at, updated_at) VALUES
((SELECT id FROM users WHERE clerk_user_id = 'clerk_tutor_001'), (SELECT id FROM users WHERE clerk_user_id = 'clerk_student_001'), 'Chinese 101', 'tutoring', NOW() - INTERVAL '85 days' + INTERVAL '10 hours', NOW() - INTERVAL '85 days' + INTERVAL '12 hours', 'booked', NOW() - INTERVAL '85 days', NOW() - INTERVAL '85 days'),
((SELECT id FROM users WHERE clerk_user_id = 'clerk_tutor_002'), (SELECT id FROM users WHERE clerk_user_id = 'clerk_student_002'), 'Chinese 201', 'office_hours', NOW() - INTERVAL '84 days' + INTERVAL '14 hours', NOW() - INTERVAL '84 days' + INTERVAL '15 hours', 'booked', NOW() - INTERVAL '84 days', NOW() - INTERVAL '84 days'),
((SELECT id FROM users WHERE clerk_user_id = 'clerk_tutor_003'), (SELECT id FROM users WHERE clerk_user_id = 'clerk_student_003'), 'Chinese 101', 'tutoring', NOW() - INTERVAL '83 days' + INTERVAL '11 hours', NOW() - INTERVAL '83 days' + INTERVAL '13 hours', 'booked', NOW() - INTERVAL '83 days', NOW() - INTERVAL '83 days'),
((SELECT id FROM users WHERE clerk_user_id = 'clerk_tutor_001'), (SELECT id FROM users WHERE clerk_user_id = 'clerk_student_004'), 'Chinese 301', 'office_hours', NOW() - INTERVAL '82 days' + INTERVAL '9 hours', NOW() - INTERVAL '82 days' + INTERVAL '10 hours', 'booked', NOW() - INTERVAL '82 days', NOW() - INTERVAL '82 days'),
((SELECT id FROM users WHERE clerk_user_id = 'clerk_tutor_002'), (SELECT id FROM users WHERE clerk_user_id = 'clerk_student_005'), 'Chinese 201', 'tutoring', NOW() - INTERVAL '81 days' + INTERVAL '13 hours', NOW() - INTERVAL '81 days' + INTERVAL '15 hours', 'booked', NOW() - INTERVAL '81 days', NOW() - INTERVAL '81 days');

-- Week 2
INSERT INTO sessions (tutor_id, student_id, course, session_type, start_time, end_time, status, created_at, updated_at) VALUES
((SELECT id FROM users WHERE clerk_user_id = 'clerk_tutor_003'), (SELECT id FROM users WHERE clerk_user_id = 'clerk_student_006'), 'Chinese 101', 'tutoring', NOW() - INTERVAL '78 days' + INTERVAL '10 hours', NOW() - INTERVAL '78 days' + INTERVAL '11 hours', 'booked', NOW() - INTERVAL '78 days', NOW() - INTERVAL '78 days'),
((SELECT id FROM users WHERE clerk_user_id = 'clerk_tutor_001'), (SELECT id FROM users WHERE clerk_user_id = 'clerk_student_007'), 'Chinese 301', 'office_hours', NOW() - INTERVAL '77 days' + INTERVAL '15 hours', NOW() - INTERVAL '77 days' + INTERVAL '17 hours', 'booked', NOW() - INTERVAL '77 days', NOW() - INTERVAL '77 days'),
((SELECT id FROM users WHERE clerk_user_id = 'clerk_tutor_002'), (SELECT id FROM users WHERE clerk_user_id = 'clerk_student_008'), 'Chinese 201', 'tutoring', NOW() - INTERVAL '76 days' + INTERVAL '11 hours', NOW() - INTERVAL '76 days' + INTERVAL '13 hours', 'booked', NOW() - INTERVAL '76 days', NOW() - INTERVAL '76 days'),
((SELECT id FROM users WHERE clerk_user_id = 'clerk_tutor_003'), (SELECT id FROM users WHERE clerk_user_id = 'clerk_student_001'), 'Chinese 101', 'office_hours', NOW() - INTERVAL '75 days' + INTERVAL '9 hours', NOW() - INTERVAL '75 days' + INTERVAL '10 hours', 'booked', NOW() - INTERVAL '75 days', NOW() - INTERVAL '75 days'),
((SELECT id FROM users WHERE clerk_user_id = 'clerk_tutor_001'), (SELECT id FROM users WHERE clerk_user_id = 'clerk_student_002'), 'Chinese 201', 'tutoring', NOW() - INTERVAL '74 days' + INTERVAL '14 hours', NOW() - INTERVAL '74 days' + INTERVAL '16 hours', 'booked', NOW() - INTERVAL '74 days', NOW() - INTERVAL '74 days');

-- Week 3-10 (More sessions)
INSERT INTO sessions (tutor_id, student_id, course, session_type, start_time, end_time, status, created_at, updated_at) VALUES
((SELECT id FROM users WHERE clerk_user_id = 'clerk_tutor_002'), (SELECT id FROM users WHERE clerk_user_id = 'clerk_student_003'), 'Chinese 101', 'tutoring', NOW() - INTERVAL '70 days' + INTERVAL '10 hours', NOW() - INTERVAL '70 days' + INTERVAL '12 hours', 'booked', NOW() - INTERVAL '70 days', NOW() - INTERVAL '70 days'),
((SELECT id FROM users WHERE clerk_user_id = 'clerk_tutor_003'), (SELECT id FROM users WHERE clerk_user_id = 'clerk_student_004'), 'Chinese 301', 'office_hours', NOW() - INTERVAL '65 days' + INTERVAL '13 hours', NOW() - INTERVAL '65 days' + INTERVAL '14 hours', 'booked', NOW() - INTERVAL '65 days', NOW() - INTERVAL '65 days'),
((SELECT id FROM users WHERE clerk_user_id = 'clerk_tutor_001'), (SELECT id FROM users WHERE clerk_user_id = 'clerk_student_005'), 'Chinese 201', 'tutoring', NOW() - INTERVAL '60 days' + INTERVAL '11 hours', NOW() - INTERVAL '60 days' + INTERVAL '13 hours', 'booked', NOW() - INTERVAL '60 days', NOW() - INTERVAL '60 days'),
((SELECT id FROM users WHERE clerk_user_id = 'clerk_tutor_002'), (SELECT id FROM users WHERE clerk_user_id = 'clerk_student_006'), 'Chinese 101', 'office_hours', NOW() - INTERVAL '55 days' + INTERVAL '9 hours', NOW() - INTERVAL '55 days' + INTERVAL '10 hours', 'booked', NOW() - INTERVAL '55 days', NOW() - INTERVAL '55 days'),
((SELECT id FROM users WHERE clerk_user_id = 'clerk_tutor_003'), (SELECT id FROM users WHERE clerk_user_id = 'clerk_student_007'), 'Chinese 301', 'tutoring', NOW() - INTERVAL '50 days' + INTERVAL '15 hours', NOW() - INTERVAL '50 days' + INTERVAL '17 hours', 'booked', NOW() - INTERVAL '50 days', NOW() - INTERVAL '50 days'),
((SELECT id FROM users WHERE clerk_user_id = 'clerk_tutor_001'), (SELECT id FROM users WHERE clerk_user_id = 'clerk_student_008'), 'Chinese 201', 'office_hours', NOW() - INTERVAL '45 days' + INTERVAL '10 hours', NOW() - INTERVAL '45 days' + INTERVAL '11 hours', 'booked', NOW() - INTERVAL '45 days', NOW() - INTERVAL '45 days'),
((SELECT id FROM users WHERE clerk_user_id = 'clerk_tutor_002'), (SELECT id FROM users WHERE clerk_user_id = 'clerk_student_001'), 'Chinese 101', 'tutoring', NOW() - INTERVAL '40 days' + INTERVAL '14 hours', NOW() - INTERVAL '40 days' + INTERVAL '16 hours', 'booked', NOW() - INTERVAL '40 days', NOW() - INTERVAL '40 days'),
((SELECT id FROM users WHERE clerk_user_id = 'clerk_tutor_003'), (SELECT id FROM users WHERE clerk_user_id = 'clerk_student_002'), 'Chinese 201', 'tutoring', NOW() - INTERVAL '35 days' + INTERVAL '11 hours', NOW() - INTERVAL '35 days' + INTERVAL '13 hours', 'booked', NOW() - INTERVAL '35 days', NOW() - INTERVAL '35 days'),
((SELECT id FROM users WHERE clerk_user_id = 'clerk_tutor_001'), (SELECT id FROM users WHERE clerk_user_id = 'clerk_student_003'), 'Chinese 101', 'office_hours', NOW() - INTERVAL '30 days' + INTERVAL '9 hours', NOW() - INTERVAL '30 days' + INTERVAL '10 hours', 'booked', NOW() - INTERVAL '30 days', NOW() - INTERVAL '30 days'),
((SELECT id FROM users WHERE clerk_user_id = 'clerk_tutor_002'), (SELECT id FROM users WHERE clerk_user_id = 'clerk_student_004'), 'Chinese 301', 'tutoring', NOW() - INTERVAL '25 days' + INTERVAL '13 hours', NOW() - INTERVAL '25 days' + INTERVAL '15 hours', 'booked', NOW() - INTERVAL '25 days', NOW() - INTERVAL '25 days'),
((SELECT id FROM users WHERE clerk_user_id = 'clerk_tutor_003'), (SELECT id FROM users WHERE clerk_user_id = 'clerk_student_005'), 'Chinese 201', 'office_hours', NOW() - INTERVAL '20 days' + INTERVAL '10 hours', NOW() - INTERVAL '20 days' + INTERVAL '11 hours', 'booked', NOW() - INTERVAL '20 days', NOW() - INTERVAL '20 days'),
((SELECT id FROM users WHERE clerk_user_id = 'clerk_tutor_001'), (SELECT id FROM users WHERE clerk_user_id = 'clerk_student_006'), 'Chinese 101', 'tutoring', NOW() - INTERVAL '15 days' + INTERVAL '14 hours', NOW() - INTERVAL '15 days' + INTERVAL '16 hours', 'booked', NOW() - INTERVAL '15 days', NOW() - INTERVAL '15 days'),
((SELECT id FROM users WHERE clerk_user_id = 'clerk_tutor_002'), (SELECT id FROM users WHERE clerk_user_id = 'clerk_student_007'), 'Chinese 301', 'tutoring', NOW() - INTERVAL '10 days' + INTERVAL '11 hours', NOW() - INTERVAL '10 days' + INTERVAL '13 hours', 'booked', NOW() - INTERVAL '10 days', NOW() - INTERVAL '10 days'),
((SELECT id FROM users WHERE clerk_user_id = 'clerk_tutor_003'), (SELECT id FROM users WHERE clerk_user_id = 'clerk_student_008'), 'Chinese 201', 'office_hours', NOW() - INTERVAL '5 days' + INTERVAL '9 hours', NOW() - INTERVAL '5 days' + INTERVAL '10 hours', 'booked', NOW() - INTERVAL '5 days', NOW() - INTERVAL '5 days');

-- Insert Future Sessions
INSERT INTO sessions (tutor_id, student_id, course, session_type, start_time, end_time, status, created_at, updated_at) VALUES
((SELECT id FROM users WHERE clerk_user_id = 'clerk_tutor_001'), (SELECT id FROM users WHERE clerk_user_id = 'clerk_student_001'), 'Chinese 101', 'tutoring', NOW() + INTERVAL '2 days' + INTERVAL '10 hours', NOW() + INTERVAL '2 days' + INTERVAL '12 hours', 'booked', NOW(), NOW()),
((SELECT id FROM users WHERE clerk_user_id = 'clerk_tutor_002'), (SELECT id FROM users WHERE clerk_user_id = 'clerk_student_002'), 'Chinese 201', 'office_hours', NOW() + INTERVAL '3 days' + INTERVAL '14 hours', NOW() + INTERVAL '3 days' + INTERVAL '15 hours', 'booked', NOW(), NOW()),
((SELECT id FROM users WHERE clerk_user_id = 'clerk_tutor_003'), NULL, 'Chinese 301', 'tutoring', NOW() + INTERVAL '4 days' + INTERVAL '11 hours', NOW() + INTERVAL '4 days' + INTERVAL '13 hours', 'available', NOW(), NOW()),
((SELECT id FROM users WHERE clerk_user_id = 'clerk_tutor_001'), (SELECT id FROM users WHERE clerk_user_id = 'clerk_student_004'), 'Chinese 301', 'office_hours', NOW() + INTERVAL '5 days' + INTERVAL '9 hours', NOW() + INTERVAL '5 days' + INTERVAL '10 hours', 'booked', NOW(), NOW()),
((SELECT id FROM users WHERE clerk_user_id = 'clerk_tutor_002'), NULL, 'Chinese 201', 'tutoring', NOW() + INTERVAL '6 days' + INTERVAL '13 hours', NOW() + INTERVAL '6 days' + INTERVAL '15 hours', 'available', NOW(), NOW()),
((SELECT id FROM users WHERE clerk_user_id = 'clerk_tutor_003'), (SELECT id FROM users WHERE clerk_user_id = 'clerk_student_006'), 'Chinese 101', 'tutoring', NOW() + INTERVAL '7 days' + INTERVAL '10 hours', NOW() + INTERVAL '7 days' + INTERVAL '11 hours', 'booked', NOW(), NOW());

-- Insert Session Notes for past sessions
INSERT INTO session_notes (session_id, tutor_id, attendance_status, notes, student_feedback, created_at, updated_at)
SELECT s.id, s.tutor_id, 'present', 'Student showed great improvement in pronunciation.', 'Student was engaged and participated actively', NOW(), NOW()
FROM sessions s WHERE s.start_time < NOW() LIMIT 15;

INSERT INTO session_notes (session_id, tutor_id, attendance_status, notes, student_feedback, created_at, updated_at)
SELECT s.id, s.tutor_id, 'present', 'Reviewed grammar concepts. Student needs more practice with tones.', 'Student was engaged and participated actively', NOW(), NOW()
FROM sessions s WHERE s.start_time < NOW() AND s.id NOT IN (SELECT session_id FROM session_notes) LIMIT 5;

-- Insert Feedback for attended sessions
INSERT INTO feedbacks (session_id, student_id, rating, comment, created_at, updated_at)
SELECT s.id, s.student_id, 5, 'Very helpful session! The tutor explained everything clearly.', NOW(), NOW()
FROM sessions s 
JOIN session_notes sn ON s.id = sn.session_id 
WHERE sn.attendance_status = 'present' AND s.student_id IS NOT NULL
LIMIT 10;

INSERT INTO feedbacks (session_id, student_id, rating, comment, created_at, updated_at)
SELECT s.id, s.student_id, 4, 'Great tutor, very patient and knowledgeable.', NOW(), NOW()
FROM sessions s 
JOIN session_notes sn ON s.id = sn.session_id 
WHERE sn.attendance_status = 'present' 
AND s.student_id IS NOT NULL 
AND s.id NOT IN (SELECT session_id FROM feedbacks)
LIMIT 8;

