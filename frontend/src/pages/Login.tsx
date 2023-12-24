import { apiClient } from 'api';
import { useAuth } from 'api/auth';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import Link from '@mui/material/Link';

import { AuthLogin } from '@chainlit/react-components';

import { Logo } from 'components/atoms/logo';

import { useQuery } from 'hooks/query';

function getCookie(cname: string) {
  const name = cname + '=';
  const decodedCookie = decodeURIComponent(document.cookie);
  const ca = decodedCookie.split(';');
  for (let i = 0; i < ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) == ' ') {
      c = c.substring(1);
    }
    if (c.indexOf(name) == 0) {
      return c.substring(name.length, c.length);
    }
  }
  return null;
}

export default function Login() {
  const query = useQuery();
  const { data: config, setAccessToken, user } = useAuth();
  const [error, setError] = useState('');

  const navigate = useNavigate();

  const handleHeaderAuth = async () => {
    try {
      const json = await apiClient.headerAuth();
      setAccessToken(json.access_token);
      navigate('/');
    } catch (error: any) {
      setError(error.message);
    }
  };

  const handlePasswordLogin = async (
    email: string,
    password: string,
    callbackUrl: string
  ) => {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);

    try {
      const json = await apiClient.passwordAuth(formData);
      setAccessToken(json.access_token);
      navigate(callbackUrl);
    } catch (error: any) {
      setError(error.message);
    }
  };

  useEffect(() => {
    setError(query.get('error') || '');
  }, [query]);

  const token = getCookie('token');

  useEffect(() => {
    if (!config) {
      return;
    }
    if (!config.requireLogin) {
      navigate('/');
    }
    if (config.headerAuth && token) {
      handleHeaderAuth();
    }
    if (user) {
      navigate('/');
    }
  }, [config, user]);

  const onLogin = async () => {
    const api_endpoint = await apiClient.getApiHost();
    window.location.href = `${api_endpoint}/api/auth/login`;
  };

  return (
    <AuthLogin
      title="Login to access the app."
      error={error}
      callbackUrl="/"
      providers={config?.oauthProviders || []}
      onPasswordSignIn={config?.passwordAuth ? handlePasswordLogin : undefined}
      onOAuthSignIn={async (provider: string) => {
        window.location.href = apiClient.getOAuthEndpoint(provider);
      }}
      renderLogo={<Logo style={{ maxWidth: '60%', maxHeight: '90px' }} />}
    >
      <Link component="button" onClick={onLogin}>
        Sign In
      </Link>
    </AuthLogin>
  );
}
