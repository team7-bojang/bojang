import axios from 'axios';

import { Config } from '@/constants/config';

const defaultConfig = {
  baseURL: Config.apiBaseUrl,
  timeout: 30_000,
} as const;

export const authClient = axios.create({
  ...defaultConfig,
  headers: { 'Content-Type': 'application/json' },
});

export const apiClient = axios.create({
  ...defaultConfig,
  headers: { 'Content-Type': 'application/json' },
});

export const formDataClient = axios.create({
  ...defaultConfig,
  headers: {
    'Content-Type': 'multipart/form-data',
  },
});
