# Beyond the Basics: Leveling Up the School 42 Fly-In Project

Of the current offer by School 42, Fly-In is perhaps an underrated subject. My personal opinion is that, by the time of this writing, the way this project is evaluated barely scratches the surface of what you can actually learn from doing this exercise.

Many of the solutions I have discussed with fellow students or found online have shown tremendous sense of creative in their approach, but in general have been poorly documented and based on limited research.

However, I have found that the core problem this exercise simulates mirrors highly relevant, modern industry challenges, where more robust and informed approaches offer a significant advantage.

My purpose, then, is to explore and discuss this project through a broader lens—focusing on the additional skills we can learn to help us grasp the real-world complexities of these kind of engineering challenge.

I will do that through this repository, as well as articles mostly posted on my blog, [https://evaristoc.github.io/re-versing].

## What you will find in this repository

This repository will be dedicated to deep into different ways to approach the Fly-In project and discuss the techniques on the light on existing formal knowledge.

The repository will include **various versions of solutions for the fly-in project using different techniques separated by folders**.

To find those techniques, I will research various methodologies found in available literature and explore existing repositories, including those kindly made public by fellow School 42 students.

Each folder could contain a README.md dedicated to the discussion of the version. 

Please note that my quest is not intended to judge or critize the work by others; rather, it is about creating a curated selection of what appears to be best practices for this kind of problem. To ensure originality and respect other people's code, I will try to replicate their approaches by writing **my own versions** from scratch when including a version based on a code found in a different repo, whenever possible.

## What you will find in the articles

The articles will sometimes replicate the READMEs of the folders,  enhanced with extra visualizations when applicable.

I will also use the articles to dive into very specific topics uncovered during my quest - for example especific situations only related to the Fly-In project, or practical insights found during the implementations that lack extensive documentation and that might be worth mentioning. I will refrain from discussing concepts that are already well-documented and accessible, opting instead to provide direct links to reference material.

In other articles I might include discussions of repositories and codebases that I consider valuable to analyze but I might not replicate for one or another reason.

Other topic for the articles could consist in the discussion of real-world applications that I hope will whet the reader's appetite by showing cases supporting a deep dive into the techniques applicable to assignments like Fly-In.

# In this repository:

* [v1-hop_based folder](./v1-hop_based): A presentation of a **priority based planning** with _simplified capacity_ (capacity always 1). Drone routes are estimated using the **A\* algorithm** that takes the costs of the heuristics from a table built using a **Bellman-Ford**-ish based on a "unitarian" cost ("hops").
[v2-capacity_heuristic folder](./v2-capacity_heuristic): The same **priority based planning** as before but with a projecdt featuring capacity handling. Similarly, this one also makes use of a table built from Bellman-Ford-ish but based on a custom **capacity-centric** cost calculation inspired from **min-cost max-flow** rationale.