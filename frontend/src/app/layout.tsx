import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";
import WireframeSphere from "@/components/WireframeSphere";
import ClinicalAssistantChatbot from "@/components/ClinicalAssistantChatbot";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "KinemaTrace AI | Pediatric Gait Intelligence",
  description:
    "Production-grade platform for markerless pediatric gait screening and multi-agent clinical decision support powered by AI.",
  keywords: ["KinemaTrace", "pediatric gait analysis", "EHR", "biomechanics", "AI clinical decision support"],
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className} style={{ backgroundColor: "#171412", minHeight: "100vh" }}>
        <div style={{ display: "flex", width: "100%", minHeight: "100vh", position: "relative" }}>
          {/* Ambient Wireframe Copper Globe Background */}
          <WireframeSphere />

          {/* Agent 5 Global Floating Clinical Assistant Chatbot */}
          <ClinicalAssistantChatbot />

          {/* Left Vertical Navigation Sidebar */}
          <Sidebar />

          {/* Right Main Content Area */}
          <div
            style={{
              flex: 1,
              display: "flex",
              flexDirection: "column",
              minWidth: 0,
              position: "relative",
              zIndex: 1,
            }}
          >
            <Header />
            <main style={{ flex: 1, padding: "0 28px 28px 28px" }}>{children}</main>
          </div>
        </div>
      </body>
    </html>
  );
}
