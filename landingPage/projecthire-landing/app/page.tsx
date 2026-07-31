"use client";

/**
 * ProjectHire — Enterprise Landing Page
 * ------------------------------------------------------------------
 * Stack target: Next.js 14 (App Router) + Tailwind CSS
 * This file is intentionally a SINGLE, self-contained component so it
 * can be previewed instantly. In a real Next.js project, add
 * `"use client"` as the very first line (required because we use
 * hooks + IntersectionObserver), and optionally split the named
 * sub-components below into their own files under `components/`:
 *
 *   components/site-nav.jsx        -> <Nav />
 *   components/hero.jsx            -> <Hero />
 *   components/value-bento.jsx     -> <ValueBento />
 *   components/how-it-works.jsx    -> <HowItWorks />
 *   components/trust-marquee.jsx   -> <TrustMarquee />
 *   components/final-cta.jsx       -> <FinalCta />
 *   components/site-footer.jsx     -> <Footer />
 *
 * WATERMELON UI
 * ------------------------------------------------------------------
 * Every place you'd drop in a Watermelon UI block instead of the
 * hand-rolled version here is marked with a banner comment:
 *
 *   // 🍉 WATERMELON UI SLOT: <ComponentName /> ...
 *
 * The hand-rolled versions (Reveal, floating cards, marquee, glow
 * panels) are functionally equivalent placeholders — swap the props
 * across 1:1 once the library is wired up, nothing else needs to
 * change structurally.
 *
 * DESIGN TOKENS
 * ------------------------------------------------------------------
 *   Void      #050507  page background
 *   Panel     #0c0d12  card surfaces
 *   Line      #1d1f27  hairline borders
 *   Fog       #9195a3  secondary text
 *   Paper     #f4f5f7  primary text
 *   Signal    #3b82f6 -> #22d3ee  accent gradient ("verified" blue)
 *   Display face: Space Grotesk  |  Body face: Inter  |  Data/mono: JetBrains Mono
 */

import React, { useEffect, useRef, useState } from "react";
import {
  ArrowRight,
  ArrowUpRight,
  Radar,
  Fingerprint,
  Rocket,
  SlidersHorizontal,
  Search,
  MessagesSquare,
  Handshake,
  CheckCircle2,
  GitCommitHorizontal,
  Sparkles,
  Menu,
  X,
} from "lucide-react";

/* ------------------------------------------------------------------ */
/*  Global styles: fonts, keyframes, reduced-motion safety             */
/* ------------------------------------------------------------------ */

function GlobalStyles() {
  return (
    <style>{`
      @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

      .bs-root { font-family: 'Inter', ui-sans-serif, system-ui, sans-serif; background:#050507; }
      .bs-display { font-family: 'Space Grotesk', ui-sans-serif, sans-serif; }
      .bs-mono { font-family: 'JetBrains Mono', ui-monospace, monospace; }

      .bs-grid-bg {
        background-image:
          linear-gradient(to right, rgba(255,255,255,0.035) 1px, transparent 1px),
          linear-gradient(to bottom, rgba(255,255,255,0.035) 1px, transparent 1px);
        background-size: 64px 64px;
        mask-image: radial-gradient(ellipse 70% 60% at 50% 0%, black 40%, transparent 100%);
      }

      .bs-text-gradient {
        background: linear-gradient(90deg, #eef2ff, #93c5fd 35%, #22d3ee 60%, #eef2ff);
        background-size: 200% auto;
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        animation: bs-shine 7s ease-in-out infinite;
      }

      @keyframes bs-shine {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
      }

      @keyframes bs-float-a {
        0%, 100% { transform: translateY(0px) rotate(-3deg); }
        50% { transform: translateY(-14px) rotate(-3deg); }
      }
      @keyframes bs-float-b {
        0%, 100% { transform: translateY(0px) rotate(2deg); }
        50% { transform: translateY(-18px) rotate(2deg); }
      }
      @keyframes bs-orb {
        0%, 100% { transform: translate(0px, 0px) scale(1); }
        50% { transform: translate(20px, -30px) scale(1.08); }
      }
      @keyframes bs-pulse-dot {
        0% { left: -6%; opacity: 0; }
        10% { opacity: 1; }
        90% { opacity: 1; }
        100% { left: 106%; opacity: 0; }
      }
      @keyframes bs-marquee {
        0% { transform: translateX(0); }
        100% { transform: translateX(-50%); }
      }
      @keyframes bs-blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0; }
      }

      .bs-animate-float-a { animation: bs-float-a 7s ease-in-out infinite; }
      .bs-animate-float-b { animation: bs-float-b 8s ease-in-out infinite 0.4s; }
      .bs-animate-orb { animation: bs-orb 12s ease-in-out infinite; }
      .bs-animate-marquee { animation: bs-marquee 32s linear infinite; }
      .bs-pulse-dot { animation: bs-pulse-dot 3.2s ease-in-out infinite; }
      .bs-blink { animation: bs-blink 1.1s step-start infinite; }

      @media (prefers-reduced-motion: reduce) {
        .bs-animate-float-a, .bs-animate-float-b, .bs-animate-orb,
        .bs-animate-marquee, .bs-pulse-dot, .bs-blink, .bs-text-gradient {
          animation: none !important;
        }
      }
    `}</style>
  );
}

/* ------------------------------------------------------------------ */
/*  Scroll-reveal primitive                                            */
/*  🍉 WATERMELON UI SLOT: <WatermelonReveal effect="fade-up" />       */
/*  replaces this hook + wrapper 1:1 — same children/delay contract.   */
/* ------------------------------------------------------------------ */

function useInView(threshold = 0.18) {
  const ref = useRef<HTMLDivElement>(null);
  const [inView, setInView] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setInView(true);
          obs.unobserve(el);
        }
      },
      { threshold }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, [threshold]);
  return [ref, inView] as const;
}

interface RevealProps {
  children: React.ReactNode;
  delay?: number;
  className?: string;
}

function Reveal({ children, delay = 0, className = "" }: RevealProps) {
  const [ref, inView] = useInView();
  return (
    <div
      ref={ref}
      className={`transition-all duration-700 ease-out motion-reduce:transition-none motion-reduce:transform-none ${inView ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
        } ${className}`}
      style={{ transitionDelay: `${delay}ms` }}
    >
      {children}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Nav                                                                 */
/* ------------------------------------------------------------------ */

function Nav() {
  const [open, setOpen] = useState(false);
  const links = [
    { href: "#value", label: "Why ProjectHire" },
    { href: "#how", label: "How it works" },
    { href: "#trust", label: "Trusted by" },
  ];
  return (
    <header className="fixed top-0 inset-x-0 z-50 border-b border-zinc-900/80 bg-black/60 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-6 lg:px-8 h-16 flex items-center justify-between">
        <a href="#top" className="flex items-center gap-2.5 group">
          <span className="bs-display text-white font-semibold tracking-tight text-lg">
            ProjectHire
          </span>
        </a>

        <nav className="hidden md:flex items-center gap-8 text-sm text-zinc-400">
          {links.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className="hover:text-white transition-colors focus-visible:outline-none focus-visible:text-white"
            >
              {l.label}
            </a>
          ))}
        </nav>

        <div className="hidden md:block">
          <a
            href="https://forms.gle/UvAWuiV3LwVJ8mzDA"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm font-medium bg-white text-black px-4 py-2 rounded-full hover:bg-zinc-200 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
          >
            Join Us
          </a>
        </div>

        <button
          aria-label="Toggle menu"
          onClick={() => setOpen((v) => !v)}
          className="md:hidden text-zinc-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 rounded"
        >
          {open ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>

      {open && (
        <div className="md:hidden border-t border-zinc-900 bg-black px-6 py-4 flex flex-col gap-4">
          {links.map((l) => (
            <a key={l.href} href={l.href} onClick={() => setOpen(false)} className="text-zinc-300 text-sm">
              {l.label}
            </a>
          ))}
          <a
            href="https://forms.gle/UvAWuiV3LwVJ8mzDA"
            target="_blank"
            rel="noopener noreferrer"
            onClick={() => setOpen(false)}
            className="text-sm font-medium bg-white text-black px-4 py-2 rounded-full text-center"
          >
            Join Us
          </a>
        </div>
      )}
    </header>
  );
}

/* ------------------------------------------------------------------ */
/*  Hero                                                                */
/*  🍉 WATERMELON UI SLOT: <WatermelonHero variant="split-glow">       */
/*  can wrap the entire <section> below — pass the two floating panels */
/*  as `visual` children and the copy as `content` children.           */
/* ------------------------------------------------------------------ */

function CodePanel() {
  return (
    <div className="bs-animate-float-a absolute left-0 top-6 sm:top-2 w-[300px] sm:w-[340px] rounded-2xl border border-zinc-800 bg-[#0c0d12]/95 shadow-2xl backdrop-blur">
      <div className="flex items-center gap-1.5 px-4 py-3 border-b border-zinc-800">
        <span className="h-2.5 w-2.5 rounded-full bg-red-400/70" />
        <span className="h-2.5 w-2.5 rounded-full bg-yellow-400/70" />
        <span className="h-2.5 w-2.5 rounded-full bg-green-400/70" />
        <span className="bs-mono text-[11px] text-zinc-500 ml-2">architecture_review.ts</span>
      </div>
      <div className="bs-mono text-[12.5px] leading-6 px-4 py-4 text-zinc-400">
        <div><span className="text-purple-400">function</span> <span className="text-blue-400">reviewCandidate</span>(builder) {"{"}</div>
        <div className="pl-4">
          <span className="text-purple-400">const</span> proof = builder.projects
        </div>
        <div className="pl-8">.filter(p =&gt; p.<span className="text-cyan-300">isProduction</span>)</div>
        <div className="pl-4">
          <span className="text-purple-400">return</span> proof.length &gt; <span className="text-orange-300">2</span>;
        </div>
        <div>{"}"}</div>
      </div>
    </div>
  );
}

function ProfilePanel() {
  const tags = ["React", "Node", "AWS", "Postgres"];
  return (
    <div className="bs-animate-float-b absolute right-0 bottom-0 w-[280px] sm:w-[300px] rounded-2xl border border-zinc-800 bg-[#0c0d12]/95 shadow-2xl backdrop-blur p-5">
      <div className="flex items-center gap-3">
        <div className="h-10 w-10 rounded-full bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center shrink-0">
          <Fingerprint className="h-5 w-5 text-black" />
        </div>
        <div>
          <p className="text-white text-sm font-semibold">Verified Builder</p>
          <p className="flex items-center gap-1 text-[11px] text-emerald-400">
            <CheckCircle2 className="h-3 w-3" /> Proof of work confirmed
          </p>
        </div>
      </div>
      <div className="flex flex-wrap gap-1.5 mt-4">
        {tags.map((t) => (
          <span
            key={t}
            className="bs-mono text-[10px] tracking-wide uppercase px-2 py-1 rounded-md border border-zinc-800 text-zinc-400"
          >
            {t}
          </span>
        ))}
      </div>
      <div className="mt-4">
        <div className="flex items-center justify-between text-[11px] text-zinc-500 mb-1">
          <span>Architecture score</span>
          <span className="text-white font-medium">94</span>
        </div>
        <div className="h-1.5 w-full rounded-full bg-zinc-800 overflow-hidden">
          <div className="h-full w-[94%] rounded-full bg-gradient-to-r from-blue-500 to-cyan-400" />
        </div>
      </div>
    </div>
  );
}

function Hero() {
  return (
    <section id="top" className="relative pt-40 pb-32 sm:pt-48 sm:pb-40 overflow-hidden">
      {/* ambient background */}
      <div className="absolute inset-0 bs-grid-bg pointer-events-none" />
      <div
        className="bs-animate-orb absolute -top-24 left-1/4 h-72 w-72 rounded-full opacity-30 blur-3xl pointer-events-none"
        style={{ background: "radial-gradient(circle, #3b82f6, transparent 70%)" }}
      />
      <div
        className="bs-animate-orb absolute top-40 right-1/4 h-72 w-72 rounded-full opacity-20 blur-3xl pointer-events-none"
        style={{ background: "radial-gradient(circle, #22d3ee, transparent 70%)", animationDelay: "2s" }}
      />

      <div className="relative max-w-7xl mx-auto px-6 lg:px-8 flex flex-col items-center text-center">
        <Reveal>
          <span className="inline-flex items-center gap-2 bs-mono text-[11px] uppercase tracking-widest text-blue-300/90 border border-blue-400/20 bg-blue-500/5 px-3 py-1.5 rounded-full">
            <Sparkles className="h-3 w-3" />
            For engineering leaders, not job boards
          </span>
        </Reveal>

        <Reveal delay={100}>
          <h1 className="bs-display mt-7 text-4xl sm:text-6xl lg:text-7xl font-semibold tracking-tight text-white max-w-4xl">
            Cut the hiring noise.
            <br />
            Meet the <span className="bs-text-gradient">top 1%</span> of builders.
          </h1>
        </Reveal>

        <Reveal delay={200}>
          <p className="mt-6 text-lg text-zinc-400 max-w-2xl leading-relaxed">
            ProjectHire doesn't forward resumes or algorithm scores. Every engineer we send has
            already proven themselves on real architecture and real, production-grade
            projects — so every conversation you take is one worth having.
          </p>
        </Reveal>

        <Reveal delay={300}>
          <div className="mt-10 flex flex-col sm:flex-row items-center gap-4">
            <a
              href="https://forms.gle/UvAWuiV3LwVJ8mzDA"
              target="_blank"
              rel="noopener noreferrer"
              className="group inline-flex items-center gap-2 bg-white text-black font-medium px-6 py-3.5 rounded-full hover:bg-zinc-200 transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
            >
              Join Us
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </a>
            <a
              href="#how"
              className="inline-flex items-center gap-2 text-zinc-300 border border-zinc-700 px-6 py-3.5 rounded-full hover:border-zinc-500 hover:text-white transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
            >
              See How It Works
            </a>
          </div>
        </Reveal>

        {/* signature visual: code -> verified candidate */}
        <Reveal delay={420} className="w-full">
          <div className="relative mt-24 h-[280px] sm:h-[260px] max-w-3xl mx-auto">
            <div
              className="absolute left-[20%] right-[20%] top-1/2 -translate-y-1/2 h-px hidden sm:block"
              style={{ background: "linear-gradient(90deg, transparent, #3b82f6, #22d3ee, transparent)" }}
            >
              <span
                className="bs-pulse-dot absolute -top-[3px] h-2 w-2 rounded-full"
                style={{ background: "#7dd3fc", boxShadow: "0 0 12px 3px rgba(56,189,248,0.8)" }}
              />
            </div>
            <CodePanel />
            <ProfilePanel />
          </div>
        </Reveal>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/*  Value proposition — Bento grid                                     */
/*  🍉 WATERMELON UI SLOT: <WatermelonBentoGrid> wrapping three         */
/*  <WatermelonBentoCard glow="blue" icon={...} /> children in place    */
/*  of the three <BentoCard /> instances below.                        */
/* ------------------------------------------------------------------ */

interface BentoCardProps {
  icon: React.ElementType;
  eyebrow: string;
  title: string;
  description: string;
  className?: string;
  children?: React.ReactNode;
}

function BentoCard({ icon: Icon, eyebrow, title, description, className = "", children }: BentoCardProps) {
  return (
    <div
      className={`group relative rounded-3xl border border-zinc-800 bg-[#0c0d12] p-8 overflow-hidden hover:border-zinc-700 transition-colors ${className}`}
    >
      <div
        className="absolute -top-24 -right-24 h-56 w-56 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-500 blur-3xl pointer-events-none"
        style={{ background: "radial-gradient(circle, #3b82f6, transparent 70%)" }}
      />
      <div className="relative flex flex-col h-full">
        <div className="h-11 w-11 rounded-xl bg-zinc-900 border border-zinc-800 flex items-center justify-center mb-6">
          <Icon className="h-5 w-5 text-blue-300" />
        </div>
        <p className="bs-mono text-[11px] uppercase tracking-widest text-zinc-500 mb-2">{eyebrow}</p>
        <h3 className="bs-display text-xl sm:text-2xl font-semibold text-white mb-3">{title}</h3>
        <p className="text-zinc-400 leading-relaxed text-[15px]">{description}</p>
        {children}
      </div>
    </div>
  );
}

function ValueBento() {
  return (
    <section id="value" className="relative py-28 sm:py-32">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <Reveal className="max-w-2xl mb-14">
          <p className="bs-mono text-[11px] uppercase tracking-widest text-blue-300/80 mb-4">Why ProjectHire</p>
          <h2 className="bs-display text-3xl sm:text-4xl font-semibold text-white tracking-tight">
            Built for the hires you can't afford to get wrong.
          </h2>
        </Reveal>

        <div className="grid grid-cols-1 md:grid-cols-3 md:grid-rows-2 gap-6">
          <Reveal delay={0} className="md:col-span-2 md:row-span-1">
            <BentoCard
              icon={Radar}
              eyebrow="Zero-noise sourcing"
              title="We only send builders."
              description="No mass resume drops, no keyword-matched maybes. Every profile that reaches your inbox has already cleared a bar most candidates never see — so your team spends time deciding, not filtering."
              className="h-full"
            >
              <div className="mt-8 flex items-center gap-6 bs-mono text-xs text-zinc-500">
                <div>
                  <p className="text-white text-2xl bs-display font-semibold">1,200+</p>
                  <p>applicants screened</p>
                </div>
                <div className="h-8 w-px bg-zinc-800" />
                <div>
                  <p className="text-white text-2xl bs-display font-semibold">3</p>
                  <p>reach your desk</p>
                </div>
              </div>
            </BentoCard>
          </Reveal>

          <Reveal delay={120} className="md:col-span-1 md:row-span-2">
            <BentoCard
              icon={Fingerprint}
              eyebrow="Verified proof of work"
              title="Proven on real projects. Not puzzles."
              description="No leetcode theater. Candidates are evaluated on deep, complex, production-shaped work — the kind that actually predicts whether someone can own a system at your company."
              className="h-full"
            />
          </Reveal>

          <Reveal delay={240} className="md:col-span-2 md:row-span-1">
            <BentoCard
              icon={Rocket}
              eyebrow="Ready to deploy"
              title="Matched to your exact stack."
              description="Tell us what you're building with. We match on real, current experience with your stack — language, framework, infrastructure — so ramp-up is measured in days, not quarters."
              className="h-full"
            />
          </Reveal>
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/*  How it works                                                       */
/* ------------------------------------------------------------------ */

function HowItWorks() {
  const steps = [
    {
      icon: SlidersHorizontal,
      title: "Define your stack",
      description: "Tell us the exact stack, seniority, and role you're hiring for — no generic job spec required.",
    },
    {
      icon: Search,
      title: "Get matched instantly",
      description: "Our platform matches you with verified builders whose real-world work fits what you need.",
    },
    {
      icon: MessagesSquare,
      title: "Run one focused interview",
      description: "Spend 20 minutes on architecture with your top 3 candidates — not 20 minutes on a whiteboard puzzle.",
    },
    {
      icon: Handshake,
      title: "Hire with confidence",
      description: "Make the offer knowing the work has already been proven, not promised.",
    },
  ];

  return (
    <section id="how" className="relative py-28 sm:py-32 border-t border-zinc-900">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <Reveal className="max-w-2xl mb-16">
          <p className="bs-mono text-[11px] uppercase tracking-widest text-blue-300/80 mb-4">How it works</p>
          <h2 className="bs-display text-3xl sm:text-4xl font-semibold text-white tracking-tight">
            From open role to signed offer, four steps.
          </h2>
        </Reveal>

        <div className="relative grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
          <div className="hidden lg:block absolute top-6 left-[12.5%] right-[12.5%] h-px bg-zinc-800" />
          {steps.map((step, i) => (
            <Reveal key={step.title} delay={i * 110}>
              <div className="relative">
                <div className="flex items-center gap-3 mb-5">
                  <span className="relative h-12 w-12 shrink-0 rounded-full bg-[#0c0d12] border border-zinc-800 flex items-center justify-center z-10">
                    <step.icon className="h-5 w-5 text-blue-300" />
                  </span>
                  <span className="bs-mono text-xs text-zinc-600">STEP {String(i + 1).padStart(2, "0")}</span>
                </div>
                <h3 className="bs-display text-lg font-semibold text-white mb-2">{step.title}</h3>
                <p className="text-zinc-400 text-sm leading-relaxed">{step.description}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/*  Trust marquee                                                       */
/*  🍉 WATERMELON UI SLOT: <WatermelonMarquee speed="slow" fade />      */
/*  can replace the scrolling track below — same logos array as items. */
/* ------------------------------------------------------------------ */

function TrustMarquee() {
  const logos = ["NIMBUS", "ORBITAL", "VERTEX", "FLUXWORKS", "QUANTA", "APEXIO", "HALIFAX", "STRATA"];
  const track = [...logos, ...logos];

  return (
    <section id="trust" className="relative py-24 border-t border-zinc-900">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <Reveal className="text-center mb-12">
          <p className="bs-mono text-[11px] uppercase tracking-widest text-zinc-500">
            Trusted by engineering teams building what's next
          </p>
        </Reveal>
      </div>

      <div className="relative overflow-hidden">
        <div
          className="pointer-events-none absolute inset-y-0 left-0 w-24 z-10"
          style={{ background: "linear-gradient(90deg, #050507, transparent)" }}
        />
        <div
          className="pointer-events-none absolute inset-y-0 right-0 w-24 z-10"
          style={{ background: "linear-gradient(270deg, #050507, transparent)" }}
        />
        <div className="flex w-max bs-animate-marquee">
          {track.map((name, i) => (
            <div
              key={`${name}-${i}`}
              className="mx-3 shrink-0 rounded-2xl border border-zinc-800 bg-[#0c0d12] px-8 py-5 flex items-center justify-center"
            >
              <span className="bs-display text-zinc-500 text-lg tracking-wide">{name}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/*  Final CTA                                                           */
/*  🍉 WATERMELON UI SLOT: <WatermelonGlowPanel intensity="high">       */
/*  can wrap this section for a richer ambient background treatment.   */
/* ------------------------------------------------------------------ */

function FinalCta() {
  return (
    <section id="final-cta" className="relative py-28 sm:py-36 border-t border-zinc-900 overflow-hidden">
      <div
        className="absolute inset-0 opacity-40"
        style={{ background: "radial-gradient(ellipse 60% 60% at 50% 0%, rgba(59,130,246,0.25), transparent 70%)" }}
      />
      <div className="relative max-w-4xl mx-auto px-6 lg:px-8 text-center">
        <Reveal>
          <h2 className="bs-display text-3xl sm:text-5xl font-semibold text-white tracking-tight leading-tight">
            Your next hire is already vetted.
            <br />
            The only question is who reaches them first.
          </h2>
        </Reveal>
        <Reveal delay={120}>
          <p className="mt-6 text-zinc-400 text-lg max-w-xl mx-auto">
            Join ProjectHire and lock in priority access to a pipeline of pre-vetted,
            ready-to-deploy engineers — matched to your stack, proven on their work.
          </p>
        </Reveal>
        <Reveal delay={220}>
          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <a
              href="https://forms.gle/UvAWuiV3LwVJ8mzDA"
              target="_blank"
              rel="noopener noreferrer"
              className="group inline-flex items-center gap-2 bg-white text-black font-medium px-7 py-3.5 rounded-full hover:bg-zinc-200 transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
            >
              Join Us
              <ArrowUpRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
            </a>
            <a
              href="#how"
              className="text-zinc-300 hover:text-white transition-colors text-sm underline underline-offset-4 decoration-zinc-700"
            >
              Talk to our team first
            </a>
          </div>
        </Reveal>
        <Reveal delay={320}>
          <div className="mt-10 inline-flex items-center gap-2 bs-mono text-xs text-zinc-600">
            <span className="text-zinc-500">$</span>
            <span>awaiting_your_move</span>
            <span className="bs-blink text-blue-400">▍</span>
          </div>
        </Reveal>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/*  Footer                                                              */
/* ------------------------------------------------------------------ */

function Footer() {
  return (
    <footer className="border-t border-zinc-900 py-10">
      <div className="max-w-7xl mx-auto px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2.5">
          <span className="h-6 w-6 rounded-md bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center">
            <GitCommitHorizontal className="h-3.5 w-3.5 text-black" strokeWidth={2.5} />
          </span>
          <span className="bs-display text-white font-semibold text-sm">ProjectHire</span>
        </div>
        <p className="text-zinc-600 text-xs">© {new Date().getFullYear()} ProjectHire. All rights reserved.</p>
      </div>
    </footer>
  );
}

/* ------------------------------------------------------------------ */
/*  Page                                                                */
/* ------------------------------------------------------------------ */

export default function ProjectHireLanding() {
  return (
    <div className="bs-root min-h-screen text-zinc-200 antialiased">
      <GlobalStyles />
      <Nav />
      <main>
        <Hero />
        <ValueBento />
        <HowItWorks />
        <TrustMarquee />
        <FinalCta />
      </main>
      <Footer />
    </div>
  );
}

