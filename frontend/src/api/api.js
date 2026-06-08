const isLocalFrontend =
  typeof window !== 'undefined' &&
  ['localhost', '127.0.0.1'].includes(window.location.hostname);

const API_ROOT = isLocalFrontend
  ? 'http://127.0.0.1:5000'
  : process.env.REACT_APP_API_URL;

const BASE_URL = API_ROOT + '/api';

if (!API_ROOT) {
  throw new Error('REACT_APP_API_URL not defined in environment');
}

export default BASE_URL;
