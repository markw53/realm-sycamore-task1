"""Serialization utilities for jobs and results."""
import json
from src.models.job import Job
from src.models.result import JobResult


def serialize_job(job: Job) -> str:
    return json.dumps(job.to_dict(), default=str)


def deserialize_job(data: str) -> Job:
    return Job.from_dict(json.loads(data))


def serialize_result(result: JobResult) -> str:
    return json.dumps(result.to_dict(), default=str)


def deserialize_result(data: str) -> JobResult:
    return JobResult.from_dict(json.loads(data))


def serialize_many_jobs(jobs: list[Job]) -> str:
    return json.dumps([j.to_dict() for j in jobs], default=str)


def deserialize_many_jobs(data: str) -> list[Job]:
    return [Job.from_dict(d) for d in json.loads(data)]