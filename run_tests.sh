#!/bin/bash
set -e

cd /target
npm install
npx jest --forceExit --detectOpenHandles --verbose 2>&1

