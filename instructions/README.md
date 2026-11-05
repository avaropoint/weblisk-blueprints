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
| [`plan-shape`](plan-shape.md) | plan | answer with one JSON object whose keys, commands and file entries follow the rules a plan is refused for breaking |
| [`requirements`](requirements.md) | plan | read the requirements input, and place every requirement in it, spelled from its declared name |
| [`package-plan`](package-plan.md) | plan | read the package plan input: the component's own directories, its entry point, and the directories that are another's |
| [`tenant-state`](tenant-state.md) | plan, generate | read the tenant state input as fact: import what the tenant provides, keep names whose requirement has not changed, plan nothing another component owns |
| [`translate`](translate.md) | translate | write one test from one criterion and the contract alone, or report the criterion untestable |
| [`generate`](generate.md) | generate | answer with exactly one file, and read the tests without writing them |
| [`plan-entry`](plan-entry.md) | generate | read the plan entry and the file set, and write the one file the entry names |
| [`declarations`](declarations.md) | generate, repair | read the declarations input: the module path, what other files declare and use, and keep to it |
| [`repair`](repair.md) | repair | edit the given files as they stand, and nothing else |
| [`repair-set`](repair-set.md) | repair | read the repair set: the files that may change, what each owes, and their content as it stands |
| [`failure`](failure.md) | repair | read the failure by its kind, and change what that kind says and nothing else |
| [`edit-form`](edit-form.md) | repair | answer in the one edit form, with a path line before each file where several may change |
| [`advise`](advise.md) | accept | read the tree as advice, never as a verdict |
| [`reading`](reading.md) | plan, translate, generate, repair | read a blueprint by its forms: what binds, and what only illustrates |
| [`plan-names`](plan-names.md) | plan | spell every declared name as its blueprint does, and list a missing one as a gap |
| [`file-names`](file-names.md) | generate, repair | spell every declared name as the plan does, and report a missing one |
| [`scope`](scope.md) | generate, repair | write only what the plan entry declares and serves |
| [`ties`](ties.md) | plan, translate, generate, repair | follow the more specific of two statements, or report the conflict |
| [`corpus-finding`](corpus-finding.md) | plan, translate, generate, repair | the one form a corpus finding takes: a conflict, a gap, or an untestable criterion |
| [`rejection`](rejection.md) | plan, generate, repair | answer again, when an earlier answer to the same request was refused, so that none of its reasons holds |
