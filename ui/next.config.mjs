import dotenv from 'dotenv';
dotenv.config();

/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    OPENAI_API_KEY: process.env.OPENAI_API_KEY,
    REMOTE_ACTION_URL: process.env.REMOTE_ACTION_URL,
  },
};

export default nextConfig;
