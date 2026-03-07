// src/amplify-config.ts
import type { ResourcesConfig } from 'aws-amplify';

export const authConfig: ResourcesConfig = {
  Auth: {
    Cognito: {
      userPoolId: import.meta.env.VITE_USER_POOL_ID,
      userPoolClientId: import.meta.env.VITE_APP_CLIENT_ID,
      // リージョン（例: ap-northeast-1）
      loginWith: {
        username: true,
      }
    }
  }
};