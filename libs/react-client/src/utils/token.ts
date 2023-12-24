const tokenKey = 'token';

export function getToken() {
  try {
    return localStorage.getItem(tokenKey);
  } catch (e) {
    return;
  }
}

export function setToken(token: string) {
  try {
    return localStorage.setItem(tokenKey, token);
  } catch (e) {
    return;
  }
}

function setCookie(cname, cvalue, exdays) {
  const d = new Date();
  d.setTime(d.getTime() + exdays * 24 * 60 * 60 * 1000);
  const expires = 'expires=' + d.toUTCString();
  document.cookie = cname + '=' + cvalue + ';' + expires + ';path=/';
}

export function removeToken() {
  try {
    setCookie('token', '', -1);
    return localStorage.removeItem(tokenKey);
  } catch (e) {
    return;
  }
}
