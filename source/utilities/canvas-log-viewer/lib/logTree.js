// Pure functions for parsing ODA Canvas operator log lines and building the
// log tree displayed by the Canvas Log Viewer. Kept free of any Kubernetes
// dependencies so they can be unit tested in isolation.

import colors from 'colors';

export const UNKNOWN = 'Unknown';

// Matches the contents of every [...] group in a log line, e.g.
// [2024-11-17 13:05:34,612] SManOP [INFO    ] [comp|res|handler|function] message
const BRACKET_CONTENTS_RX = /(?<=\[)[^\][]*(?=])/g;

/**
 * Parse a single operator log line.
 *
 * Expected format:
 *   [<TIME>] <LOGGER> [<LEVEL>] [<COMPONENT>|<RESOURCE>|<HANDLER>|<FUNCTION>] <MESSAGE>
 * or, for kopf framework messages:
 *   [<TIME>] kopf.objects [<LEVEL>] [<RESOURCE>] <MESSAGE>
 *
 * @param {string} line a single log line
 * @returns {object|null} the parsed entry, or null if the line has no [...] groups
 */
export function parseLogLine(line) {
    const matches = line.match(BRACKET_CONTENTS_RX);
    if (!matches) {
        return null;
    }

    const entry = {
        dateStamp: matches[0],
        type: UNKNOWN,
        controller: UNKNOWN,
        componentName: UNKNOWN,
        resourceName: UNKNOWN,
        handlerName: UNKNOWN,
        functionName: UNKNOWN,
        message: line,
    };

    if (matches.length < 2) {
        // no log level present - treat the whole line as an error message
        entry.type = 'ERROR';
        return entry;
    }

    entry.type = matches[1].trim();
    const messageList = line.split(']');
    entry.message = messageList[messageList.length - 1].trim();
    entry.controller = messageList[1].split('[')[0].trim();

    if (matches.length === 3) {
        const labelsList = matches[2].split('|');
        if (entry.controller === 'kopf.objects') {
            entry.resourceName = labelsList[labelsList.length - 1];
        } else {
            entry.componentName = labelsList[0] ?? UNKNOWN;
            entry.resourceName = labelsList[1] ?? UNKNOWN;
            entry.handlerName = labelsList[2] ?? UNKNOWN;
            entry.functionName = labelsList[3] ?? UNKNOWN;
        }
    }
    return entry;
}

/**
 * Format a parsed entry for display, colouring the message by log level.
 *
 * @param {object} entry a parsed log entry from parseLogLine
 * @returns {string} the formatted message
 */
export function formatMessage(entry) {
    let message = entry.message;
    if (entry.type === 'INFO') {
        message = colors.green(message);
    } else if (entry.type === 'ERROR') {
        message = colors.red(message);
    } else if (entry.type === 'WARNING') {
        message = colors.yellow(message);
    }
    return colors.gray(entry.dateStamp) + ' ' + entry.functionName + ': ' + message;
}

/**
 * Add a parsed entry to the log tree, grouped by resource, controller and handler.
 *
 * @param {object} tree the log tree object (mutated in place)
 * @param {object} entry a parsed log entry from parseLogLine
 * @returns {object} the updated tree
 */
export function addToTree(tree, entry) {
    const { resourceName, controller, handlerName } = entry;
    tree[resourceName] ??= {};
    tree[resourceName][controller] ??= {};
    tree[resourceName][controller][handlerName] ??= [];
    tree[resourceName][controller][handlerName].push(formatMessage(entry));
    return tree;
}

/**
 * Returns a function that accepts stream chunks and calls `callback` once for
 * every complete newline-terminated line. Partial lines are buffered until the
 * rest of the line arrives.
 *
 * @param {function(string)} callback called with each complete line
 * @returns {function(string|Buffer)} the chunk handler
 */
export function newLineStream(callback) {
    let buffer = '';
    return function (chunk) {
        buffer += chunk;
        let offset = 0;
        let i;
        while ((i = buffer.indexOf('\n', offset)) !== -1) {
            callback(buffer.substring(offset, i));
            offset = i + 1;
        }
        buffer = buffer.substring(offset);
    };
}
