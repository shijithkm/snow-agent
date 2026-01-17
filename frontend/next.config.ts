/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    // For server-side rewrites (running in Docker), use backend service name
    // For local dev, use localhost
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
    console.log('Backend URL for rewrites:', backendUrl);
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/:path*`
      }
    ];
  }
};

export default nextConfig;