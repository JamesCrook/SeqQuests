# Why Star Trek?

SeqQuest's web interface is inspired by LCARS, the fictional computer interface from Star Trek: The Next Generation. The honest answer for 'why?' is that it seemed like fun to try. But after building and refining it, I found that LCARS has real advantages for bioinformatics work. These advantages actually arise from the constraints the LCARS designer was working under.

## A Design Born in TV Production

Michael Okuda designed LCARS for the Star Trek TV show, which imposed some unusual requirements:

- It had to be **instantly reconfigurable** for whatever the plot needed (weapons, medical, engineering)
- It had to look **believable as an expert interface** - something trained professionals would actually use under pressure
- It had to be **readable on camera** while actors performed in front of it
- It had to **not distract** from the action happening in front of the display
- The props/screens had to be inexpensive to make, leading to the innovative for its time flat panel controls - decades ahead of touch sensitive iPhones.

These constraints pushed the design toward modularity, high contrast, clear hierarchy, and drawing visual attention to the centre. These turn out to be useful properties for data-intensive software too.

## Peripheral Vision and the Foveal Region

Your peripheral vision is good at detecting color, shape, and motion, but poor at reading text. Your fovea, the central 2° of your visual field, handles fine detail. Traditional interfaces often fight this by scattering small labeled buttons across the screen, forcing you to look away from your data to find controls.

LCARS puts chunky, color-coded controls at the edges where peripheral vision works well. After brief familiarization, you *feel* where the controls are rather than searching for them. The center of the screen stays clear for the detailed content you actually need to read. Moreover blinking of the peripheral controls can draw your attention there, if it is needed.

In SeqQuest, the curved LCARS frames become functional buttons with labels. The panels they surround hold detailed information rendered in conventional, readable typography. Star Trek used labels just for effect, such as the 'DNGN' on a pipe for "Does Nothing, Goes Nowhere". In SeqQuest the labels are meaningful and say what the buttons do.

## Variable Button Sizes

Larger targets are faster to click (Fitts's Law). But most interfaces look awkward with mixed button sizes - it breaks the grid and appears unpolished. LCARS's organic shapes make varied sizes look intentional. I discovered this benefit after playing with the new LCARS-styled interface. In my design, frequently-used functions get large buttons; rare functions get small ones. Adding or removing buttons doesn't require repacking a layout. We always get a frame of buttons around the central panel.

## Color as Vocabulary

You perceive color before conscious thought engages. SeqQuest uses this by giving color subtle meaning - grouping display options in one color family, configuration in another. Hovering over any button highlights all buttons of that color, reinforcing the grouping. Users build intuition about what controls do, without re-reading every label.

## Serious Software, Playful Interface

The playful appearance might seem at odds with serious bioinformatics work. I think the opposite is true.

SeqQuest questions conventional approaches: Why accept less sensitive search methods when Metal acceleration can deliver sensitive search at 280 GCUPs? Why browse results with standard tree widgets when multiscrollers can handle larger hierarchies? The interface signals this same ethos of thinking outside standard conventions. I had to think about UI afresh, because of the changed design constraints.

The LCARS frame is a statement. Thoughtful, careful work can be enjoyable. The work inside the frame - a fast Smith-Waterman, a max-scoring trees, novel browsing interfaces - is where the substance lives. I'm hopeful that new, fun and enjoyable user interface will encourage other developers to develop other innovative approaches to bioinformatics. AI assistance makes coding up such ideas easier than it ever was before.