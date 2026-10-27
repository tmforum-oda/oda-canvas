// Prints the state of the components namespace when a scenario fails, so a
// failure in CI can be diagnosed from the test log: by the end of the run the
// cluster is gone, and later scenarios may already have uninstalled the
// components involved.
//
// Set BDD_DIAGNOSTICS=false to turn it off, for example when running the tests
// against a shared cluster.

const { After, Status } = require('@cucumber/cucumber');
const { execSync } = require('child_process');

const NAMESPACE = 'components';
const MAX_PODS_DESCRIBED = 10;
const COMMAND_TIMEOUT = 30 * 1000;

function kubectl (args) {
  try {
    return execSync('kubectl ' + args, { encoding: 'utf-8', timeout: COMMAND_TIMEOUT, stdio: ['ignore', 'pipe', 'pipe'] });
  } catch (error) {
    return `(kubectl ${args} failed: ${(error.stderr || error.message || '').toString().trim()})\n`;
  }
}

function lastLines (text, count) {
  return text.trimEnd().split('\n').slice(-count).join('\n') + '\n';
}

// Pods that are neither ready nor finished, with the reason given by their
// containers, for example CrashLoopBackOff or ImagePullBackOff
function podsNotReady () {
  let pods;
  try {
    pods = JSON.parse(execSync(`kubectl get pods -n ${NAMESPACE} -o json`, { encoding: 'utf-8', timeout: COMMAND_TIMEOUT, stdio: ['ignore', 'pipe', 'pipe'] })).items;
  } catch (error) {
    return [];
  }
  return pods.filter(pod => {
    if (pod.status.phase === 'Succeeded') return false;
    const ready = (pod.status.conditions || []).find(condition => condition.type === 'Ready');
    return !ready || ready.status !== 'True';
  }).map(pod => ({
    name: pod.metadata.name,
    restarted: (pod.status.containerStatuses || []).some(container => container.restartCount > 0)
  }));
}

After({ name: 'Print cluster diagnostics when a scenario fails', timeout: 5 * 60 * 1000 }, function (scenario) {
  if (scenario.result.status !== Status.FAILED || process.env.BDD_DIAGNOSTICS === 'false') return;

  const output = [`\n=== Cluster diagnostics for failed scenario: ${scenario.pickle.name} ===\n`];
  output.push(`--- Pods in ${NAMESPACE} ---\n`, kubectl(`get pods -n ${NAMESPACE} -o wide`));
  output.push(`--- Persistent volume claims in ${NAMESPACE} ---\n`, kubectl(`get pvc -n ${NAMESPACE}`));
  output.push(`--- Last 40 events in ${NAMESPACE} ---\n`, lastLines(kubectl(`get events -n ${NAMESPACE} --sort-by=.lastTimestamp`), 40));

  const notReady = podsNotReady();
  for (const pod of notReady.slice(0, MAX_PODS_DESCRIBED)) {
    output.push(`--- Pod ${pod.name} is not ready: description (last 40 lines) ---\n`, lastLines(kubectl(`describe pod ${pod.name} -n ${NAMESPACE}`), 40));
    output.push(`--- Pod ${pod.name}: logs (last 30 lines) ---\n`, lastLines(kubectl(`logs ${pod.name} -n ${NAMESPACE} --all-containers --tail=30`), 30));
    if (pod.restarted) {
      output.push(`--- Pod ${pod.name}: logs before its last restart (last 30 lines) ---\n`, lastLines(kubectl(`logs ${pod.name} -n ${NAMESPACE} --all-containers --previous --tail=30`), 30));
    }
  }
  if (notReady.length > MAX_PODS_DESCRIBED) output.push(`(${notReady.length - MAX_PODS_DESCRIBED} more pods are not ready)\n`);

  output.push(`=== End of cluster diagnostics ===\n`);
  console.log(output.join(''));
});
