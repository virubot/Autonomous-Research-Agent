import cors from "cors";
import express from "express";
import chatRoutes from "./routes/chatRoutes.js";
import paperRoutes from "./routes/paperRoutes.js";

const app = express();
const PORT = process.env.PORT || 5001;

app.use(cors());
app.use(express.json({ limit: "1mb" }));

app.get("/", (req, res) => {
  res.json({
    status: "OK",
    message: "Backend is running 🚀"
  });
});

app.get("/download", (req, res) => {
  const filePath = "generated_pdfs/latest.pdf";
  res.download(filePath);
});

app.get("/api/health", (_req, res) => {
  res.json({ status: "ok" });
});

app.use("/api/chat", chatRoutes);
app.use("/api/generate-paper", paperRoutes);

app.use((err, _req, res, _next) => {
  console.error("Unhandled backend error:", err);
  res.status(500).json({ error: "Internal server error" });
});

app.listen(PORT, () => {
  console.log(`Node backend running on http://localhost:${PORT}`);
});
