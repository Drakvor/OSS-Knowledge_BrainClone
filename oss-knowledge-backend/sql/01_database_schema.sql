-- ============================================
-- PostgreSQL 데이터베이스 스키마 및 시드 데이터
-- OSS Knowledge Backend
-- ============================================

-- 기존 테이블 삭제 (데이터가 있다면 백업 후 실행)
DROP TABLE IF EXISTS chat_messages CASCADE;
DROP TABLE IF EXISTS chat_sessions CASCADE;
DROP TABLE IF EXISTS graph_edges CASCADE;
DROP TABLE IF EXISTS graph_nodes CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS rag_departments CASCADE;
DROP TABLE IF EXISTS agents CASCADE;
DROP TABLE IF EXISTS rag_agent CASCADE;

-- ============================================
-- 테이블 생성
-- ============================================

-- 1. RAG/Agent 메타데이터 테이블
CREATE TABLE rag_agent (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    type        text NOT NULL,
    name        text NOT NULL,
    purpose     text,
    owner_team  text,
    owner_user  text,
    status      text NOT NULL DEFAULT 'active',
    tags        jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at  timestamp NOT NULL DEFAULT now(),
    updated_at  timestamp NOT NULL DEFAULT now(),
    deleted_at  timestamp
);

COMMENT ON TABLE rag_agent IS 'RAG/Agent 메타데이터';
COMMENT ON COLUMN rag_agent.id IS 'UUID';
COMMENT ON COLUMN rag_agent.type IS 'RAG/Agent 종류';
COMMENT ON COLUMN rag_agent.name IS '이름';
COMMENT ON COLUMN rag_agent.purpose IS '용도';
COMMENT ON COLUMN rag_agent.owner_team IS '사용팀';
COMMENT ON COLUMN rag_agent.owner_user IS '사용자';
COMMENT ON COLUMN rag_agent.status IS '상태';
COMMENT ON COLUMN rag_agent.tags IS '태그';
COMMENT ON COLUMN rag_agent.created_at IS '생성시각';
COMMENT ON COLUMN rag_agent.updated_at IS '수정시각';
COMMENT ON COLUMN rag_agent.deleted_at IS '삭제시각';

ALTER TABLE rag_agent
    ADD CONSTRAINT uq_rag_agent_type_name UNIQUE (type, name);
CREATE INDEX idx_rag_agent_created_at ON rag_agent (created_at);

-- 2. 채팅 세션 테이블
CREATE TABLE chat_sessions (
    id                      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 bigint REFERENCES users(id) ON DELETE CASCADE,
    title                   text NOT NULL DEFAULT '새 대화',
    llm_model               text NOT NULL DEFAULT 'gpt-4o',
    status                  text NOT NULL DEFAULT 'active', -- 'active', 'archived', 'deleted'
    metadata                jsonb NOT NULL DEFAULT '{}'::jsonb, -- 세션별 설정, 통계 등
    
    -- 메시지 카운트 (슬라이딩 윈도우용)
    assistant_message_count integer NOT NULL DEFAULT 0, -- AI 응답 메시지 수
    total_message_count    integer NOT NULL DEFAULT 0, -- 전체 메시지 수
    
    -- 토큰 관리
    total_tokens_used      bigint DEFAULT 0, -- 전체 사용 토큰 수
    
    -- 대화 요약 (핵심!)
    context_summary         text, -- 대화 요약본 (TEXT 타입으로 분리)
    summary_updated_at      timestamp, -- 요약 업데이트 시간
    summary_version         integer DEFAULT 1, -- 요약 버전 (요약 재생성 시 증가)
    
    created_at              timestamp NOT NULL DEFAULT now(),
    updated_at              timestamp NOT NULL DEFAULT now(),
    deleted_at              timestamp
);

COMMENT ON TABLE chat_sessions IS '채팅 세션 정보';
COMMENT ON COLUMN chat_sessions.id IS '세션 UUID';
COMMENT ON COLUMN chat_sessions.user_id IS '사용자 ID (users 테이블 참조)';
COMMENT ON COLUMN chat_sessions.title IS '대화 제목';
COMMENT ON COLUMN chat_sessions.llm_model IS '사용된 LLM 모델';
COMMENT ON COLUMN chat_sessions.status IS '세션 상태';
COMMENT ON COLUMN chat_sessions.metadata IS '세션 메타데이터 (통계, 설정 등)';
COMMENT ON COLUMN chat_sessions.assistant_message_count IS 'AI 응답 메시지 수 (슬라이딩 윈도우용)';
COMMENT ON COLUMN chat_sessions.total_message_count IS '전체 메시지 수';
COMMENT ON COLUMN chat_sessions.total_tokens_used IS '전체 사용 토큰 수';
COMMENT ON COLUMN chat_sessions.context_summary IS '대화 요약본 (TEXT 타입으로 분리)';
COMMENT ON COLUMN chat_sessions.summary_updated_at IS '요약 업데이트 시간';
COMMENT ON COLUMN chat_sessions.summary_version IS '요약 버전 (요약 재생성 시 증가)';
COMMENT ON COLUMN chat_sessions.created_at IS '생성시각';
COMMENT ON COLUMN chat_sessions.updated_at IS '수정시각';
COMMENT ON COLUMN chat_sessions.deleted_at IS '삭제시각';

-- 3. 채팅 메시지 테이블
CREATE TABLE chat_messages (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      uuid NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    turn_index      integer NOT NULL, -- 세션 내 메시지 순서 번호 (슬라이딩 윈도우 핵심)
    message_type    text NOT NULL, -- 'user', 'assistant', 'system'
    content         text NOT NULL,
    token_count     integer DEFAULT 0, -- tiktoken으로 계산된 토큰 수
    department_id   bigint REFERENCES rag_departments(id) ON DELETE SET NULL, -- 메시지별 부서 컨텍스트
    metadata        jsonb NOT NULL DEFAULT '{}'::jsonb, -- 검색 결과, 처리 시간 등
    parent_message_id uuid REFERENCES chat_messages(id) ON DELETE SET NULL, -- 답변 관계
    status          varchar(20) DEFAULT 'pending'::character varying NULL,
    created_at      timestamp NOT NULL DEFAULT now(),
    updated_at      timestamp NOT NULL DEFAULT now(),
    deleted_at      timestamp
);

COMMENT ON TABLE chat_messages IS '채팅 메시지';
COMMENT ON COLUMN chat_messages.id IS '메시지 UUID';
COMMENT ON COLUMN chat_messages.session_id IS '세션 ID (chat_sessions 참조)';
COMMENT ON COLUMN chat_messages.turn_index IS '세션 내 메시지 순서 번호 (슬라이딩 윈도우 핵심)';
COMMENT ON COLUMN chat_messages.message_type IS '메시지 타입 (user/assistant/system)';
COMMENT ON COLUMN chat_messages.content IS '메시지 내용';
COMMENT ON COLUMN chat_messages.token_count IS 'tiktoken으로 계산된 토큰 수';
COMMENT ON COLUMN chat_messages.department_id IS '메시지별 부서 컨텍스트 (검색 시 사용된 부서)';
COMMENT ON COLUMN chat_messages.metadata IS '메시지 메타데이터 (검색 결과, 처리 시간 등)';
COMMENT ON COLUMN chat_messages.parent_message_id IS '부모 메시지 ID (답변 관계)';
COMMENT ON COLUMN chat_messages.status IS '메시지 상태 (pending/completed/failed)';
COMMENT ON COLUMN chat_messages.created_at IS '생성시각';
COMMENT ON COLUMN chat_messages.updated_at IS '수정시각';
COMMENT ON COLUMN chat_messages.deleted_at IS '삭제시각';

-- 4. 채팅 메시지 피드백 테이블
CREATE TABLE chat_message_feedback (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_message_id uuid NOT NULL REFERENCES chat_messages(id) ON DELETE CASCADE,
    user_id         bigint REFERENCES users(id) ON DELETE SET NULL, -- 익명 피드백의 경우 NULL
    rating          integer NOT NULL CHECK (rating >= 1 AND rating <= 5), -- 1-5점 별점
    comment         text, -- 사용자 코멘트 (선택사항)
    feedback_type   text NOT NULL DEFAULT 'general', -- 'general', 'accuracy', 'helpfulness', 'clarity'
    is_anonymous    boolean NOT NULL DEFAULT true, -- 익명 피드백 여부
    metadata        jsonb NOT NULL DEFAULT '{}'::jsonb, -- 추가 피드백 데이터
    created_at      timestamp NOT NULL DEFAULT now(),
    updated_at      timestamp NOT NULL DEFAULT now(),
    deleted_at      timestamp
);

COMMENT ON TABLE chat_message_feedback IS '채팅 메시지 피드백';
COMMENT ON COLUMN chat_message_feedback.id IS '피드백 UUID';
COMMENT ON COLUMN chat_message_feedback.user_message_id IS '사용자 질문 메시지 ID (어떤 질문에 대한 답변 피드백인지 추적)';
COMMENT ON COLUMN chat_message_feedback.user_id IS '피드백 작성자 ID (익명의 경우 NULL)';
COMMENT ON COLUMN chat_message_feedback.rating IS '별점 (1-5점)';
COMMENT ON COLUMN chat_message_feedback.comment IS '사용자 코멘트';
COMMENT ON COLUMN chat_message_feedback.feedback_type IS '피드백 유형';
COMMENT ON COLUMN chat_message_feedback.is_anonymous IS '익명 피드백 여부';
COMMENT ON COLUMN chat_message_feedback.metadata IS '추가 피드백 메타데이터';
COMMENT ON COLUMN chat_message_feedback.created_at IS '생성시각';
COMMENT ON COLUMN chat_message_feedback.updated_at IS '수정시각';
COMMENT ON COLUMN chat_message_feedback.deleted_at IS '삭제시각';

-- 5. Agents 테이블 (API용)
CREATE TABLE agents (
    id          varchar(26) PRIMARY KEY,
    name        text NOT NULL,
    model       text NOT NULL,
    description text,
    created_at  timestamp NOT NULL DEFAULT now()
);

CREATE INDEX idx_agents_created_at ON agents (created_at);

-- 6. RAG 부서 테이블
CREATE TABLE rag_departments (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(10),
    color VARCHAR(20),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    keywords JSONB DEFAULT '[]'::jsonb, -- JSON 배열로 저장
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    monthly_queries INT DEFAULT 0,
    CONSTRAINT uk_rag_departments_name UNIQUE (name)
);

-- 7. 사용자 테이블
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    full_name VARCHAR(100),
    role VARCHAR(20) NOT NULL DEFAULT 'USER',
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. Graph RAG 노드 테이블
CREATE TABLE graph_nodes (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    description TEXT,
    properties JSONB DEFAULT '{}'::jsonb,
    position_x FLOAT,
    position_y FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9. Graph RAG 엣지 테이블
CREATE TABLE graph_edges (
    id BIGSERIAL PRIMARY KEY,
    source_node_id BIGINT REFERENCES graph_nodes(id) ON DELETE CASCADE,
    target_node_id BIGINT REFERENCES graph_nodes(id) ON DELETE CASCADE,
    relationship_type VARCHAR(100) NOT NULL,
    strength FLOAT DEFAULT 1.0,
    properties JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 시드 데이터 삽입
-- ============================================

-- RAG Agent 시드 데이터
INSERT INTO rag_agent (id, type, name, purpose, owner_team, owner_user, status, tags) VALUES
(gen_random_uuid(), 'retriever', 'faq_search', 'FAQ 검색', 'support', 'alice', 'active', '{"category": "search", "priority": "high"}'),
(gen_random_uuid(), 'agent', 'summary_bot', '요약 봇', 'ml', 'bob', 'active', '{"category": "summarization", "priority": "medium"}');

-- Agents 시드 데이터
INSERT INTO agents (id, name, model, description) VALUES
('01HZX4N3ABCD1234567XYZ893', 'default', 'gpt-4o', '기본 RAG 에이전트'),
('01HZX4N3ABCD1234567XYZ894', 'assistant', 'gpt-3.5-turbo', '일반 어시스턴트'),
('01HZX4N3ABCD1234567XYZ895', 'expert', 'gpt-4', '전문가 모드');

-- RAG 부서 시드 데이터
INSERT INTO rag_departments (name, description, icon, color, status, keywords, monthly_queries) VALUES
('WM 현장팀', 'WM 현장 작업 및 관리', '🏭', 'blue', 'active', '["WM", "현장", "작업", "관리", "프로세스"]', 245),
('LEAN 현장팀', 'LEAN 현장 작업 및 관리', '⚡', 'green', 'active', '["LEAN", "현장", "작업", "관리", "프로세스"]', 189),
('외부 연계', '협력업체 및 고객 연계', '🌐', 'purple', 'active', '["협력업체", "고객", "외부", "연계", "협력"]', 156),
('품질관리팀', '품질 관리 및 검사', '🎯', 'orange', 'active', '["품질", "관리", "검사", "기준", "표준"]', 98),
('안전관리팀', '안전 관리 및 교육', '🛡️', 'red', 'active', '["안전", "관리", "교육", "수칙", "규정"]', 312),
('정비관리팀', '장비 정비 및 관리', '🔧', 'indigo', 'active', '["정비", "관리", "장비", "유지보수", "수리"]', 67),
('보고관리팀', '작업 보고 및 문서 관리', '📊', 'gray', 'active', '["보고", "관리", "문서", "체계", "기록"]', 134);

-- 사용자 시드 데이터 (비밀번호는 BCrypt로 인코딩된 "changeme")
INSERT INTO users (username, password, email, full_name, role, status) VALUES
('oss', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iKTVEFDi', 'oss@neoss.com', 'OSS Admin', 'ADMIN', 'ACTIVE'),
('test-user', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iKTVEFDi', 'test@neoss.com', 'Test User', 'USER', 'ACTIVE');



-- Graph RAG 노드 시드 데이터
INSERT INTO graph_nodes (name, type, description, properties, position_x, position_y) VALUES
('OSS Knowledge', 'concept', 'OSS 지식 관리 시스템', '{"importance": "high", "category": "system"}', 100, 100),
('RAG System', 'component', 'RAG 시스템 컴포넌트', '{"type": "retrieval", "status": "active"}', 200, 150),
('Document Store', 'storage', '문서 저장소', '{"capacity": "1TB", "format": "pdf,docx"}', 150, 200),
('User Interface', 'interface', '사용자 인터페이스', '{"framework": "vue", "version": "3"}', 250, 100);

-- Graph RAG 엣지 시드 데이터
INSERT INTO graph_edges (source_node_id, target_node_id, relationship_type, strength, properties) VALUES
(1, 2, 'contains', 0.9, '{"relationship": "composition"}'),
(2, 3, 'uses', 0.8, '{"relationship": "dependency"}'),
(2, 4, 'interacts_with', 0.7, '{"relationship": "interface"}'),
(1, 4, 'provides', 0.6, '{"relationship": "service"}');


-- ============================================
-- 인덱스 생성
-- ============================================

-- chat_sessions 인덱스
CREATE INDEX idx_chat_sessions_user_id ON chat_sessions (user_id);
CREATE INDEX idx_chat_sessions_created_at ON chat_sessions (created_at);
CREATE INDEX idx_chat_sessions_status ON chat_sessions (status);
CREATE INDEX idx_chat_sessions_user_created ON chat_sessions (user_id, created_at DESC);

-- chat_messages 인덱스
CREATE INDEX idx_chat_messages_session_id ON chat_messages (session_id);
CREATE INDEX idx_chat_messages_created_at ON chat_messages (created_at);
CREATE INDEX idx_chat_messages_type ON chat_messages (message_type);
CREATE INDEX idx_chat_messages_session_created ON chat_messages (session_id, created_at ASC);
CREATE INDEX idx_chat_messages_parent_id ON chat_messages (parent_message_id);

-- turn_index 기반 슬라이딩 윈도우 최적화 인덱스
CREATE INDEX idx_chat_messages_session_turn ON chat_messages (session_id, turn_index);
CREATE INDEX idx_chat_messages_turn_index ON chat_messages (turn_index);

-- department_id 인덱스 (부서별 메시지 분석용)
CREATE INDEX idx_chat_messages_department_id ON chat_messages (department_id);

-- chat_message_feedback 인덱스
CREATE INDEX idx_chat_message_feedback_user_message_id ON chat_message_feedback (user_message_id);
CREATE INDEX idx_chat_message_feedback_user_id ON chat_message_feedback (user_id);
CREATE INDEX idx_chat_message_feedback_rating ON chat_message_feedback (rating);
CREATE INDEX idx_chat_message_feedback_created_at ON chat_message_feedback (created_at);
CREATE INDEX idx_chat_message_feedback_type ON chat_message_feedback (feedback_type);
CREATE INDEX idx_chat_message_feedback_user_message_rating ON chat_message_feedback (user_message_id, rating);
CREATE INDEX idx_chat_message_feedback_anonymous ON chat_message_feedback (is_anonymous);

-- 기존 인덱스들
CREATE INDEX idx_users_username ON users (username);
CREATE INDEX idx_users_email ON users (email);
CREATE INDEX idx_graph_nodes_type ON graph_nodes (type);
CREATE INDEX idx_graph_edges_source ON graph_edges (source_node_id);
CREATE INDEX idx_graph_edges_target ON graph_edges (target_node_id);
CREATE INDEX idx_rag_departments_status ON rag_departments (status);

-- ============================================
-- 트리거 함수 및 트리거
-- ============================================

-- updated_at 자동 업데이트 함수
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- chat_sessions 트리거
CREATE TRIGGER trigger_chat_sessions_updated_at
    BEFORE UPDATE ON chat_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- chat_messages 트리거
CREATE TRIGGER trigger_chat_messages_updated_at
    BEFORE UPDATE ON chat_messages
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- chat_message_feedback 트리거
CREATE TRIGGER trigger_chat_message_feedback_updated_at
    BEFORE UPDATE ON chat_message_feedback
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 완료 메시지
-- ============================================
SELECT 'PostgreSQL 데이터베이스 스키마와 시드 데이터가 성공적으로 생성되었습니다!' as message;
