# How to contribute to the ODA Canvas Accelerator

## Have you read our code of conduct?

We want the ODA Canvas Accelerator to be a welcoming community project. We have a [code of conduct](code-of-conduct.md) that we expect all participants to follow in all interactions with, or about, the project. We will take corrective action where the code of conduct is not followed.

## Can you contribute under the terms of the license?

The project is released under the Apache 2 license. Please ensure that you have all necessary permissions to contribute code under those terms.

## Is something not working as expected?

- If it's a security vulnerability, please contact us directly at [components@tmforum.org](mailto:components@tmforum.org)rather than creating an issue. We will work together to figure out when and how that vulnerability will be disclosed.
- Check the issues to see if what you're experiencing has already been reported.
- If needed, open a new issue, and give us as much information as you can about what you did, what you were expecting and what actually happened. Even better, if you know what the root of the problem is, tell us that too.

## Can you fix a bug?

- Fork the repo, make your changes and then open a pull request against our repo with the fix.
- Make sure the PR clearly describes the problem and the solution. If you have already raised an issue, please include that reference as well.

## How is the Canvas released?

The ODA Canvas has **general releases** and **pre-releases** of the `canvas-oda` chart. The current general release is `canvas-oda-1.2.5`.

- **Pre-release.** Most pull requests create a new pre-release when they're merged. A pre-release uses the next version, plus a suffix of the proposer's initials and an index. For example, `canvas-oda-1.2.6-rc6` is the sixth pre-release of `1.2.6`, proposed by `rc`. Choose the next version by how much the canvas changes since the last general release: `1.2.6` for a patch, `1.3.0` for new features, or `2.0.0` for breaking changes.
- **General release.** Periodically, aiming for once a month, the maintainers run a full regression test of the latest pre-release, update the BDD badges, and release that version without a suffix, for example `canvas-oda-1.2.6`.

Each merge to `main` publishes the charts whose versions changed, through the chart releaser. It also builds release images for the components whose source changed, through the `dockerbuild-release-*` workflows. Pre-releases and general releases are published the same way. Only the version tells them apart.

### Proposing a pre-release in your pull request

1. **Work on a feature branch.** Name it `feature/...` or `odaa-...`, so that the prerelease Docker images build automatically. See [Work with Docker images](docs/developer/work-with-dockerimages.md).
2. **Version the images you change.** For each component whose source you change, increment its image version in `charts/canvas-oda/values.yaml` and set its `prereleaseSuffix`, for example to the issue number. Every push then builds a prerelease image, such as `1.1.1-issue625`.
3. **Version the charts.** Increment the version of each chart you change. Set the `canvas-oda` chart version in `charts/canvas-oda/Chart.yaml` to the next pre-release, for example `1.2.6-rc7`, and add a line to the version history comments below it:

   ```yaml
   version: 1.2.6-rc7
   # version: 1.2.6-rc7 - issue 625 - one line describing the change
   ```

4. **Check the BDD tests.** `trigger_test` runs only the BDD features your pull request affects. The **BDD test selection** comment on the pull request lists them, and explains any full run or skip. The tests must pass.
5. **Remove the image `prereleaseSuffix` values before merging.** Do it in a last commit whose message starts with `[skip tests]`. That turns the prerelease-suffix check green, and `trigger_test` skips the BDD tests for that commit, because the release images don't exist until the merge. Keep the pre-release suffix on the `canvas-oda` chart version.

After the merge, check in **Actions** that the `dockerbuild-release-*` workflows finished. The new pre-release can't pull its image versions until they have.

### Making a general release

Maintainers make a general release from `main`, aiming for once a month:

1. **Run the full regression test.** Go to **Actions > trigger_test > Run workflow** on `main`. This runs every BDD feature, including the Kong and APISIX features, each on its own cluster, and updates the BDD badges. The run must pass, or any failures must be understood and recorded as issues.
2. **Release the version.** In a pull request, set the `canvas-oda` chart version to the version without its suffix, for example `1.2.6`, and add a `# version: 1.2.6 - ...` history line that summarises the release. This needs no new images, so the PR runs only the smoke test. When it's merged, the chart releaser publishes `canvas-oda-1.2.6`.

See [Executing the tests](feature-definition-and-test-kit/Executing-tests.md) for how the BDD features are selected and run.

## Do you need a new feature?

Raise an issue describing the feature you need and how you might implement it before starting to code. Any feature that is applied to the codebase will eventually become part of the TM Forum Open Digital Architecture standard, so new features may need ratifying before implementation. We can have that discussion with you as part of the issue and nail the feature down in a way that will be acceptable to members before development work starts.

## Anything else?

Please contact us directly at [components@tmforum.org](mailto:components@tmforum.org).