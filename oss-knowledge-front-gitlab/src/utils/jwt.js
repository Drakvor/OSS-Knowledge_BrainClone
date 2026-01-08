/**
 * JWT 토큰 유틸리티 함수들
 */

/**
 * JWT 토큰을 디코딩하여 페이로드 정보를 반환
 * @param {string} token - JWT 토큰
 * @returns {Object|null} 디코딩된 페이로드 또는 null
 */
export const decodeJWT = (token) => {
    try {
        if (!token) return null;

        // JWT 토큰은 3부분으로 구성: header.payload.signature
        const parts = token.split(".");
        if (parts.length !== 3) return null;

        // payload 부분 디코딩 (base64url)
        const payload = parts[1];
        const b64 = payload.replace(/-/g, "+").replace(/_/g, "/");
        const binary = atob(b64);
        // UTF-8 바이트로 변환 후 TextDecoder로 안전하게 디코딩
        const bytes = Uint8Array.from(binary, (c) => c.charCodeAt(0));
        const json = new TextDecoder("utf-8").decode(bytes);
        return JSON.parse(json);
    } catch (error) {
        console.warn("JWT 디코딩 실패:", error);
        return null;
    }
};

/**
 * JWT 토큰에서 사용자 정보를 추출
 * @param {string} token - JWT 토큰
 * @returns {Object|null} 사용자 정보 또는 null
 */
export const extractUserFromToken = (token) => {
    const payload = decodeJWT(token);
    if (!payload) return null;

    return {
        id: payload.userId,
        username: payload.sub, // JWT의 subject는 username
        email: payload.email,
        fullName: payload.fullName,
        role: payload.role,
        status: payload.status,
    };
};

/**
 * JWT 토큰이 만료되었는지 확인
 * @param {string} token - JWT 토큰
 * @returns {boolean} 만료 여부
 */
export const isTokenExpired = (token) => {
    const payload = decodeJWT(token);
    if (!payload || !payload.exp) return true;

    const currentTime = Math.floor(Date.now() / 1000);
    return payload.exp < currentTime;
};

/**
 * JWT 토큰이 유효한지 확인 (구조 + 만료시간)
 * @param {string} token - JWT 토큰
 * @returns {boolean} 유효 여부
 */
export const isValidToken = (token) => {
    if (!token) return false;

    const payload = decodeJWT(token);
    if (!payload) return false;

    return !isTokenExpired(token);
};
