import assert from 'node:assert/strict';
import test from 'node:test';
import { getFeedbackDatabaseConfig } from '../lib/feedback-database.cjs';
import clearFeedback from '../api/clear-feedback.js';
import getFeedback from '../api/get-feedback.js';
import submitFeedback from '../api/submit-feedback.js';

test('new Supabase secret keys are not sent as bearer JWTs', () => {
  const config = getFeedbackDatabaseConfig({
    SUPABASE_URL: 'https://project.supabase.co/',
    SUPABASE_SECRET_KEY: 'sb_secret_test'
  });

  assert.equal(config.supabaseUrl, 'https://project.supabase.co');
  assert.equal(config.headers.apikey, 'sb_secret_test');
  assert.equal(config.headers.Authorization, undefined);
});

test('legacy service-role environment variables remain supported', () => {
  const config = getFeedbackDatabaseConfig({
    SUPABASE_URL: 'https://project.supabase.co',
    SUPABASE_SERVICE_ROLE_KEY: 'legacy-service-role-jwt'
  });

  assert.equal(config.headers.apikey, 'legacy-service-role-jwt');
  assert.equal(config.headers.Authorization, 'Bearer legacy-service-role-jwt');
});

test('all feedback API handlers load and enforce their HTTP methods', async () => {
  for (const [handler, method] of [[submitFeedback, 'GET'], [getFeedback, 'POST'], [clearFeedback, 'POST']]) {
    const result = {};
    const res = {
      status(code) {
        result.status = code;
        return this;
      },
      json(body) {
        result.body = body;
        return body;
      }
    };

    await handler({ method }, res);
    assert.equal(result.status, 405);
  }
});

test('feedback submission uses normalized new-key headers and trims feedback', async () => {
  const originalEnvironment = {
    SUPABASE_URL: process.env.SUPABASE_URL,
    SUPABASE_SECRET_KEY: process.env.SUPABASE_SECRET_KEY,
    SUPABASE_SERVICE_ROLE_KEY: process.env.SUPABASE_SERVICE_ROLE_KEY
  };
  const originalFetch = globalThis.fetch;
  let request;

  process.env.SUPABASE_URL = 'https://project.supabase.co/';
  process.env.SUPABASE_SECRET_KEY = 'sb_secret_test';
  delete process.env.SUPABASE_SERVICE_ROLE_KEY;
  globalThis.fetch = async (url, options) => {
    request = { url, options };
    return { ok: true };
  };

  const result = {};
  const res = {
    status(code) {
      result.status = code;
      return this;
    },
    json(body) {
      result.body = body;
      return body;
    }
  };

  try {
    await submitFeedback({ method: 'POST', body: { feedback: '  Test feedback  ' } }, res);
  } finally {
    globalThis.fetch = originalFetch;
    for (const [key, value] of Object.entries(originalEnvironment)) {
      if (value === undefined) delete process.env[key];
      else process.env[key] = value;
    }
  }

  assert.equal(result.status, 200);
  assert.equal(request.url, 'https://project.supabase.co/rest/v1/feedback');
  assert.equal(request.options.headers.apikey, 'sb_secret_test');
  assert.equal(request.options.headers.Authorization, undefined);
  assert.equal(JSON.parse(request.options.body).feedback, 'Test feedback');
});

test('feedback submission reports an unreachable database as a service outage', async () => {
  const originalEnvironment = {
    SUPABASE_URL: process.env.SUPABASE_URL,
    SUPABASE_SECRET_KEY: process.env.SUPABASE_SECRET_KEY,
    SUPABASE_SERVICE_ROLE_KEY: process.env.SUPABASE_SERVICE_ROLE_KEY
  };
  const originalFetch = globalThis.fetch;
  process.env.SUPABASE_URL = 'https://project.supabase.co';
  process.env.SUPABASE_SECRET_KEY = 'sb_secret_test';
  delete process.env.SUPABASE_SERVICE_ROLE_KEY;
  globalThis.fetch = async () => {
    throw new TypeError('fetch failed');
  };

  const result = {};
  const res = {
    status(code) {
      result.status = code;
      return this;
    },
    json(body) {
      result.body = body;
      return body;
    }
  };

  try {
    await submitFeedback({ method: 'POST', body: { feedback: 'Test feedback' } }, res);
  } finally {
    globalThis.fetch = originalFetch;
    for (const [key, value] of Object.entries(originalEnvironment)) {
      if (value === undefined) delete process.env[key];
      else process.env[key] = value;
    }
  }

  assert.equal(result.status, 503);
  assert.match(result.body.error, /SUPABASE_URL/);
});
