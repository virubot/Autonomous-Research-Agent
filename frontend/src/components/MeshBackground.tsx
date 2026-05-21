import researchBg from "@/assets/research-papers-bg.png";

export const MeshBackground = () => {
  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden bg-[#030305]">
      {/* Research papers image with a subtle blur */}
      <div
        className="absolute inset-0 opacity-60"
        style={{
          backgroundImage: `url(${researchBg})`,
          backgroundSize: "cover",
          backgroundPosition: "center",
          filter: "blur(6px) brightness(0.7)",
          transform: "scale(1.03)", // Prevent edge blur clipping
        }}
      />

      {/* Dark gradient overlay to ensure UI elements remain highly readable */}
      <div
        className="absolute inset-0 bg-gradient-to-b from-[#060608]/80 via-[#060608]/60 to-[#060608]/90"
      />

      {/* Noise overlay for a premium matte finish */}
      <div
        className="absolute inset-0 opacity-[0.04] mix-blend-overlay"
        style={{
          backgroundImage: "url('data:image/svg+xml,%3Csvg viewBox=%220 0 200 200%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter id=%22noiseFilter%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.65%22 numOctaves=%223%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23noiseFilter)%22/%3E%3C/svg%3E')",
        }}
      />
    </div>
  );
};

