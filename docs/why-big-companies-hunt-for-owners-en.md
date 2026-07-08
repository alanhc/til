# Why Big Companies Are Forever Hunting for an Owner — From the Problem of Many Hands to Accountability Sinks, and How AI Agents Are Reshuffling the Deck

## A Scene Every Engineer Knows

Something breaks. A cross-team meeting convenes. The dashboard on the screen is red. The first thing out of the manager's mouth is not "what's the root cause?" It is—

"Who owns this?"

The next twenty minutes are not spent on the fix. They are spent on a precise exercise in boundary-drawing: is this a platform issue or a driver issue? A CI environment problem or a code problem? Our module, or the neighboring team's dependency? Everyone in the room is doing the same thing: proving that the arrow does not point at them.

If you have worked at a large company, you know this is not a pathology of any particular firm. It is close to a universal behavioral pattern of large organizations. And here is the interesting part: this pattern has more than forty years of scholarly lineage behind it—it has a name, a theory, a set of solutions, and a complete record of how those solutions fail. More importantly, as AI agents enter the workflow, this old problem is reopening in a new form.

## Layer One: Hunting for an Owner Is Rational — The Problem of Many Hands

Let us first say something in the organization's defense: hunting for an owner is not bureaucratic disease. It is a rational response to a genuine dilemma.

The political scientist Dennis Thompson named this dilemma in 1980: the **problem of many hands** [1]. When an outcome is produced by many hands together, no single individual can reasonably be held responsible. Everyone contributed only a small piece; each piece, viewed alone, is beyond reproach; together they add up to a disaster—and when the disaster arrives, you cannot find "the person responsible," because that person does not exist.

Psychology supplied an even earlier experimental foundation. Darley and Latané's 1968 bystander experiments demonstrated the **diffusion of responsibility** effect [2]: the more people present, the lower the probability that any one of them acts. Transposed into an organization, the corollary is brutal—the more recipients on an email, the less likely anyone replies; the more attendees in a meeting, the less likely anyone decides; the more names attached to a project, the less likely anyone is actually watching it.

So when organizations hunt for an owner, they are fighting something close to a law of human physics. Responsibility must converge on a single name before anything moves.

## Layer Two: The Industry's Solution — One Name, and Not One More

The tech industry has developed a mature, institutionalized answer to the problem of many hands, and the versions across companies are strikingly consistent: **force the number of accountable people down to one.**

Apple's version is the **DRI (Directly Responsible Individual)**: every project, every feature, every action item in every meeting must carry a name. Not a department. Not a team. A name.

Amazon's version is the **single-threaded owner**, documented at length in *Working Backwards* [3]: anything important must have a "single-threaded" leader—someone who does not moonlight, does not simultaneously own anything else, someone who thinks about this one thing every waking moment. Amazon's logic: a part-time owner equals no owner, because when two commitments collide, one of them will be sacrificed, and the sacrificed one is, in effect, ownerless.

Even the much-maligned RACI matrix was designed around the same idea: R (responsible for execution) can be many people, but A (ultimately accountable) can hold exactly one name per cell. When RACI fails in practice, it usually is not because the framework is wrong—it is because the organization could not resist filling the A column with a crowd of names, which is to personally invite the problem of many hands back in.

Up to this point the story is a positive one: the problem of many hands is real, and the single-owner institution is an effective answer. But it is not that simple—the answer has three structural limits, each backed by solid empirical research.

## Layer Three: The Limits of the Solution — Some Systems Are Born Many-Handed, and Owners Change

**Limit one: not everything can converge on a single name.**

The most-cited empirical study of ownership in software engineering is Bird et al.'s 2011 analysis of Windows Vista and Windows 7 [4]: the lower a component's top-owner proportion and the more low-expertise contributors it has, the more pre-release faults and post-release failures it suffers. The paper is routinely invoked as proof that single ownership works—but the same study revealed the other side: low-expertise contributors touching other people's code is, for the most part, not an indiscipline problem but a structural inevitability. They are usually forced to modify someone else's territory because of dependencies and interfaces belonging to their own components. The deeper the coupling between components, the more "every file has a clear owner" approaches a fiction.

Platform layers, CI pipelines, shared test resources, infrastructure that spans product lines—these "commons" components are the extreme case: every team touches them, every team depends on them, yet hanging any of them on a single individual is a name without substance. This is also why a tradition within the agile movement advocates collective code ownership: rather than maintain a nominal single owner, let the whole team hold the code together, replacing boundaries with norms and tests. That path has its own failure mode (collective ownership degrades easily into no ownership, which is the many-hands problem all over again), but its very existence makes the point: the single owner is not a universal solution. It is a tool with a bounded domain of application.

**Limit two: owners change, and the cost of the change is large enough to quantify.**

The owner column on the org chart looks static; in reality it churns continuously—resignations, internal transfers, reorgs, product-line handoffs. The empirical estimates of this cost are unforgiving.

Mockus's 2010 study found that developer-centered measures of organizational volatility—people leaving, structures being reorganized—predict customer-reported defects [5]. In other words, an owner change is itself a leading indicator of defects. Even earlier, in 2009, he had proposed a way to measure **succession** [6]: when code passes from a departing developer to a successor, the quality of that transfer can be tracked and evaluated—which amounts to admitting that an owner change is not an HR event but an engineering process with costs, risks, and a need for management.

Rigby, Mockus, and colleagues took the accounting to its conclusion in 2016 [7]: using Chrome and a project at Avaya as case studies, they borrowed methods from financial risk analysis to quantify turnover-induced knowledge loss, and found that projects are susceptible to losses more than three times larger than the expected loss—over five times larger in historical simulations. Translated into management language: if you plan owner transitions around the "average handover cost," you are systematically underestimating tail risk. The worst case is not 1.5x the average. It is three to five.

**Limit three: organizations do not follow their own solution — part-time owners and percentage-slicing.**

Amazon's single-threaded logic is explicit: the owner must not moonlight. Yet in reality, driven by headcount costs, most organizations do exactly the opposite—one person simultaneously holds a system-integration role and a module-owner role, and the standard management artifact is an allocation sheet reading "30% on A, 70% on B." Organizational research has a formal name for this: **multiple team membership (MTM)**, and it is no fringe phenomenon—Mortensen and Gardner's 2017 survey in *Harvard Business Review* reported that in global companies, belonging to multiple teams at once is the norm for 81% of managers [9].

The foundational theory here is O'Leary, Mortensen, and Woolley's 2011 model [8]: organizations use MTM to chase a double dividend of productivity and learning, but the structure imposes competing pressures on members' attention and information processing that make it hard to raise both at once—the number and variety of memberships is something to be carefully balanced, not a resource that stacks without limit.

The deeper problem is the metric itself. A percentage assumes attention can be sliced linearly, like machine-hours: invest 30% of the time, harvest 30% of the output. The empirical record rejects that assumption. Zika-Viktorsson and colleagues' 2006 study of multi-project settings introduced the concept of **project overload** [10]: the fragmentation and frequent switching of multi-project work correlate with psychological stress reactions and impaired competence development—fragmentation eats not only output but growth. In software engineering, Vasilescu et al.'s 2016 large-scale longitudinal study of GitHub [11] found that developer output depends on the balance among project count, focus, and project diversity: multitasking has measurable cognitive limits—the paper's title, *The Sky Is Not the Limit*, is itself the conclusion. The most widely circulated rule of thumb in industry comes from Weinberg: each additional concurrent project costs roughly 20% of one's time to switching. That is a heuristic, not rigorous evidence—but it points in the same direction as the research that followed: switching costs appear on no percentage sheet. They are an invisible tax levied outside the ledger.

And percentage-slicing carries one deeper contradiction, straight back to Amazon's logic: when the 30% role and the 70% role collide, the 30% commitment is effectively ownerless. A percentage is not the intensity of a commitment; it is the priority order of its sacrifice—an owner cut in half is not two half-time owners, but two owners each liable to drop to zero at any moment. The allocation sheet manufactures an accounting illusion that "everything is covered by someone." But attention is not an accounting entry.

Together, the three limits explain a phenomenon large companies routinely overlook: **there exists an entire class of roles—systems integration, build/CI operations, cross-team triage, program management—whose actual job content is to keep paying, day after day, for the problem of many hands and the cost of owner change; and the irony is that these are precisely the roles most often percentage-sliced.** The single-owner institution did not eliminate the many-hands problem. It merely pushed it out to the boundaries between components; and the collisions at those boundaries, the knowledge gaps left after names change, and the invisible tax of switching all need someone to absorb them daily. The existence of these roles is not organizational inefficiency—it is the organization honestly pricing the limits of its own solution. Provided, of course, that the pricing is honest, rather than a pretense that the percentage sheet has already counted the cost.

## Layer Four: The People in the Middle — The Structural Predicament of Boundary Roles

The previous layer said someone is paying for the system. This layer asks how the people doing the paying are faring. The answer: organizational research has studied this position for nearly fifty years, and the findings are remarkably consistent—**people standing on boundaries suffer penalties that come from the position, not from their performance.**

Start with how critical the role is. Tushman's foundational 1977 study in *Administrative Science Quarterly* (345 subjects across 58 projects in R&D laboratories) identified special boundary roles—gatekeepers and liaisons [12]: effective information flow across boundaries is accomplished only by the few individuals who are well connected both internally and externally. In other words, integration and coordination are not "chores anyone can do." They are a scarce capability—the first conclusion of this literature, and the one organizations forget most often.

But critical does not mean comfortable. Kahn et al.'s 1964 classic on role conflict [13] describes the predicament of the "focal person": someone on whom multiple role senders—managers, partner teams, downstream customers—simultaneously project expectations. When those expectations are incompatible, the focal person bears role conflict, which, in the original text's words, in persistent and extreme form is "not merely irritating" but "identity destroying." Two findings from this research tradition land squarely on the "sandwiched" experience. First, follow-up analyses showed that experienced conflict intensity correlates with the diversity of the role set—people in frequent contact with other parts of the organization experience the strongest conflict, and the greater the organizational distance of the role set (the more levels and departments spanned), the greater the conflict. Second, one of Kahn's principal findings: objective conflict converts into subjective strain when the role set is powerful. Stack the two findings: **a low-ranked person facing a high-power, high-diversity, high-organizational-distance ring of role senders is the most painful configuration role-conflict theory can describe—and it is the daily reality of systems-integration roles in large companies.**

Now consider "being challenged." The sociological review of brokerage—Stovel and Shaw, 2012, in the *Annual Review of Sociology* [14]—identifies a fundamental duality: brokerage eases interaction, enables economic activity, and facilitates cooperation; and at the same time it routinely attracts suspicion of self-dealing, accusations of exploitation, and the reproduction of inequality. Being questioned about "misusing resources" is a structural interrogation of the broker's position, not of the broker's character: **each side can see only the cost you spend on their side; neither side can see the coordination cost you save for the whole**—because when coordination cost is saved, it appears on nobody's report; only when coordination fails does everyone suddenly see you. A middleman's output is inherently counterfactual: the better you do the job, the less anyone knows you did it.

Finally, the matter of rank. Babcock and colleagues, writing in the *American Economic Review* in 2017, introduced the concept of **non-promotable tasks** [15]: work that is critical to the organization's functioning but useless to the performer's advancement, and whose allocation is systematically biased—it tends to land on those for whom refusal is most costly. The engineering world's practitioner version is Reilly's "Being Glue": the work of cross-team coordination, decomposing ambiguous problems, and making sure nothing falls on the floor is *glue work*, and it carries a cruel asymmetry—the same work, done by a senior person, is called leadership; done by a junior person, it risks being scored at review time as "not technical enough." This closes a self-reinforcing loop: **coordination work does not count toward promotion → rank stays put → low rank makes the "misused resources" challenge easier to sustain → and a sustained challenge further suppresses the visibility of the work.** Every step of the loop is locally rational for each party; the sum is the systematic depreciation of the organization's scarcest role.

The conclusion of this layer deserves to be said plainly: if you find yourself as the person in the middle, what the literature offers you is not consolation but a diagnosis—the conflict, the suspicion, and the stalled rank you experience are structural products of the boundary position, written into the textbooks fifty years ago. The question that actually deserves to be challenged is this: why does an organization that runs on its boundary roles place those roles in the positions with the least power?

## Layer Five: The Dark Side — When Hunting for an Owner Becomes an Accountability Sink

In 2024, the economist Dan Davies introduced a concept that has spread rapidly through management circles: the **accountability sink** [16].

Davies's observation: large organizations evolve structures that delegate decisions to rulebooks, standard procedures, or computer systems, so that "the person who decided" vanishes from the system. When your flight is canceled, your insurance claim denied, your purchase request bounced, the person behind the counter tells you: "It's the system. There's nothing I can do." They are telling the truth. The decision really wasn't theirs—but it also wasn't made by anyone you can find. Responsibility has been sucked into a sink, never to return.

Davies's key insight: for an accountability sink to hold, one link must be severed—**feedback from the people affected by a decision must be unable to reach the system that made it.** With the feedback loop cut, errors can be neither attributed nor corrected.

And here comes an uncomfortable inference: **organizations' enthusiasm for finding an owner is sometimes not about solving the problem, but about pre-arranging where the blame will land.** The public-administration scholar Christopher Hood documented this behavior systematically in *The Blame Game* [17]: organizations carefully engineer structures to deflect and distribute blame, and "designating an owner" is the cheapest blame insurance available—when things go wrong, the sink is already dug and the name already filled in.

This explains the strange scene in the meeting room: why everyone spends twenty minutes drawing boundaries instead of fixing the problem. Because everyone intuits that being designated the owner at that moment confers not resources and authority, but a pre-paid blame invoice.

## Layer Six: The Name Can Be Found; the Ownership Cannot

Here lies a pair of concepts organizations chronically conflate but scholarship keeps sharply distinct.

The management scholars Pierce, Kostova, and Dirks, in their work on **psychological ownership** [18], point out that "being designated the owner" and "genuinely feeling this is mine" are two different things. The former is a label on an org chart; the latter is a psychological state—and only the latter produces the behavior organizations actually want: proactive maintenance, long-term investment, treating the system's health as one's own concern.

Psychological ownership has three wellsprings: a sense of control over the target, intimate knowledge of it, and investment of the self into it. Note what the three have in common: none of them can be produced by assignment. You can hang a legacy system on an engineer's name in the org chart, but if he has no control over it (changes require five layers of approval), no deep knowledge of it (the documentation is lost, the original authors gone), and no self invested in it (he inherited it last year), then what you have obtained is an owner's name and zero ownership.

Here is the true dilemma of the owner hunt: **what the organization needs is ownership, but the institution can only manufacture owners.** The name gets filled in, the sink gets dug, but the person who "thinks about this one thing every waking moment" does not materialize from an assignment email.

## Layer Seven: The AI Agents Arrive, and the Old Problem Reopens

The six layers above are the story before AI. The arrival of agentic AI is resurrecting this forty-year-old problem in a new form.

The philosopher Andreas Matthias predicted it in 2004, under the name **responsibility gap** [19]: traditional responsibility ascription rests on two conditions—control and foreseeability. You controlled the behavior, you could foresee the consequences, therefore you are responsible. But the behavior of learning, autonomous systems exceeds what their designers can predict; when a system does something no one instructed and no one could foresee, the chain of responsibility snaps.

Santoni de Sio and Mecacci went further in 2021 [20]: the responsibility gap that AI brings is not one problem but at least four interrelated gaps—culpability, moral accountability, public accountability, and active responsibility—and the introduction of AI sharpens the original problem of many hands, because data and decisions are introduced and processed at ever more nodes along the chain, making it ever harder for those affected to find whom to ask.

Translate the abstraction into the language of the engineering floor:

An AI agent in your CI pipeline autonomously fixes a bug, opens a PR, gets merged into production—and three weeks later it blows up. Now, how do you answer the meeting-room question, "who owns this?" The person who wrote the prompt? The manager who approved the agent's rollout? The engineer who reviewed the PR (he spent ninety seconds)? The model vendor? Or the person listed as "agent owner," who neither wrote that code nor ever read it?

The organization's instinct is to reuse the old solution: find an owner, hang the agent on his name. But that is exactly the problem—**this owner is being asked to take full responsibility for output he did not write, did not read, and cannot fully predict.** He has the owner's name, but he cannot possibly have the three wellsprings of psychological ownership: control (the agent is autonomous), intimate knowledge (the output volume exceeds what a human can read), invested self (it is not his work). This is an ownership that is structurally hollow by construction.

And the handover cost from Layer Three recurs here in a worse form: the agent itself never resigns, but the agent's owner does. When a human owner hands over a system he wrote himself, he at least has documentation, commit history, and the decision context in his head to transfer; when he hands over an agent plus its accumulated configuration, prompts, boundary rules, and exception lists—a bundle even he only partially understands—the "three-to-five-times" tail risk from the succession research is probably still an underestimate.

**And when organizations begin demanding that employees process work "in parallel" and supervise multiple agents "in parallel," percentage accounting loses whatever residual validity it had.**

The first problem is cognitive. Dual-task research in psychology long ago established that human central cognitive processing has a serial bottleneck [29]: two tasks that require thought cannot truly run at once; they can only queue. Rubinstein, Meyer, and Evans's 2001 experiments measured the price of switching [30]: every switch between tasks carries a measurable time cost, and the more complex and less familiar the tasks, the higher the cost. What we call "parallel processing" is, cognitively, high-frequency serial switching plus a tax on every switch—a tax for which the percentage sheet has no line item.

The second problem is that "supervising multiple autonomous systems" has already been quantified—just in another field. Human-robot interaction research, in the context of unmanned vehicles, developed the **fan-out model**: Olsen and Wood proposed at CHI 2004 [31] that the number of autonomous systems one person can operate simultaneously is governed by the ratio between the systems' neglect time (how long each can be left alone) and interaction time (how long each intervention takes); robot attention demand and interaction effort are the field's standard measures. Two findings from that literature should alarm anyone in the agent era: first, once later models incorporated wait times and attention-switching costs, feasible fan-out proved lower than the original estimates; second, even within this specialist field, methods for predicting "how many can one person supervise" have produced inconsistent results to this day—**the thing the drone field could not pin down in twenty years, the management floor settles with one percentage sheet.**

The third problem is the temporal structure. Supervisory work is bursty and interrupt-driven: when an agent needs a human is not decided by the owner's calendar. Mark and colleagues' classic 2008 study of interrupted work found [32] that interrupted workers compensate by finishing faster—at the price of significantly higher stress, frustration, and time pressure. And the basic result of queueing theory (brought systematically into product-development management by Reinertsen [33]) says: as resource utilization approaches 100%, waiting time explodes nonlinearly—filling a person to 100% by percentages guarantees that every agent he supervises will be standing in line at the moment it needs a human. **Agents can run in parallel. Their owner's attention cannot be given in parallel.**

Put the three together and the conclusion is: percentage accounting was merely inaccurate in the era of human multitasking; in the era of agent supervision it is measuring the wrong dimension. It measures how time is sliced, while the true cost of supervisory work lies in the distribution of interruptions and queueing delays. The right question is not "what percent of your time goes to each thing?" but "after your interaction times are summed, how much neglect tolerance does this system have left?"—and the latter, at present, appears on no management report anywhere.

And Davies's warning turns piercing at this moment: delegating decisions to algorithms is the most convenient way to build an accountability sink. If organizations do not redesign accountability, AI agents will not solve the problem of many hands—they will become the largest hand in history: a hand with no name, no psychological state, and no way to be blamed. And the human owner whose name hangs on it is merely the signboard at the sink's entrance.

**Finally, the arrival of AI hands individual employees a brand-new double bind.**

Many organizations now issue two directives to their employees at once. The first is explicit: "spend X% of your time studying AI." But Layer Three already established that percentages are an accounting illusion—and of all activities, learning happens to be the one most sensitive to time fragmentation. Zika-Viktorsson's project-overload research showed long ago [10] that what fragmentation damages most is not just output but competence development itself. "AI research time" sliced into slivers buys not research, but a record of having researched.

The second directive is implicit, and points the other way. Reif, Larrick, and Soll, in four preregistered experiments (4,439 participants) published in *PNAS* in 2025, found [21]: people who use AI at work both anticipate and receive negative social evaluations of their competence and motivation—they are seen as lazier, less capable, more replaceable—and the penalty holds consistently across occupation, age, and gender. More ironic still: the harshest evaluations come from assessors who do not use AI themselves. The authors frame it as a paradox: a productivity-enhancing tool that simultaneously damages its user's professional reputation. The consequence is predictable—participants were significantly less willing to disclose their AI use to managers and colleagues.

Stack the two directives and you have a double bind in Bateson's sense [22]: "you must adopt AI" and "adopting AI will be punished" hold simultaneously, and—this is Argyris's classic description of organizational defensive routines [23]—**the contradiction itself is undiscussable.** In the vast majority of organizations, no one can say in a meeting, "we are demanding that employees learn AI while punishing them for using it"—because the person who points out a mixed message is usually treated as the problem. Argyris laid out the full defensive routine: send inconsistent messages, deny the inconsistency, then make the denial itself undiscussable.

**And resource scarcity twists the double bind tighter.** When headcount is already short, every minute an employee spends on AI draws simultaneous challenge from two directions—and the phrasing of those challenges is strikingly uniform across industries, each with a classic theory behind it.

The first challenge comes from the management side: "You can't even finish your core work—why are you fiddling with AI?" This is the structural bias March described in his 1991 classic of organizational learning [24]: organizations naturally favor exploitation (harvesting certain, near-term returns from existing capabilities) at the expense of exploration (building new capabilities with distant, uncertain returns)—because exploration's payoffs are further away in time and more dispersed in probability, it loses every round of the resource competition. Nohria and Gulati's 1996 empirical work adds the role of slack [25]: slack (resources in excess of the minimum necessary) has an inverted-U relationship with innovation—**in the absence of slack, experimentation cannot be sustained at all, because experimental outcomes are inherently high-variance.** Translated: a resource-starved organization telling its employees to "study AI" is asking them to do something statistically guaranteed to fail a few times, inside an environment structurally unable to tolerate failure. Mullainathan and Shafir's research on scarcity [26] explains the management side's field of vision: scarcity tunnels attention—people whose bandwidth is taxed by the urgent are structurally unable to see the value of long-term investment. Managers do not fail to understand that AI matters; scarcity ensures that everyone sees only the core work inside the tunnel.

The second challenge comes from peers: "How come you have spare time for AI?" This belongs to a different lineage. Adams's equity theory [27] holds that people continuously compare their input–output ratios with others', and perceived inequity triggers strong corrective motivation—in an everyone-is-firefighting environment, any visible time spent on non-firefighting work is read directly as "your load is lighter than mine," regardless of whether it was assigned. Bellezza and colleagues' 2017 research [28] adds the cultural layer: in a workplace culture where busyness itself has become a status symbol, visible non-core time is not merely a load signal—it is a status violation. So in a scarce organization, the directive to "spend X% on AI" leaves its executor besieged on three fronts: the management side's exploitation bias, peers' equity comparisons, and one's own scarcity-tunneled attention—**the moment the directive is issued, the organization has already deployed every mechanism required to punish its execution.**

And here the double bind converges with the article's main line: when AI adoption stalls, the organization finds an owner and asks "why isn't this moving?"; when AI use goes wrong, the organization finds an owner and asks "why did you use it?" The same person can perfectly well be the owner of both questions. Facing this configuration, the individually rational response is shadow AI—use it quietly, disclose nothing—and shadow AI happens to be the worst case for any accountability structure: **usage maximized, accountability minimized.** With its own evaluation culture, the organization has pushed AI use into the sink with its own hands.

## Closing: Three Questions for the Organization

This essay does not offer a complete solution—that would take another essay. But before an organization rushes to assign an owner to every AI agent, three questions deserve answers first.

**First: are you looking for an owner, or for a place to park the blame?** The test is simple: look at whether the owner receives authority or only obligations. If he has the power to stop the agent, to change the agent's boundaries, to veto the agent's output—that is ownership. If he is merely the person who writes the report when things go wrong, that is the signboard on an accountability sink.

**Second: does your accountability structure preserve the feedback link?** Davies's criterion bears repeating: a sink exists precisely where feedback is severed. The people affected by the agent's output—downstream teams, customers, engineers carpet-bombed with review requests—can their feedback genuinely change how the agent operates? If not, you are already digging.

**Third: what do you actually want—a name, or a psychological state?** If the latter, assignment is not enough. Psychological ownership grows from control, knowledge, and invested self—which means the agent's owner must participate in designing the agent's boundaries, must have the tools to see through the agent's behavior, must have the time to cultivate it as his own work. That is expensive. But a hollow owner is more expensive; the invoice merely arrives later.

Forty years ago, Thompson told us the problem of many hands cannot be solved, only managed. The tech industry managed it for thirty years with DRIs and single-threaded owners. Now AI agents walk into the office carrying the most hands in history—and organizations will either redesign accountability, or discover that the answer to "who owns this?" is becoming "no one—and this time, truly no one."

---

*The situations described in this essay are composite depictions of cross-industry patterns; every scenario has counterparts in the empirical samples of the cited literature (spanning Windows, Chrome, Avaya, GitHub, and surveys of managers in global companies), and none refers to any specific organization or individual.*

---

## References

1. Thompson, D. F. (1980). *Moral Responsibility of Public Officials: The Problem of Many Hands.* American Political Science Review, 74(4), 905–916. https://doi.org/10.2307/1954312
   — Origin of the "problem of many hands": when an outcome is produced by many actors together, no individual can reasonably be held responsible.

2. Darley, J. M., & Latané, B. (1968). *Bystander Intervention in Emergencies: Diffusion of Responsibility.* Journal of Personality and Social Psychology, 8(4), 377–383.
   — Classic experiments on diffusion of responsibility: the more people present, the lower the probability any individual acts.

3. Bryar, C., & Carr, B. (2021). *Working Backwards: Insights, Stories, and Secrets from Inside Amazon.* St. Martin's Press.
   — Documents Amazon's single-threaded leadership: important initiatives require a single, non-moonlighting owner.

4. Bird, C., Nagappan, N., Murphy, B., Gall, H., & Devanbu, P. (2011). *Don't Touch My Code! Examining the Effects of Ownership on Software Quality.* ESEC/FSE '11, 4–14. https://doi.org/10.1145/2025113.2025119
   — Windows Vista/7 evidence: lower top-owner proportion and more low-expertise contributors correlate with more pre-release faults and post-release failures; also finds that low-expertise contributions stem largely from structural causes (dependencies, interfaces) and cannot simply be forbidden.

5. Mockus, A. (2010). *Organizational Volatility and Its Effects on Software Defects.* FSE '10, 117–126. https://doi.org/10.1145/1882291.1882311
   — Developer-centered measures of organizational change (departures, reorganizations) predict customer-reported defects.

6. Mockus, A. (2009). *Succession: Measuring Transfer of Code and Developer Productivity.* ICSE '09.
   — Proposes measuring code succession between developers, treating owner change as a trackable, assessable knowledge-transfer process rather than a mere personnel event.

7. Rigby, P. C., Zhu, Y. C., Donadelli, S. M., & Mockus, A. (2016). *Quantifying and Mitigating Turnover-Induced Knowledge Loss: Case Studies of Chrome and a Project at Avaya.* ICSE '16, 1006–1016. https://doi.org/10.1145/2884781.2884851
   — Applies financial risk-analysis methods to turnover-induced knowledge loss (measured via abandoned source files): projects are susceptible to losses more than three times the expected loss, over five times in historical simulations; reviews prior evidence that survivors and newcomers maintaining abandoned code lose productivity and err more.

8. O'Leary, M. B., Mortensen, M., & Woolley, A. W. (2011). *Multiple Team Membership: A Theoretical Model of Its Effects on Productivity and Learning for Individuals and Teams.* Academy of Management Review, 36(3), 461–478.
   — Foundational MTM theory: organizations pursue productivity and learning through multiple team membership, but the structure imposes competing pressures on attention and information; number and variety of memberships require careful balancing.

9. Mortensen, M., & Gardner, H. K. (2017). *The Overcommitted Organization.* Harvard Business Review, 95(5), 58–65.
   — Reports that multiple team membership is the norm for 81% of managers in global companies; examines how organizational overcommitment erodes team effectiveness.

10. Zika-Viktorsson, A., Sundström, P., & Engwall, M. (2006). *Project Overload: An Exploratory Study of Work and Management in Multi-Project Settings.* International Journal of Project Management, 24(5), 385–394.
   — Introduces "project overload": fragmentation and frequent switching in multi-project work correlate with psychological stress reactions and impaired competence development.

11. Vasilescu, B., Blincoe, K., Xuan, Q., Casalnuovo, C., Damian, D., Devanbu, P., & Filkov, V. (2016). *The Sky Is Not the Limit: Multitasking Across GitHub Projects.* ICSE '16, 994–1005. https://doi.org/10.1145/2884781.2884875
   — Large-scale longitudinal GitHub evidence: developer output depends on the balance among project count, focus, and project diversity; multitasking has measurable cognitive limits.

12. Tushman, M. L. (1977). *Special Boundary Roles in the Innovation Process.* Administrative Science Quarterly, 22(4), 587–605.
   — Foundational boundary-spanning study (345 subjects, 58 projects in R&D labs): identifies gatekeepers and liaisons; effective cross-boundary information flow is accomplished only by the few individuals well connected both internally and externally.

13. Kahn, R. L., Wolfe, D. M., Quinn, R. P., Snoek, J. D., & Rosenthal, R. A. (1964). *Organizational Stress: Studies in Role Conflict and Ambiguity.* Wiley.
   — Original role-conflict theory: the focal person bears incompatible expectations from multiple role senders; a principal finding is that objective conflict converts to subjective strain when the role set is powerful; follow-up research shows conflict rises with role-set diversity and organizational distance.

14. Stovel, K., & Shaw, L. (2012). *Brokerage.* Annual Review of Sociology, 38, 139–158.
   — Sociological review of brokerage: a fundamental duality—brokerage eases interaction, economic activity, and cooperation, while routinely attracting suspicion of self-dealing, accusations of exploitation, and the amplification of inequality.

15. Babcock, L., Recalde, M. P., Vesterlund, L., & Weingart, L. (2017). *Gender Differences in Accepting and Receiving Requests for Tasks with Low Promotability.* American Economic Review, 107(3), 714–747.
   — Introduces "non-promotable tasks": work critical to the organization but useless for the performer's advancement, systematically allocated toward those for whom refusal is most costly.

16. Davies, D. (2024). *The Unaccountability Machine: Why Big Systems Make Terrible Decisions—And How the World Lost Its Mind.* Profile Books.
   — Introduces the "accountability sink": organizations absorb decision responsibility into rulebooks, standard procedures, or computer systems, severing the feedback link between decision-makers and those affected, making errors unattributable and uncorrectable.

17. Hood, C. (2011). *The Blame Game: Spin, Bureaucracy, and Self-Preservation in Government.* Princeton University Press.
   — Systematic account of how organizations engineer structures to deflect and distribute blame (blame avoidance).

18. Pierce, J. L., Kostova, T., & Dirks, K. T. (2001). *Toward a Theory of Psychological Ownership in Organizations.* Academy of Management Review, 26(2), 298–310. https://doi.org/10.5465/amr.2001.4378028
   — Psychological ownership theory: distinguishes the designated owner from the genuine feeling of ownership, which grows from control, intimate knowledge, and investment of self—none producible by assignment.

19. Matthias, A. (2004). *The Responsibility Gap: Ascribing Responsibility for the Actions of Learning Automata.* Ethics and Information Technology, 6(3), 175–183. https://doi.org/10.1007/s10676-004-3422-1
   — Original "responsibility gap" paper: when learning autonomous systems act beyond predictable bounds, the traditional conditions for responsibility ascription (control and foreseeability) break down.

20. Santoni de Sio, F., & Mecacci, G. (2021). *Four Responsibility Gaps with Artificial Intelligence: Why They Matter and How to Address Them.* Philosophy & Technology, 34, 1057–1084. https://doi.org/10.1007/s13347-021-00450-x
   — Argues the AI responsibility gap comprises four interrelated gaps (culpability, moral accountability, public accountability, active responsibility) and that AI's introduction sharpens the problem of many hands.

21. Reif, J. A., Larrick, R. P., & Soll, J. B. (2025). *Evidence of a Social Evaluation Penalty for Using AI.* Proceedings of the National Academy of Sciences, 122(19), e2426766122. https://doi.org/10.1073/pnas.2426766122
   — Four preregistered experiments (N = 4,439): people who use AI at work anticipate and receive negative evaluations of competence and motivation (lazier, less capable, more replaceable), consistent across occupation, age, and gender; the harshest evaluators are those who do not use AI themselves; participants were consequently less willing to disclose AI use.

22. Bateson, G., Jackson, D. D., Haley, J., & Weakland, J. (1956). *Toward a Theory of Schizophrenia.* Behavioral Science, 1(4), 251–264.
   — Original "double bind" concept: an individual receives contradictory injunctions and can neither discuss the contradiction nor leave the situation. This essay borrows the structure to describe organizations' contradictory demands around AI adoption, without invoking its original clinical context.

23. Argyris, C. (1990). *Overcoming Organizational Defenses: Facilitating Organizational Learning.* Allyn & Bacon.
   — Classic on organizational defensive routines: organizations send mixed messages, deny the inconsistency, and render the denial undiscussable, blocking organizational learning.

24. March, J. G. (1991). *Exploration and Exploitation in Organizational Learning.* Organization Science, 2(1), 71–87. https://doi.org/10.1287/orsc.2.1.71
   — Foundational framework: organizations naturally favor exploitation (certain, near-term returns) at the expense of exploration (distant, uncertain returns), because exploration's payoffs lose systematically in every resource competition.

25. Nohria, N., & Gulati, R. (1996). *Is Slack Good or Bad for Innovation?* Academy of Management Journal, 39(5), 1245–1264.
   — Empirical inverted-U between slack (resources beyond the minimum necessary) and innovation: without slack, experimentation cannot be sustained because outcomes are high-variance; too much slack erodes discipline.

26. Mullainathan, S., & Shafir, E. (2013). *Scarcity: Why Having Too Little Means So Much.* Times Books.
   — Psychology of scarcity: scarcity tunnels attention and taxes cognitive bandwidth, causing systematic neglect of long-term investment outside the tunnel.

27. Adams, J. S. (1965). *Inequity in Social Exchange.* In L. Berkowitz (Ed.), Advances in Experimental Social Psychology (Vol. 2, pp. 267–299). Academic Press.
   — Original equity theory: people continuously compare input–output ratios with others; perceived inequity triggers strong corrective motivation.

28. Bellezza, S., Paharia, N., & Keinan, A. (2017). *Conspicuous Consumption of Time: When Busyness and Lack of Leisure Become a Status Symbol.* Journal of Consumer Research, 44(1), 118–138.
   — Evidence on busyness as a status symbol: busyness and lack of leisure are read as signals of competence and scarcity, so visible spare time carries a status cost.

29. Pashler, H. (1994). *Dual-Task Interference in Simple Tasks: Data and Theory.* Psychological Bulletin, 116(2), 220–244.
   — Classic review of dual-task interference: human central cognitive processing has a serial bottleneck; tasks requiring thought cannot truly run in parallel, only queue.

30. Rubinstein, J. S., Meyer, D. E., & Evans, J. E. (2001). *Executive Control of Cognitive Processes in Task Switching.* Journal of Experimental Psychology: Human Perception and Performance, 27(4), 763–797.
   — Experimental measurement of task-switching costs: every switch carries a measurable time cost, rising with task complexity and unfamiliarity.

31. Olsen, D. R., Jr., & Wood, S. B. (2004). *Fan-out: Measuring Human Control of Multiple Robots.* CHI '04, 231–238. ACM.
   — Proposes the fan-out model: the number of autonomous systems one person can operate depends on the ratio of neglect time to interaction time; later extensions incorporating wait times and switching costs lower the feasible fan-out.

32. Mark, G., Gudith, D., & Klocke, U. (2008). *The Cost of Interrupted Work: More Speed and Stress.* CHI '08, 107–110. ACM.
   — Classic interruption experiment: interrupted workers compensate with faster work, at the cost of significantly higher stress, frustration, and time pressure.

33. Reinertsen, D. G. (2009). *The Principles of Product Development Flow: Second Generation Lean Product Development.* Celeritas Publishing.
   — Systematically brings queueing theory into product-development management: as utilization approaches 100%, waiting time explodes nonlinearly; scheduling to full utilization guarantees delay.

---

## Verification Notes

> 1. Publication details (title, authors, year) verified online during drafting for items 1, 4, 7, 8, 10, 11, 12, 13, 14, 16, 19, 20, 21, 24, 25, 31. For item 16 (Davies), the UK edition is Profile Books (2024) and the US edition University of Chicago Press (2025); books carry no DOI. DOIs verified for item 4 (10.1145/2025113.2025119), item 7 (10.1145/2884781.2884851), item 11 (10.1145/2884781.2884875), item 21 (10.1073/pnas.2426766122), and item 24 (10.1287/orsc.2.1.71). For item 25, the volume/issue/pages (AMJ 39(5), 1245–1264) and the "without slack, experimentation cannot be sustained due to high-variance outcomes" mechanism were cross-checked via secondary sources. For item 31, the CHI 2004 pages (231–238), the fan-out/neglect-time/interaction-time definitions, the "later models incorporating wait times and switching costs" extensions (Goodrich et al.), and the "inconsistent fan-out prediction methods" finding (Crandall & Cummings 2007) were all verified. "Losses more than three times the expected loss, over five times in simulations" is from the Rigby et al. abstract. "Not merely irritating … identity destroying" is a rendering of Kahn et al., p. 6. For item 21, the "lazier / less capable / more replaceable," "harshest evaluations from non-users," and "less willing to disclose" claims were cross-checked against the paper's abstract and text and Duke Fuqua's official coverage.
> 2. For item 8 (O'Leary et al.), volume/issue/pages were verified, but two DOI variants circulate (10.5465/amr.2011.61031807 and 10.5465/amr.2009.0275), so no DOI is attached here; confirm the official DOI at the AMR site before formal submission. For item 9 (Mortensen & Gardner, HBR), the "81% of managers" figure is relayed via a secondary review (Rishani 2024); check the HBR original before citing formally.
> 3. For item 13 (Kahn et al.), the in-text claims that conflict rises with role-set diversity derive from Snoek's (1966) follow-up analysis of the same dataset, and that conflict rises with organizational distance from Miles (1977); the essay attributes them to "follow-up research" rather than to Kahn's book. Cite Snoek (1966) and Miles (1977) directly if named attribution is needed.
> 4. Item 15 (Babcock et al., AER) is well known but its volume/pages were not re-verified against the AER original during drafting. Reilly's "Being Glue" is a practitioner talk/essay (noidea.dog/glue), not academic literature; it is cited as a practitioner perspective and not listed among formal references; "done by a senior person it's leadership; done by a junior person it's 'not technical enough'" is a paraphrase of its argument. Items 22 (Bateson et al.) and 23 (Argyris) are textbook classics whose volume/pages were not re-verified; Bateson's double bind originates in clinical psychology, and this essay borrows only its "contradictory injunctions + undiscussable contradiction" structure, as noted in the reference annotation. A 2026 arXiv preprint reports behavioral-experiment evidence that participants will incur personal costs to punish peers who use LLMs (punishment rising with usage intensity), directionally consistent with item 21, but it is not cited here as it has not undergone peer review.
> 5. Bibliographic details for items 5 (Mockus 2010) and 6 (Mockus 2009) appear consistently across multiple papers' reference lists but were not checked against the ACM originals during drafting; verify before formal submission.
> 6. Items 2 (Darley & Latané), 3 (Bryar & Carr), 17 (Hood), and 18 (Pierce et al.) are textbook classics or well-known publications; volume/page details were not re-verified during drafting.
> 7. Weinberg's "each additional concurrent project costs roughly 20% of one's time to switching" is from *Quality Software Management, Vol. 1: Systems Thinking* (Dorset House, 1992); it is a practitioner heuristic, not rigorous evidence, is flagged as such in the text, and is not listed among formal references.
> 8. Apple's DRI practice is widely described in industry reporting and secondary accounts (e.g., Fortune's coverage of Apple's management system), but Apple has published no first-party documentation; the essay treats it as industry common knowledge without binding it to a specific source.
> 9. "The A column of a RACI can hold only one name" is standard project-management practice found in PMI and similar training materials; no specific paper is cited.
> 10. "Collective code ownership" is an Extreme Programming practice tradition (Beck et al.), mentioned as conceptual context without a specific citation; "collective ownership degrades easily into no ownership" is this essay's own argument, not a citation.
> 11. "Delegating decisions to algorithms is the most convenient way to build an accountability sink" is an extension of Davies's argument found in the book's critical reception (the book itself connects algorithmic decision-making to accountability sinks); it is presented as this essay's own reasoning, without quotation marks. "The allocation sheet manufactures an accounting illusion," "a middleman's output is inherently counterfactual," "the systematic depreciation of the organization's scarcest role," and similar formulations are this essay's own arguments, not citations.
