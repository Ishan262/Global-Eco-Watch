import { Router, type IRouter } from "express";
import healthRouter from "./health";

const router: IRouter = Router();

// Root handler — deployment healthcheck hits GET /api (the base path)
router.get("/", (_req, res) => {
  res.status(200).json({ status: "healthy" });
});

router.use(healthRouter);

export default router;
