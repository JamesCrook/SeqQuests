# Accessibility

The web interface for SeqQuests uses some new user interface paradigms which are not known/understood by existing screen readers. In Open Source software development there is a strong ethos of accessibility - making the same interface work for colour blind and visually impaired users. Non standard interface elements may require ARIA tags to make them more usable. Even so that may not be 'enough'.

Experience with working on Audacity - Open Source audio software that is valuable to blind people - I saw very clearly that one cannot fully replace some visual cues or drag-style interactions. For example the waveform view and spectrogram view in Audacity are of no use to blind users. Selecting a range of audio needs audio feedback, not visual feedback, for the blind. Navigation of menus and dialogs also has significantly different demands on it for blind users using JAWS than it does for sighted users.

I came to the opinion that visually impaired users would benefit most from exposing the underlying workhorse elements via scripting. Then custom scripts and pipelines for that user's needs could be built purely in text. Custom audio menus could be built around that. For reasons of automatability, AI-assisted development and custom pipelines, SeqQuests is already built on CLI commands. In this it follows tools like SoX and Git, which are CLI first, with GUI as an overlay. 

## Automating GUI Overlay

SeqQuests attempts to generalise the process of providing GUI overlay over CLI commands.

* The job-runner script converts a long running script into a job that can be managed by a web UI. Specifically it captures summary and detailed progress information, start, pause, stop, configuration.
* The tree browser panel converts any large ASCII tree (as produced by some of the tools) into a browsable tree. The tree can be scrolled and breadcrumbs followed.  

## Experimental GUI

SeqQuests includes novel GUI elements such as the LCARs user interface, protein stream plots and multiscrollers. The route I'm choosing is to explore and develop these without putting ARIA and accessibility features first - thoughtful provision of workhorse features as script has bigger yield, and like waveform views of audio, some aspects won't work for visually impaired or blind. As the experimental methods mature the actual structural reasons for wins become clearer, and for example these can motivate scripting level tools that fill the gap that web UI maybe can't. For example the stream plot of proteins may be better served, for visually impaired, by a CLI tool that does scriptable 'sliding window' analysis of a sequence, and announces important transitions. In the Web UI it is built into the stream plot as a developer made decision. For a CLI it could be user customisable.