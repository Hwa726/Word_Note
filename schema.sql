-- 2025-10-20 - 스마트 단어장 - 데이터베이스 스키마
-- 파일 위치: schema.sql
-- vocabulary.db 스키마 생성 스크립트

PRAGMA foreign_keys = ON;
PRAGMA encoding = "UTF-8";

-- ==============================================================================
-- 1. words 테이블
-- ==============================================================================
CREATE TABLE IF NOT EXISTS words (
    word_id INTEGER PRIMARY KEY AUTOINCREMENT,
    english TEXT NOT NULL UNIQUE,
    korean TEXT NOT NULL,
    memo TEXT,
    is_favorite INTEGER NOT NULL DEFAULT 0 CHECK(is_favorite IN (0,1)),
    created_date TEXT NOT NULL,
    modified_date TEXT
);

CREATE INDEX IF NOT EXISTS idx_words_english ON words(english);
CREATE INDEX IF NOT EXISTS idx_words_favorite ON words(is_favorite);
CREATE INDEX IF NOT EXISTS idx_words_created ON words(created_date);

-- ==============================================================================
-- 2. learning_history 테이블
-- ==============================================================================
CREATE TABLE IF NOT EXISTS learning_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    word_id INTEGER NOT NULL,
    study_date TEXT NOT NULL,
    is_correct INTEGER NOT NULL CHECK(is_correct IN (0,1)),
    response_time REAL,
    study_type TEXT NOT NULL CHECK(study_type IN ('flashcard','exam')),
    FOREIGN KEY (word_id) REFERENCES words(word_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_history_word ON learning_history(word_id);
CREATE INDEX IF NOT EXISTS idx_history_date ON learning_history(study_date);

-- ==============================================================================
-- 3. word_statistics 테이블
-- ==============================================================================
CREATE TABLE IF NOT EXISTS word_statistics (
    word_id INTEGER PRIMARY KEY,
    total_attempts INTEGER NOT NULL DEFAULT 0,
    correct_count INTEGER NOT NULL DEFAULT 0,
    wrong_count INTEGER NOT NULL DEFAULT 0,
    ease_factor REAL NOT NULL DEFAULT 2.5,  -- SM-2 알고리즘 파라미터
    interval_days INTEGER NOT NULL DEFAULT 0, -- SM-2 알고리즘 파라미터
    last_study_date TEXT, -- 최근 학습일
    FOREIGN KEY (word_id) REFERENCES words(word_id) ON DELETE CASCADE
);

-- ==============================================================================
-- 4. exam_history 테이블 (시험 기록)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS exam_history (
    exam_id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_date TEXT NOT NULL,
    total_words INTEGER NOT NULL,
    correct_count INTEGER NOT NULL,
    time_taken_seconds INTEGER,
    exam_type TEXT NOT NULL CHECK(exam_type IN ('short_answer','multiple_choice'))
);

-- ==============================================================================
-- 5. exam_details 테이블 (시험 상세 기록)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS exam_details (
    detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_id INTEGER NOT NULL,
    word_id INTEGER NOT NULL,
    is_correct INTEGER NOT NULL CHECK(is_correct IN (0,1)),
    user_answer TEXT,
    FOREIGN KEY (exam_id) REFERENCES exam_history(exam_id) ON DELETE CASCADE,
    FOREIGN KEY (word_id) REFERENCES words(word_id) ON DELETE CASCADE
);

-- ==============================================================================
-- 6. wrong_note 테이블 (오답 노트)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS wrong_note (
    note_id INTEGER PRIMARY KEY AUTOINCREMENT,
    word_id INTEGER NOT NULL UNIQUE,
    added_date TEXT NOT NULL,
    last_review_date TEXT,
    review_count INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (word_id) REFERENCES words(word_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_note_word ON wrong_note(word_id);
CREATE INDEX IF NOT EXISTS idx_note_date ON wrong_note(added_date);

-- ==============================================================================
-- 7. user_settings 테이블
-- ==============================================================================
CREATE TABLE IF NOT EXISTS user_settings (
    setting_key TEXT PRIMARY KEY,
    setting_value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_settings_updated ON user_settings(updated_at);

-- ==============================================================================
-- 8. 기본 설정값 삽입
-- ==============================================================================
-- common/settings.py에서 로드 시 DB에 값이 없으면 기본값을 사용하므로, 
-- 초기 실행 시에만 삽입하도록 'INSERT OR IGNORE' 사용
INSERT OR IGNORE INTO user_settings (setting_key, setting_value, updated_at) VALUES
('daily_word_goal', '50', datetime('now')),
('daily_time_goal', '30', datetime('now')),
('theme', 'light', datetime('now')),
('font_size', 'medium', datetime('now')),
('flashcard_time_limit', '10', datetime('now')),
('exam_time_limit', '600', datetime('now')),
('language', 'ko', datetime('now'));

-- ==============================================================================
-- 9. 스키마 버전 테이블
-- ==============================================================================
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL,
    description TEXT
);

INSERT OR IGNORE INTO schema_version (version, applied_at, description)
VALUES (1, datetime('now'), 'Initial schema creation');