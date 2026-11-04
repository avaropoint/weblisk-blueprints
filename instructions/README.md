# Instructions

Every sentence a build gives a model, written once and passed as written. Each
file is one instruction of the family [`schemas/instruction`](../schemas/instruction.md):
its `in` names the build steps whose prompt carries it, and its Text is what
the model is given. The steps, and what a model may and may not do in each,
are [`architecture/engine`](../architecture/engine.md#the-build-steps)'s; the
rules for what a generator conveys, and why, are
[`architecture/generation`](../architecture/generation.md#the-prompt-contract)'s.

An instruction is not a skill. A tenant's agents are given a programme's
`skills:` at run time; a coding agent reads [`skills/`](../skills/README.md);
an instruction is what the engine gives a model inside one build step, and the
engine gives a model nothing else of its own.

| Instruction | In | What it makes the model do |
|---|---|---|
| [`plan`](plan.md) | plan | write a plan inside the fixed packages, with top-level symbols in `declares` |
| [`translate`](translate.md) | translate | write one test from one criterion and the contract alone, or report the criterion untestable |
| [`generate`](generate.md) | generate | answer with exactly one file, and read the tests without writing them |
| [`repair`](repair.md) | repair | edit the given files as they stand, and nothing else |
| [`advise`](advise.md) | accept | read the tree as advice, never as a verdict |
| [`reading`](reading.md) | plan, translate, generate, repair | read a blueprint by its forms: what binds, and what only illustrates |
| [`plan-names`](plan-names.md) | plan | spell every declared name as its blueprint does, and list a missing one as a gap |
| [`file-names`](file-names.md) | generate, repair | spell every declared name as the plan does, and report a missing one |
| [`scope`](scope.md) | generate, repair | write only what the plan entry declares and serves |
| [`ties`](ties.md) | plan, translate, generate, repair | follow the more specific of two statements, or report the conflict |
| [`corpus-finding`](corpus-finding.md) | plan, translate, generate, repair | the one form a corpus finding takes: a conflict, a gap, or an untestable criterion |
