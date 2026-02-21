// Web Worker for precise timing that works even when tab is not focused
let timers = {};
let timerIdCounter = 0;

self.onmessage = function (e) {
    const { action, id, delay } = e.data;

    if (action === 'setTimeout') {
        const timerId = timerIdCounter++;
        timers[timerId] = setTimeout(() => {
            // Post back the original caller's requestId (id), not the internal timerId
            self.postMessage({ type: 'timeout', id: id });
            delete timers[timerId];
        }, delay);
        // Also send the internal timerId so the caller can cancel it
        self.postMessage({ type: 'timerId', requestId: id, timerId: timerId });
    } else if (action === 'clearTimeout') {
        if (timers[id]) {
            clearTimeout(timers[id]);
            delete timers[id];
        }
    }
};
