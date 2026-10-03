import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RiskIntel upay | Trust & Risk Intelligence Engine",
  description: "Real-time AI-Powered Transaction Fraud Scoring, Local SHAP Explainability, and Governance Triage Dashboard for upay MFS.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#0B132B] text-slate-100 antialiased selection:bg-[#FFC107] selection:text-black">
        {children}
      </body>
    </html>
  );
}
