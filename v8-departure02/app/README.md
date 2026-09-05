MAPF Classroom Editor - current state

Goal:
Build a graph editor on top of PNG classroom layouts for MAPF evacuation scenarios.

Technology:
- FastAPI backend
- HTML/Javascript frontend
- Canvas rendering
- JSON only used for browser communication
- Main config format is custom text format

Current functionality:
✓ Load PNG background
✓ Place nodes with coordinates
✓ Node model:
    - name
    - category
    - attributes
        - color
        - max_drones
✓ Edit node properties
✓ Export node configuration
✓ Create edges in edge mode
✓ Prevent duplicate edges
✓ Render edges
✓ Show edge table/context view

Current decisions:
- Nodes have categories.
- Edges have attributes but no categories.
- Edge attributes:
    - max_link_capacity
- Do not implement deletion yet.
- Avoid UUID migration for now; project currently uses names.
- Consider UUID/internal IDs later.

Next planned step:
1. Edge attribute editing.
2. Close/open edge table behaviour.
3. Improve export for connections.

Future:
- Node deletion with edge cleanup.
- Edge deletion.
- Zones.
- Initial occupancy for evacuation scenarios.
- MAPF simulation integration.

If you paste something like that into a future chat, it will restore almost all of the important context quickly.

And about the model: newer iterations can indeed feel different. A lot of what made this session productive was not only code generation; it was the iterative design conversation. Your corrections shaped the result:

rejecting premature complexity;
distinguishing categories from attributes;
insisting that UX matters;
questioning edge interaction;
postponing deletion;
keeping the existing config philosophy.

Those decisions are what made the implementation converge.

Also, one thing I would explicitly preserve: the editor is not yet "just a MAPF tool". The direction it naturally evolved into is a small environment modelling tool:

physical layout
      ↓
graph representation
      ↓
constraints/capacities
      ↓
MAPF scenario
      ↓
simulation

That is a much stronger foundation than a one-off exercise solver.

Enjoy the feeling of having a working piece. 🙂 When you come back, start with the handover notes and we can continue from "edge attribute editing" rather than rebuilding the whole discussion.