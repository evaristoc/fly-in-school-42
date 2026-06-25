# Beyond the Basics: Leveling Up the School 42 Fly-In Project

Of the current offer by School 42, Fly-In is perhaps an underrated subject. My personal opinion is that, by the time of this writing, the way this project is evaluated barely scratches the surface of what you can actually learn from it.

However, I have found that the core problem this exercise simulates mirrors highly relevant, modern industry challenges, where more robust and informed approaches offer a significant advantage.

My purpose, then, is to explore and discuss this project through a broader lens—focusing on the additional skills we can learn to help us grasp the real-world complexities of these kind of engineering challenge.

To accomplish that goal I will research various methodologies found in available literature and explore existing repositories, including those kindly made public by fellow School 42 students.

> Please note that my quest is not intended to judge or critize the work by others; rather, it is about an _opinionated best effort_ to create a curated selection of what appears to be best practices for this kind of problem.

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
|[v1-hop_based](./v1-hop_based)|A solution based on the **priority planning** method with _simplified capacity_ (capacity always 1). This is a **time-expanded** solution. Individual drone (aka agent) routes are estimated using the **A\* algorithm**, which takes hop-based heuristic costs from a "distance" table built using a **Bellman-Ford**-ish algo. Under this assumption, this project reached global optima for _all the mandatory exercises_, but failed to cope with some custom patterns that deviated from the typical distribution of the mandatory ones, or when modified capacities of the mandatory exercises implied a different expected global optimum.|
|[v2-capacity_heuristic_low_traffic](./v2-capacity_heuristic_low_traffic)|The same **priority planning** method as before but featuring _capacity handling_. The registry of the zone use is called "constraint" but they are actually **reservations**, for which only the number of _occupying agents_ is of use. Similarly to the previous one this one also makes use of a "distance" table built from a Bellman-Ford-ish algo, but with heuristic costs based on a **custom capacity-centric** calculation inspired in the **min-cost max-flow** rationale, albeit one that favours **low capacity / low traffic regions**. This project solves _all the mandatory exercises correctly and under the highest score limit_, although sometimes slightly sub-optimal for at least one of the "hard" problems (couple of steps more than exact optimum but still under lower limit). It also failed in finding optima for custom graphs involving routes that splitted into high-capacity routes of few steps and low-capacity routes of many steps, favouring the latter. Optimal behaviour from some of the graphs, as shown from the only mandatory that showed to be sub-optimum, might improve when allowing for small manipulations of some of the capacities at configuration, evidencing the importance of clearly understanding the scope of the parameters to find potential adjustments. The project offers insights about the difficulties in capturing the scope of these methods when the number of factors affecting the "cost" calculation increases.|
|[v3-capacity_heuristic_high_traffic](./v3-capacity_heuristic_high_traffic)|Almost exactly the same as the previous one, except for small modifications to the heuristic calculation so it favours **high capacity / high traffic regions** instead. This project can solve some custom graphs better than the previous version as well as result in global optima without modifying configurable conditions for _most of the mandatory exercises_, but largerly fails in solving the "impossible dream" exercise, evidencing the sensitivity of the heuristics (and the solving methods in general) to domain-specific conditions.|
|[v4-dijkstra](./v4-dijkstra)|This iteration of the priority planning introduces a fair modification to the agent's pathfinder, shifting it toward an **optimized Dijkstra's algorithm** that uses _waiting ticks_ as the core metric for "distance" calculation. Due to the project's implementation framework, Dijkstra's algorithm computes distances between **time-based states**. These states are also subject to **constraints** imposed by other agents occupying the zones at those specific times, making the entire pathfinding process **strictly time-expanded**. This project behaves the same as version v3.|
|[v5-cbs](./v5-cbs)|(_This is still work in progress_) This is a _first working draft_ of a **CBS (constraint-based search) method implementation** to solve the Fly-In. In this iteration, the **low-level planners implement the Dijkstra** of previous version. High level planner implements a **best first search** on expanded constraint nodes. Differently to the previous versions where priority planner was implemented, the CBS makes use of **constraints** not as reservations but as **forbidden entries**. It was found that some of the requirements of the Fly-In might not correspond with typical classical cases for cbs implementations, like _capacities for zones **and** edges constraints_, resulting in the reassessment of the common method. This version works well so far for simple, straight graphs but it is still buggy and fails to complete complex or circular ones. (_NOTE: CBS was the original method I wanted to try for the Fly-In assignment before deciding to submit a priority planner_)|

## What you will find in the articles

The articles will sometimes replicate the READMEs of the folders, enhanced with extra visualizations when applicable.

I will also use the articles to dive into very specific topics uncovered during my quest - for example especific situations only related to the Fly-In project, or practical insights found during the implementations that lack extensive documentation and that might be worth mentioning. I will refrain from discussing concepts that are already well-documented and accessible, opting instead to provide direct links to reference material.

In other articles I might include discussions of repositories and codebases that I consider valuable to analyze but I might not replicate for one or another reason.

Other topic for the articles could consist in the discussion of real-world applications that I hope will whet the reader's appetite by showing cases supporting a deep dive into the techniques applicable to assignments like Fly-In.