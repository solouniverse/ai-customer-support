import time
from dataclasses import dataclass

from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Evaluator, EvaluatorContext

from app.ai.decide import decide
from app.ai.schemas import Decision
from evals.golden_emails import GOLDEN_EMAILS


@dataclass
class SectionMatches(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return ctx.output.section == ctx.expected_output["section"]


@dataclass
class ActionMatches(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return ctx.output.action == ctx.expected_output["action"]


def run_pipeline(email: str) -> Decision:
    for attempt in range(3):
        try:
            return decide(email)
        except Exception as error:
            status_code = getattr(error, "status_code", None)
            transient = (
                isinstance(error, (ConnectionError, TimeoutError))
                or status_code in {429, 502, 503, 504}
                or error.__class__.__name__ in {
                    "APIConnectionError",
                    "APITimeoutError",
                    "InternalServerError",
                    "OverloadedError",
                    "RateLimitError",
                    "ServiceUnavailableError",
                }
            )
            if not transient or attempt == 2:
                raise
            time.sleep(2 ** attempt)


dataset = Dataset(
    name="golden-emails",
    cases=[
        Case(
            name=case["name"],
            inputs=case["email"],
            expected_output={"section": case["section"], "action": case["action"]},
        )
        for case in GOLDEN_EMAILS
    ],
    evaluators=[SectionMatches(), ActionMatches()],
)

if __name__ == "__main__":
    report = dataset.evaluate_sync(run_pipeline, max_concurrency=1)
    report.print(include_input=False, include_output=True, include_durations=False)
