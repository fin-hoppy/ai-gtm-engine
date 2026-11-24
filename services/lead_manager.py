
from datetime import datetime, timezone


STAGES = [
    "Matched",
    "Contacted",
    "Replied",
    "Meeting Booked",
    "Closed",
    "Lost",
]


TRANSITIONS = {
    "Matched": ["Contacted", "Lost"],
    "Contacted": ["Replied", "Lost"],
    "Replied": ["Meeting Booked", "Lost"],
    "Meeting Booked": ["Closed", "Lost"],
    "Closed": [],
    "Lost": [],
}


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def sync_pipeline(
    pipeline: dict,
    prospects: list,
    outreach_records: dict,
    scope: str,
) -> dict:

    for index, prospect in enumerate(prospects):

        lead_id = f"{scope}_{index}"

        if lead_id not in pipeline:

            pipeline[lead_id] = {
                "id": lead_id,
                "company": prospect.company_name,
                "website": str(prospect.website),
                "industry": prospect.industry,
                "fit_score": prospect.fit_score,
                "buyer": prospect.buyer_name,
                "stage": "Matched",
                "outreach_status": "Not Generated",
                "reached_stages": ["Matched"],
                "created_at": timestamp(),
                "updated_at": timestamp(),
                "history": [
                    {
                        "timestamp": timestamp(),
                        "actor": "System",
                        "action": "Imported research candidate",
                        "from": None,
                        "to": "Matched",
                        "simulated": False,
                    }
                ],
            }

        outreach = outreach_records.get(
            lead_id, {}
        )

        pipeline[lead_id]["outreach_status"] = (
            outreach.get(
                "status",
                "Not Generated",
            )
        )

    return pipeline


def update_stage(
    lead: dict,
    new_stage: str,
) -> None:

    old_stage = lead["stage"]

    allowed = TRANSITIONS[old_stage]

    if new_stage not in allowed:
        raise ValueError(
            "Invalid stage transition."
        )

    if (
        new_stage == "Contacted"
        and lead["outreach_status"] != "Approved"
    ):
        raise ValueError(
            "Outreach must be approved first."
        )

    lead["stage"] = new_stage
    lead["updated_at"] = timestamp()

    if new_stage not in lead["reached_stages"]:
        lead["reached_stages"].append(new_stage)

    lead["history"].append({
        "timestamp": timestamp(),
        "actor": "Human",
        "action": "Simulated stage transition",
        "from": old_stage,
        "to": new_stage,
        "simulated": True,
    })


def calculate_metrics(
    pipeline: dict,
) -> dict:

    leads = list(pipeline.values())

    total = len(leads)

    reached = {
        stage: sum(
            stage in lead["reached_stages"]
            for lead in leads
        )
        for stage in STAGES
    }

    def conversion(
        numerator: str,
        denominator: str,
    ) -> float | None:

        count = reached[denominator]

        if count == 0:
            return None

        return round(
            reached[numerator] / count * 100,
            1,
        )

    return {
        "total": total,
        "approved": sum(
            lead["outreach_status"] == "Approved"
            for lead in leads
        ),
        "reached": reached,
        "reply_rate": conversion(
            "Replied",
            "Contacted",
        ),
        "meeting_rate": conversion(
            "Meeting Booked",
            "Replied",
        ),
        "close_rate": conversion(
            "Closed",
            "Meeting Booked",
        ),
    }
