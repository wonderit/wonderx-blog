---
title: "From Astro Back to Jekyll — Don't Reinvent the Wheel"
description: "Tried to recreate the Chirpy theme in Astro. Too many missing pieces. Switched to the real Chirpy (Jekyll) and got everything working in 2 hours. Use what's already built."
date: 2026-02-08 01:00:00 +0900
tags: ['astro', 'jekyll', 'chirpy', 'migration', 'blog', 'dont-reinvent-wheel']
categories: [dev]
image:
  path: /images/blog/astro-migration-1.webp
  width: 800
  height: 800
author: wonder
lang: en
twin: astro-migration-reinventing-wheel
---

## It Started with Astro

This blog was originally built with **Astro v5**.

I wrote components from scratch, designed layouts, styled everything. Added SEO, hooked up Giscus comments, integrated GoatCounter for page views.

It was working pretty well, honestly.

## Then I Found the Benchmark

One day I stumbled upon [otzslayer.github.io](https://otzslayer.github.io/). A Jekyll blog running the **Chirpy theme**.

Even at a glance, the polish was on another level.

- Fixed left sidebar (profile, navigation, social links)
- Right panel (recent updates, trending tags)
- Page view counters on every single post
- AdSense ads placed naturally throughout the layout
- Dark/light mode toggle
- Search, table of contents, related posts — the works

"I want all of this on my blog."

## Building Chirpy-Style Inside Astro

My first instinct was to **recreate the Chirpy layout inside Astro**.

I had Claude Code build it. Here's what came out:

- `Sidebar.astro` — Left sidebar (profile, nav, social icons)
- `RightPanel.astro` — Right panel (recent updates, trending tags, ads)
- `SearchBar.astro` — Client-side search
- `global.css` fully rewritten — 1,235 lines
- Brand new Categories, Tags, and Archives pages

Build succeeded. 48 pages generated. Committed and pushed.

## But So Many Things Were Broken

After deploying, the list of missing features was... not short.

- Page views not showing on individual posts
- Right sidebar not appearing on post pages
- Ad placement completely off
- No like/reaction functionality
- Search was flaky
- Dark mode transition broke half the styles

Chirpy had been refined over **years**. Recreating all of that in Astro components in a single day? **Not happening.**

## So I Went with the Real Chirpy

I had a choice to make.

> "Do I keep patching things one by one in Astro, or just use the Chirpy theme?"

The answer was obvious. **Use what's already built.**

I forked `cotes2020/jekyll-theme-chirpy` and replaced the entire repo.

### The Migration Process

1. **Clone the Chirpy theme** — delete all Astro files
2. **Configure `_config.yml`** — Korean locale, GA4, GoatCounter, Giscus comments, avatar
3. **Migrate 10 blog posts** — convert frontmatter (`pubDate` to `date`, `heroImage` to `image`, `category` to `categories`)
4. **Fix image paths** — `public/images/blog/` to `assets/img/blog/`
5. **Update internal links** — `/blog/slug` to `/posts/slug/`
6. **Set up AdSense** — sidebar + in-article ads
7. **GitHub Actions deployment** — Ruby 3.3 + Jekyll build

Build time: **0.8 seconds**. Total time to deploy: **50 seconds**.

## What Chirpy Gives You Out of the Box

With the theme, all of this **just worked:**

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

**Build it yourself: days. Use the theme: 2 hours.**

## Don't Reinvent the Wheel

There's a trap developers fall into all the time.

**"I could totally build this myself."**

Sure. You can. But **should you?**

Trying to recreate Chirpy in Astro taught me something. Making the layout look similar? Easy. Making every feature actually **work** with the same level of polish? Completely different problem.

Page view integration, dark mode transitions, search indexing, ad placement optimization, responsive sidebars... Instead of spending time implementing each of these from scratch, **just use a theme that's been refined over years.**

> **Don't reinvent the wheel.**

A well-made off-the-shelf solution beats a half-baked custom build. Spend that time **writing one more post instead.**

---

*P.S. Astro isn't bad. It's a great framework. But in a space like blogging, where polished solutions already exist, there's no reason to build from scratch.*
