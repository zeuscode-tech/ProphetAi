/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    // Restrict to common real estate listing and CDN domains.
    // Add more patterns as needed when integrating additional listing sources.
    remotePatterns: [
      { protocol: "https", hostname: "*.zillow.com" },
      { protocol: "https", hostname: "*.realtor.com" },
      { protocol: "https", hostname: "*.redfin.com" },
      { protocol: "https", hostname: "*.trulia.com" },
      { protocol: "https", hostname: "*.zillowstatic.com" },
      { protocol: "https", hostname: "ap.rdcpix.com" },
      { protocol: "https", hostname: "photos.zillowstatic.com" },
      // Generic CDN fallback for other listing sources (can be tightened per integration)
      { protocol: "https", hostname: "*.amazonaws.com" },
      { protocol: "https", hostname: "*.cloudfront.net" },
    ],
  },
};

module.exports = nextConfig;
