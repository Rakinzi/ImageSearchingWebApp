// Single source of truth for API URL
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';
const IMAGE_URL = BASE_URL + '/images';
const FACES_URL = BASE_URL + '/faces';
const AUTH_URL = BASE_URL + '/auth';

export {
    IMAGE_URL,
    FACES_URL,
    AUTH_URL,
    BASE_URL
}