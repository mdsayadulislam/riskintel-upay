import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'RiskIntel upay | Trust & Risk Intelligence Engine',
  description: 'Official upay (UCB Fintech Ltd.) Transaction Simulator & Real-Time AI Fraud Scoring Console.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="bg-[#F4F6F8] text-slate-800 antialiased">
      <body className="bg-[#F4F6F8] text-slate-800 antialiased min-h-screen">
        {children}
      </body>
    </html>
  );
}
