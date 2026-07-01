import { Router, type IRouter } from "express";
import { HealthCheckResponse } from "@workspace/api-zod";

const router: IRouter = Router();

router.get("/healthz", (_req, res) => {
  try {
    const data = HealthCheckResponse.parse({ status: "ok" });
    res.status(200).json(data);
  } catch (_err) {
    res.status(200).json({ status: "ok" });
  }
});

export default router;
