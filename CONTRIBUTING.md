# Contributing to ReTrace AI

Thanks for your interest in improving ReTrace AI.

## Ways to contribute

- Report bugs and missing behaviors
- Improve the GitHub evidence collection heuristics
- Improve the decision replay output format
- Improve the UI and developer experience
- Add tests and reliability checks
- Suggest better open-weight model integration patterns

## Local setup

1. Clone the repository.
2. Create a virtual environment for the backend.
3. Install backend dependencies.
4. Install frontend dependencies.
5. Run the backend and frontend locally.
6. Test a repository URL and question through the UI or API.

## Code guidelines

- Keep changes small and targeted.
- Do not add authentication flows or paid infrastructure to the MVP.
- Respect public-only repository support.
- Keep API responses structured and explain uncertainty explicitly.
- Never commit secrets, GitHub tokens, API keys, or environment files.
- Do not add fake claims or invented historical reasoning.

## Pull request expectations

- Describe the problem and the change clearly.
- Include validation steps.
- Note any limitations or follow-up work.
- Keep public-facing documentation aligned with the implementation.

## Security reminder

- Never commit `.env` files.
- Never commit GitHub tokens, API keys, or other secrets.
- Do not place credentials in frontend code or source-controlled files.

## Questions

Open an issue before making a large change, especially for architecture or model-selection work.
