import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  ...(process.env.STATIC_EXPORT==='1'?{output:'export',basePath:process.env.NEXT_PUBLIC_BASE_PATH??'',images:{unoptimized:true},trailingSlash:true,typescript:{tsconfigPath:'tsconfig.pages.json'}}:{}),
};

export default nextConfig;
