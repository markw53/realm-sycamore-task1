# Environment Interface

## Observation space

- Source Python repository files under `/source`
- `prompt.txt`
- Shell output from build, test, grep, and file inspection commands

## Action space

- Read files
- Search code
- Create and edit files under `/target`
- Run shell commands (npm install, npx tsc, npx jest, etc.)
- Install Node.js/TypeScript dependencies

## Episode start

- Container starts with the source Python repository at `/source`
- An empty `/target` directory is provided for the translation
- The target test suite is pre-installed and will be copied into the translation for verification
- The agent receives only `prompt.txt`

## Deterministic verifier

- Copy target test files into the agent's translated repository
- Run `cd /target && npm install && npx tsc` to verify compilation
- Run `cd /target && npx jest --forceExit --detectOpenHandles --verbose` to verify functional equivalence
- Count passing and failing tests

## Success condition

- `npx tsc` succeeds with no errors
- All target tests pass: `84 passed, 0 failed`
- No test files were modified by the agent