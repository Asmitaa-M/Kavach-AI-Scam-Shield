/** Proxies /api/* to the FastAPI backend so the browser never deals with CORS. */
const BACKEND = process.env.BACKEND_URL || "http://127.0.0.1:8000";
module.exports = {
  reactStrictMode: true,
  eslint: { ignoreDuringBuilds: true },
  async rewrites() { return [{ source: "/api/:path*", destination: `${BACKEND}/api/:path*` }]; },
};
