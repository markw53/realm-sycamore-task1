# Issue Introduced: Using `Array.sort()` Instead of a Min‑Heap for the Task Queue

During the translation from Python to TypeScript, the original `heapq`‑based priority queue was replaced with a simple array that gets re‑sorted on every insertion. This is an easy mistake to make because Python provides a built‑in binary heap (`heapq`), while JavaScript does not — so using `Array.sort()` feels like a quick and reasonable substitute.

## Why This Causes Problems

### 1. Performance Degradation
A binary heap provides:

- **O(log n)** insertion
- **O(log n)** removal
- **O(1)** peek

Sorting the entire array on every insertion turns the operation into:

- **O(n log n)**

This becomes a significant bottleneck as the queue grows, especially under heavy load.

### 2. Loss of FIFO Stability for Equal Priorities
The Python implementation uses a monotonically increasing insertion counter to guarantee:

- jobs with the same priority
- are returned in the order they were added

`Array.sort()` does **not** guarantee stable ordering unless a tie‑breaker is explicitly implemented. Without that counter, equal‑priority jobs may come out in the wrong order, breaking the expected behavior.

### 3. Behavioral Test Failures
The hidden test suite checks for:

- stable ordering
- correct priority semantics
- correct pop/peek behavior
- correct handling of stale entries

A sorted array implementation fails these tests in subtle but consistent ways.

## How to Fix It

The correct solution is to implement a small binary **min‑heap** in TypeScript that:

- orders jobs by priority
- uses an insertion counter as a secondary key
- supports `push`, `pop`, `peek`, and `remove`
- integrates with the `jobIndex` map for O(1) lookup

This restores the exact semantics of the Python `heapq` implementation and ensures the task queue behaves correctly under all test conditions.
