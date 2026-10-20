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

## How is a change released?

Every merge to `main` is a release. The chart releaser publishes each chart whose version changed, and the `dockerbuild-release-*` workflows build the release images for the components whose source changed. While a pull request is open, its images are built as prerelease versions. See [Work with Docker images](docs/developer/work-with-dockerimages.md).

Before you merge a pull request that changes the canvas:

1. Check that `trigger_test` passed. It runs only the BDD features the pull request affects. The **BDD test selection** comment on the pull request lists them, and explains any full run.
2. If the pull request releases a new version of the `canvas-oda` chart, run the full BDD suite against its branch, while it still uses the prerelease images. Go to **Actions > trigger_test > Run workflow** and pick the branch. This also runs the Kong and APISIX features, each on its own cluster.
3. Remove the prerelease suffixes in a last commit whose message starts with `[skip tests]`. `trigger_test` skips the BDD tests for that commit, because the release images don't exist yet.

After you merge, check in **Actions** that the `dockerbuild-release-*` workflows finished. The released charts can't pull the new image versions until then.

See [Executing the tests](feature-definition-and-test-kit/Executing-tests.md) for how the BDD features are selected and run.

## Do you need a new feature?

Raise an issue describing the feature you need and how you might implement it before starting to code. Any feature that is applied to the codebase will eventually become part of the TM Forum Open Digital Architecture standard, so new features may need ratifying before implementation. We can have that discussion with you as part of the issue and nail the feature down in a way that will be acceptable to members before development work starts.

## Anything else?

Please contact us directly at [components@tmforum.org](mailto:components@tmforum.org).