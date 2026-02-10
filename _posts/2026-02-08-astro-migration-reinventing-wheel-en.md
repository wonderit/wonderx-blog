---
title: "From Astro Back to Jekyll — Don't Reinvent the Wheel"
description: "Tried to recreate the Chirpy theme in Astro. Too many missing pieces. Switched to the real Chirpy (Jekyll) and got everything working in 2 hours. Use what's already built."
date: 2026-02-08 01:00:00 +0900
tags: ['Astro', 'Jekyll', 'Chirpy', 'migration', 'blog', 'dont-reinvent-wheel']
categories: [dev]
image:
  path: /images/blog/astro-migration-1.webp
  width: 800
  height: 800
author: wonder
lang: en
twin: astro-migration-reinventing-wheel
---

## Can You Recreate the Chirpy Theme in Astro? Yes. Should You? Absolutely Not.

Here's the verdict upfront: **I spent a day trying to recreate the Chirpy blog theme in Astro v5, then switched to the actual Chirpy (Jekyll) theme and had everything working in 2 hours.** Build time: 0.8 seconds. Features that would have taken days to implement myself came for free with a single theme.

This isn't a criticism of Astro. It's a **real-world case study on why reinventing the wheel is a bad engineering decision** when a mature, battle-tested solution already exists.

## Starting Point — A Blog Built with Astro v5

This blog was originally built with **Astro v5**. I wrote components from scratch, designed layouts, styled everything. Added SEO, hooked up Giscus comments, integrated GoatCounter for page views. It was working reasonably well.

## Finding the Benchmark — Chirpy's Level of Polish

Then I stumbled upon [otzslayer.github.io](https://otzslayer.github.io/). A Jekyll blog running the **Chirpy theme**. The difference in polish was immediately apparent.

- Fixed left sidebar (profile, navigation, social links)
- Right panel (recent updates, trending tags)
- Page view counters on every single post
- AdSense ads placed naturally throughout the layout
- Dark/light mode toggle
- Search, table of contents, related posts -- the works

My Astro blog had less than half of these features. The thought was inevitable: "I want all of this on my blog."

## First Attempt — Building Chirpy-Style Inside Astro

My initial instinct was to **recreate the Chirpy layout within Astro**. I had Claude Code build it, and the output looked promising:

- `Sidebar.astro` -- Left sidebar (profile, nav, social icons)
- `RightPanel.astro` -- Right panel (recent updates, trending tags, ads)
- `SearchBar.astro` -- Client-side search
- `global.css` fully rewritten -- 1,235 lines
- Brand new Categories, Tags, and Archives pages

Build succeeded. 48 pages generated. Committed and pushed. So far, so good.

## Reality Check — Layout Similarity Is Not Feature Parity

After deploying and actually using it, **the list of missing pieces was substantial:**

- Page views not showing on individual posts
- Right sidebar disappearing on post pages
- Ad placement completely off
- No like/reaction functionality
- Search was flaky
- Dark mode transitions broke half the styles

Here's what I learned: **making the layout look similar and making every feature work with production-level polish are completely different problems.** Chirpy had been refined over years with community feedback. Recreating all of that in Astro components in a single day was not happening.

## The Decision — Switch to Real Chirpy

The deliberation was brief.

> "Do I keep patching things one by one in Astro, or just use the Chirpy theme?"

The answer was obvious. **Use what's already built.** I forked `cotes2020/jekyll-theme-chirpy` and replaced the entire repo.

### Migration — 7 Steps, 2 Hours Total

1. **Clone the Chirpy theme** -- delete all Astro files
2. **Configure `_config.yml`** -- Korean locale, GA4, GoatCounter, Giscus comments, avatar
3. **Migrate 10 blog posts** -- convert frontmatter (`pubDate` to `date`, `heroImage` to `image`, `category` to `categories`)
4. **Fix image paths** -- `public/images/blog/` to `assets/img/blog/`
5. **Update internal links** -- `/blog/slug` to `/posts/slug/`
6. **Set up AdSense** -- sidebar + in-article ads
7. **GitHub Actions deployment** -- Ruby 3.3 + Jekyll build

Build time: **0.8 seconds**. Total time to deploy: **50 seconds**. The build was actually faster than Astro.

## What Chirpy Gives You — The "It Just Works" Checklist

With the theme applied, all of the following features worked **with configuration alone:**

- Left sidebar (profile, navigation, dark/light toggle)
- Right panel (recent updates, trending tags)
- GoatCounter page views (auto-displayed on every post)
- Giscus comments + reactions
- Search (Simple-Jekyll-Search)
- Table of Contents
- Related posts
- Previous/Next post navigation
- AdSense ads (sidebar + in-article)
- Korean locale built in
- PWA support
- SEO optimization (og:image, twitter:card, etc.)

Features that would take days to build from scratch were all included in a single theme. **Build it yourself: days. Use the theme: 2 hours.** That gap is the essence of "don't reinvent the wheel."

## The Core Lesson — "Can Build" vs "Should Build"

There's a trap developers fall into constantly.

**"I could totally build this myself."**

Sure. You can. But **should you?**

Trying to recreate Chirpy in Astro made this crystal clear. Getting the layout to look similar? Easy. But page view integration, dark mode transition animations, search indexing, ad placement optimization, responsive sidebars -- building each of these to production quality is an entirely different scale of work.

| Comparison | Custom Astro Build | Chirpy Theme |
|---|---|---|
| **Time invested** | Multiple days (estimated) | 2 hours |
| **Feature completeness** | 60-70% | 100% |
| **Maintenance** | All on you | Community + updates |
| **Build time** | ~1.5s | 0.8s |

With numbers like these, there's nothing to debate.

> **Don't reinvent the wheel.**

A well-made off-the-shelf solution beats a half-baked custom build every time. The time you save is better spent **writing one more post** -- which is, after all, the entire point of having a blog.

---

*Astro isn't a bad framework. It's a great one. But in a domain like blogging, where polished solutions already exist, there's no reason to build from scratch. Save your energy for where you can actually differentiate.*
