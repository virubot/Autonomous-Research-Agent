import researchBg from "@/assets/research-papers-bg.png";

// Layered, blended bi-color background. Deep navy base with diffused indigo
// gradients and a soft, blurred research-papers texture for depth.
export const MeshBackground = () => {
  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      {/* Base */}
      <div className="absolute inset-0 bg-background" />

      {/* Research papers image — lightly blurred, desaturated, tinted to theme */}
      <div
        className="absolute inset-0 opacity-[0.35]"
        style={{
          backgroundImage: `url(${researchBg})`,
          backgroundSize: "cover",
          backgroundPosition: "center",
          filter: "blur(4px) saturate(0) brightness(0.9) contrast(1.1)",
          transform: "scale(1.04)",
        }}
      />

      {/* Indigo color wash to blend the image into the theme (lighter so image shows) */}
      <div
        className="absolute inset-0"
        style={{
          background:
            "linear-gradient(135deg, hsl(222 45% 7% / 0.55) 0%, hsl(232 50% 12% / 0.45) 50%, hsl(243 50% 14% / 0.55) 100%)",
        }}
      />

      {/* Top-left indigo glow */}
      <div
        className="absolute -left-[15%] -top-[20%] h-[70vh] w-[70vw] rounded-full opacity-[0.55] blur-3xl"
        style={{
          background:
            "radial-gradient(circle at center, hsl(232 60% 30% / 0.55) 0%, hsl(230 50% 20% / 0.25) 40%, transparent 70%)",
        }}
      />

      {/* Bottom-right deeper indigo/violet wash */}
      <div
        className="absolute -bottom-[25%] -right-[15%] h-[80vh] w-[75vw] rounded-full opacity-[0.5] blur-3xl"
        style={{
          background:
            "radial-gradient(circle at center, hsl(243 55% 28% / 0.55) 0%, hsl(230 45% 18% / 0.2) 45%, transparent 75%)",
        }}
      />

      {/* Soft center diffusion to blend the two */}
      <div
        className="absolute left-1/2 top-1/2 h-[90vh] w-[90vw] -translate-x-1/2 -translate-y-1/2 rounded-full opacity-[0.25] blur-3xl"
        style={{
          background:
            "radial-gradient(circle at center, hsl(225 50% 22% / 0.5) 0%, transparent 70%)",
        }}
      />

      {/* Subtle vignette to add depth at edges */}
      <div
        className="absolute inset-0 opacity-70"
        style={{
          background:
            "radial-gradient(ellipse at center, transparent 45%, hsl(220 40% 4% / 0.7) 100%)",
        }}
      />
    </div>
  );
};
