# Beyond the Basics: Leveling Up the School 42 Fly-In Project

Of the current offer by School 42, Fly-In is perhaps an underrated subject. My personal opinion is that, by the time of this writing, the way this project is evaluated barely scratches the surface of what you can actually learn from it.

However, I have found that the core problem this exercise simulates mirrors highly relevant, modern industry challenges, where more robust and informed approaches offer a significant advantage.

My purpose, then, is to explore and discuss this project through a broader lens—focusing on the additional skills we can learn to help us grasp the real-world complexities of these kind of engineering challenge.

To find those techniques, I will research various methodologies found in available literature and explore existing repositories, including those kindly made public by fellow School 42 students.

Please note that my quest is not intended to judge or critize the work by others; rather, it is about creating a curated selection of what appears to be best practices for this kind of problem.

> This project is an _opinionated best effort_, intended for curation, discussion and basic reference.

I expect to document my quest on two different places:
- this repository, 
- blog's articles, mostly posted on my blog, [https://evaristoc.github.io/re-versing], but also Medium and other online publications.

## What you will find on this repository

This repository will be dedicated to host the different ways to approach the Fly-In project that IMO tend to offer the most relevant learnings, and discuss the techniques on the light on existing formal knowledge.

The various solutions will be documented on dedicated **folders** and might be based on solutions provided by others. To ensure originality and respect other people's code, I will try to replicate their approaches by writing **my own versions**.

Each folder could contain a README.md with a discussion of the version and its origin, crediting the source when possible.

When not able to make my own version, I will rather discuss the project in a dedicated article instead.

> Be aware that the whole repository is a live one, so structure and or content could change without notice.

### Current Versions:

|Folder|Hightlights|
|------|-----------|
|[v1-hop_based folder](./v1-hop_based)|A solution based on the **priority planning** methodology with _simplified capacity_ (capacity always 1). Individual drone (aka agent) routes are estimated using the **A\* algorithm**, which takes hop-based heuristic costs from a "distance" table built using a **Bellman-Ford**-ish algo.|
|[v2-capacity_heuristic_low_traffic folder](./v2-capacity_heuristic_low_traffic)|The same **priority planning** method as before but featuring _capacity handling_. Similarly, this one also makes use of a "distance" table built from a Bellman-Ford-ish algo, but with heuristic costs based on a custom **capacity-centric** calculation inspired in the **min-cost max-flow** rationale, but one that favour low capacity / low traffic regions.|


## What you will find in the articles

The articles will sometimes replicate the READMEs of the folders, enhanced with extra visualizations when applicable.

I will also use the articles to dive into very specific topics uncovered during my quest - for example especific situations only related to the Fly-In project, or practical insights found during the implementations that lack extensive documentation and that might be worth mentioning. I will refrain from discussing concepts that are already well-documented and accessible, opting instead to provide direct links to reference material.

In other articles I might include discussions of repositories and codebases that I consider valuable to analyze but I might not replicate for one or another reason.

Other topic for the articles could consist in the discussion of real-world applications that I hope will whet the reader's appetite by showing cases supporting a deep dive into the techniques applicable to assignments like Fly-In.