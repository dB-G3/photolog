// src/amplify-config.ts
import type { ResourcesConfig } from 'aws-amplify';

export const authConfig: ResourcesConfig = {
  Auth: {
    Cognito: {
      userPoolId: 'ap-northeast-1_jug0MpVwV', // メモした UserPoolId
      userPoolClientId: '6sl2gevrvmp1pjq2mc7h8uhsa9',         // メモした AppClientId
      // リージョン（例: ap-northeast-1）
      loginWith: {
        username: true,
      }
    }
  }
};