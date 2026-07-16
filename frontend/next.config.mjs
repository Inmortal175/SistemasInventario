/** @type {import('next').NextConfig} */
const nextConfig = {
  // "standalone" es requerido por el Dockerfile de producción. En Windows local
  // el empaquetado usa symlinks (falla con EPERM sin modo desarrollador);
  // exportar NEXT_DISABLE_STANDALONE=1 permite compilar localmente sin él.
  output: process.env.NEXT_DISABLE_STANDALONE ? undefined : "standalone",
  eslint: {
    // El linting se corre aparte; no debe bloquear el build del contenedor.
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;
