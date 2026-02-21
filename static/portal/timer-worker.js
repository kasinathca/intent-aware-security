// Web Worker for precise timing that works even when tab is not focused
let timers = {};
let timerIdCounter = 0;

self.onmessage = function (e) {
    const { action, id, delay } = e.data;

    if (action === 'setTimeout') {
        const timerId = timerIdCounter++;
        timers[timerId] = setTimeout(() => {
            self.postMessage({ type: 'timeout', id: timerId });
            delete timers[timerId];
        }, delay);
        self.postMessage({ type: 'timerId', requestId: id, timerId: timerId });
    } else if (action === 'clearTimeout') {
        if (timers[id]) {
            clearTimeout(timers[id]);
            delete timers[id];
        }
    }
};
