import { chatResponse } from "../services/llmService.js";

export const handleChat = async (req, res, next) => {
  try {
    const prompt = req.body?.message || req.body?.query || req.body?.prompt || req.body?.input || "";
    
    if (!prompt.trim()) {
      return res.status(400).json({ error: "Message is required." });
    }

    const answer = await chatResponse(prompt.trim());
    
    return res.json({
      type: "chat",
      answer,
    });
  } catch (error) {
    console.error("Chat generation failed:", error);
    return next(error);
  }
};
