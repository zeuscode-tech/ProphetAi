/** @type {import('next').NextConfig} */
const nextConfig = {
  devIndicators: false,
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
      // house.kg / lalafo.kg CDNs
      { protocol: "https", hostname: "cdn.house.kg" },
      { protocol: "https", hostname: "img.house.kg" },
      { protocol: "https", hostname: "images.house.kg" },
      { protocol: "https", hostname: "*.house.kg" },
      { protocol: "https", hostname: "*.lalafo.kg" },
      // Generic CDN fallback for other listing sources
      { protocol: "https", hostname: "*.amazonaws.com" },
      { protocol: "https", hostname: "*.cloudfront.net" },
      { protocol: "https", hostname: "images.unsplash.com" },
    ],
  },
};

module.exports = nextConfig;
