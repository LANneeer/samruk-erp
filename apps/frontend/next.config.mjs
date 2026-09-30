/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  typescript: {
    ignoreBuildErrors: false,
  },
  images: {
    unoptimized: true,
  },
  productionBrowserSourceMaps: true,
  experimental: {
    serverSourceMaps: true,
    serverMinification: false,
  },
}

export default nextConfig
