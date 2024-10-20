const LOCAL_URL = 'http://localhost:5000';
const REMOTE_URL = 'http://10.15.10.11:5000'

const BASE_URL = navigator.onLine ? REMOTE_URL : LOCAL_URL ;
const IMAGE_URL = BASE_URL + '/images';
const FACES_URL = BASE_URL + '/faces';
const AUTH_URL = BASE_URL + '/auth';

export {
    IMAGE_URL,
    FACES_URL,
    AUTH_URL,
    BASE_URL
}