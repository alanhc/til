# Why Companies Can't Get Agentic AI Off the Ground: It's Not a Technology Problem — It's Four Organizational Walls

Over the past year, I've put agentic AI into a real development workflow, and I gave a talk on the topic at COSCUP. Seen from the tech community, agentic AI looks like the next productivity revolution. Seen from inside a company, most rollouts stall — and where they stall almost never has anything to do with the technology.

What actually kills a proposal to "let an AI agent take over the development of some module" is a handful of very human things: management feels it can't be controlled, no one knows who's responsible when something breaks, and colleagues fear being replaced. And even once it does ship, there's one more wall that fewer people talk about but that sits closest to the engineering floor — an agent dismantles a person's role and quietly relocates responsibility to code review, a place no one prepared for. I've watched all of this happen firsthand, and as it turns out, academia has already written it all up.

## Wall #1: Management Feels It "Can't Be Controlled"

When you propose letting an agent autonomously take over a stretch of development work, a manager's first reaction usually isn't "how accurate is it?" — it's "how do I control this thing?"

That's not conservatism; it's a reasonable instinct. When traditional code breaks, I have logs, stack traces, and tests to localize the problem. But an agent's reasoning process is a black box — when it makes a wrong decision, you often can't say which step broke. A system that can't be observed and can't be debugged is, for anyone accountable for outcomes, a system you don't dare put into a production flow.

This is precisely one of the core barriers the research identifies. A 2026 interview study of software engineering practitioners found that the key bottlenecks to agentic AI adoption include compatibility with existing legacy systems, responsibility attribution in shared decision-making, and the absence of governance frameworks for autonomous operation — and the non-deterministic nature of LLMs makes it especially hard for engineering teams to build trust. In other words, management's hesitation isn't emotional; it's a normal risk response to a system whose behavior can't be predicted and whose responsibility can't be traced.

## Wall #2: When Something Breaks, No One Knows Who's Responsible

This is the most lethal of the walls — academia has even given it a fixed name: the **accountability gap**.

An agent can be deployed, monitored, even audited, yet none of that answers the most basic question: when it does something wrong and causes a loss, who's responsible? When responsibility is implicit rather than explicitly assigned to a person, governance fails. Discussions around the NIST AI Risk Management Framework therefore argue that before an agent is allowed to act, a named business and technical owner must be assigned.

Industry framing puts it even more bluntly: AI agents lack the legal accountability, moral responsibility, and reputational incentives that ordinary employees inherently carry, so the consequences don't naturally land on anyone — governance has to actively fill that gap.

My own take: people are willing to answer for their own judgment because they can't escape it — they'll be reviewed, it'll affect their performance rating, it'll have career consequences. An agent has none of that. So when a process shifts from "this engineer is responsible" to "this agent is responsible," responsibility isn't transferred — it **evaporates**. That's what managers are truly afraid of.

And it gets worse: even if you want to assign an owner, you find responsibility isn't a *point* — it's a *chain*. The person who wrote the agent, the person who reviewed its output, the person who hit merge, the person who configured the automated checks — every link touched that code. When something breaks, each of them can reasonably say "it wasn't only me." This is exactly the "problem of many hands": when responsibility is spread across many hands, no single hand is responsible.

I think you have to be honest about this: **there's no clean right answer, and anyone who says "it should just be person X" is oversimplifying.** But it can be decomposed. The key is to separate two things that get conflated: *causal responsibility* (whose lapse produced the bug) — usually multi-causal, established after the fact — and *accountability* (who answers for it) — which the system assigns *in advance*, and shouldn't be argued about only after something breaks. Most organizational pain comes from thinking they're looking for the first (whose fault) when what they actually lack is the second (who's accountable) — and the second never had to equal the person who erred. Like aviation safety: the captain is accountable for the whole aircraft, which doesn't mean they tightened every screw.

The pragmatic move isn't to elect "the one person responsible" — it's to make *each link accountable for its own decision*: whoever designs the agent and its automated checks owns the *capability boundary* (what the agent is authorized to do, what the checks cover, whether that's reasonable); whoever reviews owns *that particular judgment* (given the information they had, should this change pass); whoever hits merge owns the *release decision* — the final gate. That's fairer than anointing a single super-owner, and far more auditable. Which is exactly why "merge authority exclusive to humans + immutable audit logs" matters so much: rather than argue about fault after the fact, make every decision leave a named trail beforehand. When something breaks, you don't argue — you read the log and trace each layer back.

Worth adding: a plane has a captain, but an agent pipeline has none by default — it's missing exactly that role that's accountable for the release as a whole. So merge authority isn't something that pre-exists and we assign; it's a captain we **deliberately manufacture**. That's also why "let the agent auto-merge" is so dangerous in accountability terms: it's a plane with no captain.

## Wall #3: Colleagues Fear Being Replaced

After the technical conversation and the governance conversation, this last wall is the quietest — and the hardest to take down.

When you ask a team to "use AI to take on part of the work," you think you're talking about efficiency. But what a frontline engineer may hear is a signal that the organization is preparing to replace this role. That feeling turns into silent resistance — nominal compliance, but in practice they route around it, treat it as a showpiece, and adoption never climbs.

There's a large body of empirical work on this in organizational behavior. The most-cited framework, STARA awareness, found that the more aware employees are of "smart technology, artificial intelligence, robotics, and algorithms," the lower their organizational commitment and career satisfaction, and the higher their turnover intentions. What should concern leadership more: these negative attitudes are often not simply about fearing unemployment, but about feeling that one's professional identity is under threat — AI disrupts not just tasks, but the psychological contract that gives the work meaning.

For a profession with as strong an identity as engineering, this gets amplified. What you're touching isn't their working hours — it's the thing that makes them who they are.

## Wall #4: When the Agent Dismantles Your Role, Who's Approving That PR?

The first three walls are about "whether to adopt." But once it's actually live, there's a finer and less-discussed wall: an agent doesn't cleanly replace a person — it **takes a role apart and reassembles it** — and that reassembly quietly moves responsibility to a spot no one was ready for.

Academia describes this more precisely than I'd expected. Research argues that reducing AI's impact to "replace vs. augment" isn't enough; what actually happens is task *chaining*: on one hand, AI pulls previously manual steps "under the hood" of a single task, narrowing the span of activity a human directly handles and shifting responsibility *within* a role; on the other, it lowers the cost of chaining steps across a job boundary, making it rational to redraw that boundary and reassign activities *between* roles. Put differently, an engineer's job gets split into execution, search, coordination, judgment, and accountability — the agent takes the first few, but "accountability" doesn't disappear with them. It just gets pushed downstream.

And where does it get pushed to? **Code review.**

This is my deepest takeaway from the past year, and the research happens to back it up. When an agent generates code at volume, the bottleneck shifts from *writing* code to *reviewing* AI-generated code — and every AI suggestion has to be read with suspicion until proven correct. Studies call this the *oversight burden* and note it's the most underestimated hidden cost of adopting AI in software engineering, sometimes consuming more effort than it saves.

More critically, where responsibility lands. A study on the future of code review in the AI era makes the point directly: automation doesn't eliminate accountability — it **redistributes** it. Human developers remain formally responsible, but as AI generates code, flags defects, and proposes fixes, evaluative authority blurs; respondents even described needing to "review the AI review," meaning oversight responsibility grows rather than shrinks. A paper proposing an agentic code review architecture puts it more firmly still: it deliberately keeps final merge authority exclusive to the human reviewer, backed by immutable audit logs, so that every AI-generated judgment is permanently tethered to the person who authorized it to ship. It invokes a vivid phrase — the "problem of many hands": when responsibility is spread across many hands, the result is that no hand is responsible.

To put it plainly for leadership: **when a module the agent wrote breaks, responsibility doesn't stop at the agent — it slides all the way down and stops at the reviewer who hit approve.** That means two things. First, code review is upgraded from a hygiene habit into the accountability anchor of the entire pipeline — it's *more* important after agents ship, not less. Second, if a company hasn't thought this through, it's effectively letting one engineer silently bear the full consequences of an AI output they may not even be equipped to fully review. That's unfair to the reviewer, and an undefended risk to the company.

And there's no free lunch here. Research points out that "review everything" causes velocity collapse — review overhead eats the entire productivity gain the agent brought — while "review nothing" produces unauditable, non-compliant code. So the answer isn't either/or; it's **risk-graduated human oversight** — high-risk changes bound tightly to human review and named responsibility, low-risk ones let through. Which loops right back to the first three walls: observable, named ownership, humans kept in the loop.

## So What Do You Do? — Directions, Not Answers

I won't pretend to have a complete solution, but after this year, here are the directions I think are worth pursuing:

**First, make the agent observable before you talk about autonomy.** Before trust is established, a human review checkpoint isn't the enemy of autonomy — it's the entry ticket that gives the agent a chance to be accepted. Understand it first, then loosen the reins.

**Second, treat "layered, named accountability" as a precondition for deployment, not an afterthought.** Stop asking "who's the one person responsible" — there isn't one. Make every decision in the chain named and logged: who authorized the agent, who approved, who merged, which checks passed at the time. The accountability gap isn't something technology can patch — it's something the system has to design for by distributing responsibility across layers up front. When something breaks, you should be able to read the log and trace it back, not argue about it in a meeting room.

**Third, make employees co-designers, not the ones being replaced.** Let engineers help define what the agent should and shouldn't do, and they shift from "the person under threat" to "the person holding the reins" — resistance loosens on its own.

**Fourth, design code review as the accountability anchor, and graduate it by risk.** Admit one thing: when an agent dismantles a role, the person hitting approve is where responsibility lands. Rather than let that happen silently, say it out loud — bind high-risk changes to human review and a named reviewer, auto-approve only the low-risk ones, and keep an auditable decision trail. This doesn't slow AI down; it keeps speed from bypassing responsibility.

Agentic AI often fails to get off the ground not because it isn't capable enough, but because it exposes the holes that already existed in a company's governance, accountability, people, and division of labor. The technology will keep improving — but these walls, the organization has to take down itself.

---

## References

**Academic papers (peer-reviewed / preprints)**

1. Apostolou, S. A., Bosch, J., & Holmström Olsson, H. (2026). *Agentic AI in Industry: Adoption Level and Deployment Barriers.* arXiv:2605.14675. https://arxiv.org/abs/2605.14675
   — Interview study across 16 practitioners at 12 companies; introduces a "capability–deployment verification gap" and identifies barriers such as legacy compatibility, non-determinism, and data confidentiality. (Wall #1)

2. Brougham, D., & Haar, J. (2018). *Smart Technology, Artificial Intelligence, Robotics, and Algorithms (STARA): Employees' perceptions of our future workplace.* Journal of Management & Organization, 24(2), 239–257. https://doi.org/10.1017/jmo.2016.55
   — The original STARA awareness paper. Greater awareness correlates with lower organizational commitment and career satisfaction, and higher turnover intentions, cynicism, and depression. (Wall #3)

3. *Chaining Tasks, Redefining Work: A Theory of AI Automation.* (2026). arXiv:2606.15960. https://arxiv.org/abs/2606.15960
   — Argues the "replace vs. augment" dichotomy is insufficient; AI shifts responsibility within roles and redraws job boundaries through task chaining. (Wall #4: role reconfiguration)

4. *The Integrator Advantage: Controlled Agentic AI for Small and Medium-Sized Companies.* (2026). arXiv:2606.16649. https://arxiv.org/abs/2606.16649
   — Decomposes a role into execution, search, coordination, judgment, accountability, etc.; argues agents take the front end while humans retain context and responsibility. The right question is "which human time can be multiplied," not "who can be replaced." (Wall #4)

5. *Quo Vadis, Code Review? Exploring the Future of Code Review.* (2025). arXiv:2508.06879. https://arxiv.org/abs/2508.06879
   — Empirical interviews showing automation redistributes rather than eliminates accountability; human reviewers must "review the AI review," expanding oversight responsibility and raising legal exposure. (Wall #4: code review as accountability anchor)

6. *Rethinking Code Review in the Age of AI: A Vision for Agentic Code Review.* (2026). arXiv:2605.17548. https://arxiv.org/abs/2605.17548
   — Proposes keeping final merge authority exclusive to human reviewers, backed by immutable audit logs tethering each AI judgment to its authorizer; invokes the "problem of many hands." (Wall #4)

7. *Human Oversight and Overload: Two Hidden and Costly Burdens of AI-Assisted Software Engineering.* (2026). arXiv:2606.05770. https://arxiv.org/abs/2606.05770
   — Notes the bottleneck has shifted from writing code to reviewing AI-generated code; introduces the "oversight burden" as the most underestimated hidden cost. (Wall #4)

8. *Governed AI-Assisted Engineering: Graduated Human Oversight for Agentic Code Generation in Regulated Domains.* (2026). arXiv:2606.22484. https://arxiv.org/abs/2606.22484
   — Shows "review everything" causes velocity collapse and "review nothing" causes non-compliance; argues for risk-graduated human oversight. (Wall #4 and the closing directions)

**Industry reports & governance frameworks (not peer-reviewed; for further reading)**

9. IBM (2026). *The accountability gap in autonomous AI.* https://www.ibm.com/think/insights/accountability-gap-autonomous-ai
   — Notes enterprises often lack the ability to monitor agent behavior, review automated decisions, and attribute responsibility after the fact. (Wall #2)

10. SPHERE / NHIMG (2026). *AI Agent Ownership — An Underlying NIST AI RMF Control.* https://nhimg.org/community/agentic-ai-and-nhis/ai-agent-ownership-and-accountability-gaps-in-ai-governance/
   — Argues a named business and technical owner should be assigned before an agent is allowed to act, treating ownership as a prerequisite control for governance. (Wall #2)

> Note: Items 3–8 are largely 2026 preprints (arXiv) that have not yet been peer-reviewed; consider labeling them as such in formal contexts. Items 9–10 are industry/governance pieces rather than academic papers; the "named owner" and "human-in-the-loop checkpoint" arguments are echoed consistently across BCG, MIT Sloan Management Review, OECD, and the EU AI Act (Articles 12–14), which can be cited for further verification.
