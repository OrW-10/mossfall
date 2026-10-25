# Mossfall — The Guardian’s Trial

A small, single-player RPG and fighting game built entirely with HTML, CSS, and JavaScript. Explore a lively forest village, challenge its guardian, and earn your license to venture into the Whispering Woods.

![Mossfall village](screenshots/village.png)

## Play locally

Download or clone this repository and open `index.html` in a modern browser. No build, installation, server, database, API keys, or internet connection is required. The game, styles, and procedural artwork are contained in one HTML file.

## Play from a repository link

GitHub Pages can host this game directly. GitHub currently rejects Pages for this private repository on the owner's plan, so there is no live game link yet. Viewing `index.html` on GitHub shows its source rather than running the game.

To enable hosting, use a plan that supports Pages for private repositories, or make this repository public. In **Settings → Pages**, select **Deploy from a branch**, choose **main** and **/ (root)**, and save. The repository includes `.nojekyll` for static hosting. Pages serves static files only; the game still runs entirely in the player's browser.

After Pages reports a successful deployment, the expected address is `https://orw-10.github.io/mossfall/`. Add a prominent README hyperlink using:

```markdown
[Play Mossfall](https://orw-10.github.io/mossfall/)
```

## Controls

| Action | Keyboard |
| --- | --- |
| Explore | WASD or arrow keys |
| Talk, greet animals, or use a gate/trail | E near the target |
| Inspect earned forest license | I or the Forest license button |
| Move during a duel | A / D or left / right arrows |
| Jump | Space, W, or up arrow |
| Strike | J |
| Heavy attack | K |
| Guard | Hold L |
| Pause | Escape or the Pause button |

On-screen controls are available on small screens and touch devices.

## The adventure

Explore a village with tiled cottages, smoking chimneys, flower beds, a lily pond, birch trees, drifting leaves, and butterflies. Mira the herbalist and Bram the woodcutter walk around the village and offer advice. Greet Pip the cat and Clover the chicken with **E** nearby to see their reactions.

Approach Rowan at the stone circle and accept his challenge. Manage health and stamina, watch for gold heavy-attack wind-ups, and block or jump before counterattacking. The duel ends in a knockout or after 90 seconds; the fighter with more health wins at timeout. A draw or defeat does not award a license.

Your first victory grants a signed **Forest Venture License**. Inspect it with **I**, then approach the north gate and press **E** to enter the Whispering Woods. Explore its winding trail, stream, mushrooms, and wildlife; greet Fern the deer or Ember the fox. Use **E** at the south trail sign to return to Mossfall. You may rematch Rowan, and later losses do not revoke your license.

The license and duel scores last for the current visit. Refreshing resets the game. There is no persistent save system, multiplayer, or audio.

![Forest license](screenshots/license.png)

![Whispering Woods](screenshots/forest.png)

## Project files

- `index.html`: the complete offline game, including HTML, CSS, JavaScript, and procedural artwork.
- `screenshots/`: desktop, forest, license, and mobile previews.
- `tests/test_game.py`: repeatable Playwright regression checks.
- `tests/requirements.txt`: optional development dependencies; not required to play.
- `.nojekyll`: enables direct static-file hosting with GitHub Pages.

## Browser verification

Install the optional test tools in a Python virtual environment, then run from the repository root:

```sh
python -m pip install -r tests/requirements.txt
python -m playwright install --with-deps chromium
python tests/test_game.py
```

Tested in headless Chromium. Checks cover movement, NPC dialogue, animal reactions, AI combat, guard and stamina mechanics, jumping, pause/resume, rematches, license rewards, locked forest access, return travel, mobile controls and layout, and session reset. Controlled game states cover win/loss/draw reward boundaries. Screenshots are regenerated in `screenshots/`. No HTTP/API requests or JavaScript runtime errors are expected.
