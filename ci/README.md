# CI workflows

GitHub blocked pushing workflow files from this environment (the connected
GitHub App lacks the `workflows` permission). To enable CI, move these files
yourself:

```bash
mkdir -p .github/workflows
git mv ci/backend.yml ci/frontend.yml .github/workflows/
git commit -m "Enable GitHub Actions CI"
git push
```

- `backend.yml` — runs the pytest suite on every backend change
- `frontend.yml` — builds the Next.js app on every frontend change
