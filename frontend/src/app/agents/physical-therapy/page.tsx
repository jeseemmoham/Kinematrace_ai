"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function PhysicalTherapistRedirect() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/agents/patient-progress");
  }, [router]);

  return (
    <div style={{ padding: "40px", textAlign: "center", color: "var(--ehr-muted)" }}>
      Redirecting to Agent 3: Patient Progress Monitoring Workspace...
    </div>
  );
}
