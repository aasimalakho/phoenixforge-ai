# Submission Checklist — Build with DataHub: The Agent Hackathon

Use this before you hit submit on Devpost. Check off each item; don't submit until
every box is true.

## Eligibility (Stage One, pass/fail)

- [ ] Project reasonably fits the theme (data/ML agent problem). ✅ Incident response
      for data pipelines — fits "Agents That Do Real Work" and "Metadata-Aware Code
      Generation & Development."
- [ ] Project uses DataHub together with **at least one of**: MCP Server, Agent Context
      Kit, DataHub Skills, Analytics Agent.
      → This is the item the original build was missing. It now uses the **MCP Server**
      for real. Before submitting: run in `INTEGRATION_MODE=mcp`, `DEMO_MODE=false`
      against a real DataHub instance at least once, and confirm in the terminal that
      the MCP subprocess connects (no fallback warning printed). Screenshot or clip that
      for your own records in case a judge asks.
- [ ] Built during the Registration & Submission Period (July 6 – Aug 10, 2026). Any
      pre-existing code you reused (framework boilerplate, starter templates) is
      disclosed in the README.

## Repository requirements

- [ ] Repo is **public**.
- [ ] `LICENSE` file (Apache 2.0) is at the top level — already included — and GitHub
      shows "Apache-2.0" in the repo's **About** section (GitHub auto-detects this from
      the LICENSE file; double-check it actually appears after you push).
- [ ] Repo contains all source code, assets, and instructions needed to run it
      (`SETUP_GUIDE.md` covers this end-to-end for Codespaces).
- [ ] `examples/` folder has sample generated outputs (already included: sample repair
      SQL, sample PR description, sample runbook) so judges can evaluate output quality
      without running the project.

## Submission form

- [ ] Project URL: a live/testable link (hosted dashboard, or repo with clear setup
      instructions — Codespaces one-click works for this).
- [ ] Public repo URL.
- [ ] Text description covering features, functionality, technologies, and data used
      (draw from the README — don't just paste it verbatim, Devpost wants a summary).
- [ ] Demo video: **under 3 minutes**, uploaded to YouTube or Vimeo, **public
      visibility**. Must show the project actually running — not just slides. Suggested
      cut: (1) 10s problem statement, (2) trigger the demo incident, (3) walk the agent
      trace timeline showing MCP tool calls happening, (4) show the generated PR, (5)
      show the knowledge-base entry written back to DataHub. No third-party trademarks
      or copyrighted music unless you have permission.
- [ ] (Optional but recommended) Opt into the Most Valuable Feedback Survey during
      submission — separate $50 x 10 prize pool, low effort, doesn't compete with your
      main entry.

## Judging criteria — self-check before submitting

- [ ] **Use of DataHub:** demonstrate MCP read tools AND at least one write-back tool
      (`save_document` via the Knowledge Agent) in the video — write-back is explicitly
      called out as what separates strong submissions.
- [ ] **Technical Execution:** run the full pipeline end-to-end at least 3 times without
      manual intervention before recording the video.
- [ ] **Originality:** the README's "Why this exists" section should make clear this
      goes beyond DataHub's out-of-the-box features (autonomous repair + write-back
      memory, not just a metadata viewer).
- [ ] **Real-World Usefulness:** the text description should name a concrete team
      persona (data platform / analytics engineering) and the problem this saves them.
- [ ] **Submission Quality:** proofread the README and video script; a judge with zero
      context should understand what happened in the first 30 seconds of the video.
- [ ] **Bonus — open-source contribution:** `contrib/incident-repair-skill-PROPOSAL.md`
      is a draft, not a merged PR. If you have time before the deadline, actually open it
      as a PR/RFC against a DataHub Skills repo — a real (even unmerged) PR link is worth
      more than a proposal file sitting in your own repo. If you don't have time, keep it
      as-is but don't describe it as "contributed" in your text description — say
      "proposed."

## Honesty check (no loopholes)

- [ ] Nothing in the README, video, or description claims a capability the code doesn't
      actually have. In particular: don't say "contributes to DataHub open source" unless
      a PR actually exists; say "MCP-integrated" only once you've verified a live MCP
      connection, not just the fallback-to-demo path.
- [ ] `DEMO_MODE=true` is clearly labeled as a demo/fallback in the video narration, not
      presented as the real integration.
