import { Router } from "express";
import { generatePaperController } from "../controllers/paperController.js";

const router = Router();

router.post("/", generatePaperController);

export default router;
