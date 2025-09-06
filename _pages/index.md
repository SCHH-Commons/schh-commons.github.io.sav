---
layout: default
title: Home
permalink: /
---

<style>
  :root {
    /* Coastal-inspired softer palette */
    --tile-ai: #6A89CC;       /* AI Chatbots - soft indigo blue */
    --tile-calendar: #D97C6B; /* Events Calendar - coral, harmonizes with logo */
    --tile-maps: #7FB685;     /* Maps - muted coastal green */
    --tile-podcasts: #E4C987; /* Podcasts - sandy beige-gold */
    --tile-blog: #5FB3B3;     /* Blog - teal seafoam */

    --tile-neutral: #F7F9F9;  /* Neutral background */
    --text-on-dark: #ffffff;
    --text-on-light: #102a43;
    --radius: 20px;
    --shadow: 0 8px 14px rgba(16, 42, 67, 0.12);
    --shadow-hover: 0 14px 24px rgba(16, 42, 67, 0.2);
  }
  .grid-container section {
    position: relative;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    min-height: 140px;
    border-radius: var(--radius);
    padding: 18px 18px 16px;
    box-shadow: var(--shadow);
    text-decoration: none;
    transition: transform 140ms ease, box-shadow 140ms ease, filter 140ms ease;
    overflow: hidden;
    isolation: isolate;
  }

</style>

# Welcome

Welcome to SCHH Commons, a neighbor-supported project designed to bring together resources, knowledge, and experiences that make life in Sun City Hilton Head easier and more enjoyable. This site is a community effort to collect, organize, and share helpful information, from practical how‑tos and curated documents to maps, guides, and stories contributed by residents.

##
{: .grid}


### ![AI Icon](https://upload.wikimedia.org/wikipedia/commons/2/23/Noun_project_194.svg) Knowledge Base
{: click="knowledge-base" style="background: var(--tile-ai);"}

Ask questions and explore SCHH resources with AI assistance.  


### ![Calendar Icon](https://upload.wikimedia.org/wikipedia/commons/8/82/Calendar_Icon_v1.svg) Calendar
{: click="calendar" style="background: var(--tile-calendar);"}

What’s happening this week and beyond.

### ![Map Icon](https://upload.wikimedia.org/wikipedia/commons/8/86/Interactive_Map_icon.svg) Maps
{: click="maps" style="background: var(--tile-maps);"}

Neighborhoods, amenities, trails, and points of interest.

### ![Podcasts Icon](https://upload.wikimedia.org/wikipedia/commons/8/81/Noun_Project_Sound_icon_755642.svg) Podcasts
{: click="podcasts" style="background: var(--tile-podcasts);"}

Stories, overviews, and interviews from the community.
